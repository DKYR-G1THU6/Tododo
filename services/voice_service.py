"""
语音任务服务（PC 端）

按住说话 -> 录音落地到本地 -> 上传 Storage -> 触发服务端转写。
与手机端逻辑对齐：录音先本地落地，任务卡片立刻出现；上传和转写在后台线程做，
失败只标记 transcribe_status='failed'，不会把录音弄丢。
"""
import logging
import uuid as uuid_lib
from pathlib import Path
from typing import Optional

from PyQt5.QtCore import QThread, pyqtSignal

import config
from services.supabase_client import SupabaseClient, SupabaseError

logger = logging.getLogger(__name__)

SAMPLE_RATE = 16000   # Whisper 内部就是 16k，再高只是浪费带宽
CHANNELS = 1

# 录音文件存放目录
RECORDINGS_DIR = config.APP_DATA_DIR / "recordings"


class VoiceRecorder:
    """麦克风录音（同步接口，由 UI 的按下/松开驱动）"""

    def __init__(self):
        self._stream = None
        self._frames: list = []
        self._sd = None
        self._sf = None

    def _lazy_import(self):
        """延迟导入：没装录音库时，app 其余功能仍然完全可用"""
        if self._sd is None:
            import sounddevice as sd
            import soundfile as sf
            self._sd = sd
            self._sf = sf

    @property
    def is_recording(self) -> bool:
        return self._stream is not None

    def start(self):
        """开始录音"""
        self._lazy_import()
        self._frames = []

        def callback(indata, frames, time_info, status):
            if status:
                logger.debug(f"Audio input status: {status}")
            self._frames.append(indata.copy())

        self._stream = self._sd.InputStream(
            samplerate=SAMPLE_RATE, channels=CHANNELS, dtype="int16", callback=callback
        )
        self._stream.start()
        logger.info("Recording started")

    def stop(self) -> Optional[Path]:
        """停止录音并写成 WAV，返回文件路径；没录到内容时返回 None"""
        if self._stream is None:
            return None

        self._stream.stop()
        self._stream.close()
        self._stream = None

        if not self._frames:
            logger.info("Recording produced no audio")
            return None

        import numpy as np
        audio = np.concatenate(self._frames, axis=0)
        self._frames = []

        # 太短的多半是误触
        duration = len(audio) / SAMPLE_RATE
        if duration < 0.3:
            logger.info(f"Recording too short ({duration:.2f}s), discarded")
            return None

        RECORDINGS_DIR.mkdir(parents=True, exist_ok=True)
        path = RECORDINGS_DIR / f"{uuid_lib.uuid4()}.wav"
        self._sf.write(str(path), audio, SAMPLE_RATE)
        logger.info(f"Recording saved: {path} ({duration:.1f}s)")
        return path


class VoiceUploadWorker(QThread):
    """后台：上传录音 + 触发转写"""

    succeeded = pyqtSignal(str)   # task uuid
    failed = pyqtSignal(str, str)  # task uuid, error

    def __init__(self, db, auth, client: SupabaseClient, task_uuid: str, audio_path: Path, parent=None):
        super().__init__(parent)
        self.db = db
        self.auth = auth
        self.client = client
        self.task_uuid = task_uuid
        self.audio_path = audio_path

    def run(self):
        try:
            token = self.auth.ensure_session()
            user_id = self.auth.user_id
            if not user_id:
                raise SupabaseError("no user id available")

            object_path = f"{user_id}/{self.task_uuid}.wav"
            data = self.audio_path.read_bytes()

            self.client.upload_storage_object(
                token, config.SUPABASE_VOICE_BUCKET, object_path, data, "audio/wav"
            )
            self.db.set_task_audio_url(self.task_uuid, object_path)

            # 先把任务和 audio_url 推上云，转写函数才能在云端找到这一行
            self._push_pending(token)

            self.client.invoke_function(
                token, "transcribe", {"uuid": self.task_uuid, "audio_url": object_path}
            )
            self.succeeded.emit(self.task_uuid)

        except Exception as e:
            logger.warning(f"Voice upload/transcribe failed: {e}")
            try:
                self.db.set_transcribe_status(self.task_uuid, "failed")
            except Exception:
                pass
            self.failed.emit(self.task_uuid, str(e))

    def _push_pending(self, token: str):
        """把本地待推送的行推上去（复用同步层的时间戳归一化）"""
        from services.sync_service import local_to_iso

        dirty = self.db.get_dirty_tasks()
        if not dirty:
            return
        rows = []
        for task in dirty:
            row = task.to_remote_dict()
            row["updated_at"] = local_to_iso(row.get("updated_at"))
            row["deleted_at"] = local_to_iso(row.get("deleted_at"))
            rows.append(row)
        self.client.upsert_tasks(token, rows)
        self.db.mark_synced([t.uuid for t in dirty])
