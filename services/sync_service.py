"""
同步引擎：本地优先 + last-write-wins

每轮同步固定「先推后拉」：
  1) push：把本地 dirty=1 的行（含软删除墓碑）upsert 到云端，成功后清 dirty
  2) pull：按高水位游标拉取云端更新的行，按 updated_at 做 LWW 合并进本地

沿用 services/update_service.py 的 QThread + pyqtSignal 模式，网络操作不阻塞 Qt UI 线程。
"""
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from PyQt5.QtCore import QObject, QThread, QTimer, pyqtSignal

import config
from services.supabase_client import SupabaseClient, SupabaseError

logger = logging.getLogger(__name__)


# ============================
# 时间戳归一化
# 本地 SQLite: 'YYYY-MM-DD HH:MM:SS'（CURRENT_TIMESTAMP，UTC）
# 云端 Postgres: RFC3339，如 '2026-07-18T12:34:56.789+00:00'
# 两边都保持 UTC，且转换后仍可按字符串比较（保留小数秒不破坏字典序）
# ============================

def local_to_iso(ts: Optional[str]) -> Optional[str]:
    """本地时间戳 -> RFC3339 UTC（上推/做游标时用）"""
    if not ts:
        return None
    ts = ts.strip()
    if "T" in ts:
        return ts  # 已经是 ISO
    return ts.replace(" ", "T") + "Z"


def iso_to_local(ts: Optional[str]) -> Optional[str]:
    """RFC3339 -> 本地时间戳格式（统一转成 UTC；保留小数秒以免丢精度）"""
    if not ts:
        return None
    raw = ts.strip()
    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        logger.warning(f"Unparseable timestamp from server: {raw}")
        return raw
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    # 统一到毫秒，与本地 SQLite 的 strftime('%Y-%m-%d %H:%M:%f','now') 格式一致，
    # 保证两边的时间戳字符串可以直接按字典序比较
    return f"{dt.strftime('%Y-%m-%d %H:%M:%S')}.{dt.microsecond // 1000:03d}"


class SyncState:
    """持久化同步状态（目前只有增量拉取的高水位游标）"""

    def __init__(self, path: Path = config.SYNC_STATE_FILE):
        self.path = path
        self._state = self._load()

    def _load(self) -> dict:
        if not self.path.exists():
            return {}
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to read sync state, starting fresh: {e}")
            return {}

    @property
    def pull_cursor(self) -> Optional[str]:
        """上次从服务端拉到的最大 updated_at（RFC3339）"""
        return self._state.get("pull_cursor")

    def set_pull_cursor(self, cursor: str):
        self._state["pull_cursor"] = cursor
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self._state, f)
        except Exception as e:
            logger.error(f"Failed to persist sync state: {e}")

    def reset(self):
        """清空游标（切换账号/重新配对后需要全量重拉）"""
        self._state = {}
        try:
            if self.path.exists():
                self.path.unlink()
        except Exception as e:
            logger.warning(f"Failed to remove sync state: {e}")


class SyncWorker(QThread):
    """执行一轮「先推后拉」的后台线程"""

    finished_ok = pyqtSignal(int, int)   # pushed, pulled
    failed = pyqtSignal(str)

    def __init__(self, db, auth, client: SupabaseClient, state: SyncState, parent=None):
        super().__init__(parent)
        self.db = db
        self.auth = auth
        self.client = client
        self.state = state

    def run(self):
        try:
            token = self.auth.ensure_session()
            pushed = self._push(token)
            pulled = self._pull(token)
            self.finished_ok.emit(pushed, pulled)
        except SupabaseError as e:
            # 离线/服务端报错都走这里，下轮再试即可
            logger.warning(f"Sync failed: {e}")
            self.failed.emit(str(e))
        except Exception as e:
            logger.error(f"Unexpected sync error: {e}", exc_info=True)
            self.failed.emit(str(e))

    def _push(self, token: str) -> int:
        """把本地 dirty 行推上云"""
        dirty_tasks = self.db.get_dirty_tasks()
        if not dirty_tasks:
            return 0

        rows = []
        for task in dirty_tasks:
            row = task.to_remote_dict()
            row["updated_at"] = local_to_iso(row.get("updated_at"))
            row["deleted_at"] = local_to_iso(row.get("deleted_at"))
            rows.append(row)

        self.client.upsert_tasks(token, rows)
        self.db.mark_synced([t.uuid for t in dirty_tasks])
        logger.info(f"Sync push: {len(rows)} row(s)")
        return len(rows)

    def _pull(self, token: str) -> int:
        """按高水位游标增量拉取并合并"""
        cursor = self.state.pull_cursor
        remote_rows = self.client.fetch_tasks_since(token, cursor)
        if not remote_rows:
            return 0

        # 游标只依据服务端返回值推进（服务端已按 updated_at 升序返回）
        newest = max((r.get("updated_at") for r in remote_rows if r.get("updated_at")), default=None)

        normalized = []
        for r in remote_rows:
            row = dict(r)
            row["updated_at"] = iso_to_local(r.get("updated_at"))
            row["deleted_at"] = iso_to_local(r.get("deleted_at"))
            normalized.append(row)

        written = self.db.upsert_from_remote(normalized)
        if newest:
            self.state.set_pull_cursor(newest)
        logger.info(f"Sync pull: {len(remote_rows)} row(s) fetched, {written} applied")
        return written


class SyncService(QObject):
    """对外的同步入口：合并重复请求 + 定时轮询"""

    sync_started = pyqtSignal()
    sync_succeeded = pyqtSignal(int, int)   # pushed, pulled
    sync_failed = pyqtSignal(str)

    def __init__(self, db, auth, client: Optional[SupabaseClient] = None, parent=None):
        super().__init__(parent)
        self.db = db
        self.auth = auth
        self.client = client or SupabaseClient()
        self.state = SyncState()

        self._worker: Optional[SyncWorker] = None
        self._pending = False   # 同步进行中又来了新请求，结束后补一轮

        self._timer = QTimer(self)
        self._timer.timeout.connect(self.request_sync)

    # ============================
    # 对外
    # ============================

    def start_auto_sync(self, interval_seconds: int = config.SYNC_POLL_INTERVAL):
        """启动定时轮询，并立即同步一次"""
        self._timer.start(interval_seconds * 1000)
        self.request_sync()

    def stop_auto_sync(self):
        self._timer.stop()

    def shutdown(self, wait_ms: int = 3000):
        """退出前调用：停掉轮询并等待正在跑的同步收尾，避免线程被强行销毁"""
        self._pending = False
        self._timer.stop()
        if self._worker is not None and self._worker.isRunning():
            logger.info("Waiting for in-flight sync to finish before exit...")
            self._worker.wait(wait_ms)

    def request_sync(self):
        """请求同步；若已有同步在跑，则记下待办，结束后再补一轮"""
        if self._worker is not None and self._worker.isRunning():
            self._pending = True
            return

        self._worker = SyncWorker(self.db, self.auth, self.client, self.state)
        self._worker.finished_ok.connect(self._on_success)
        self._worker.failed.connect(self._on_failure)
        self._worker.finished.connect(self._on_thread_finished)
        self.sync_started.emit()
        self._worker.start()

    # ============================
    # 内部回调
    # ============================

    def _on_success(self, pushed: int, pulled: int):
        self.sync_succeeded.emit(pushed, pulled)

    def _on_failure(self, message: str):
        self.sync_failed.emit(message)

    def _on_thread_finished(self):
        self._worker = None
        if self._pending:
            self._pending = False
            self.request_sync()
