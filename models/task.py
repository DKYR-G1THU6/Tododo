"""
Task 数据模型
"""
from datetime import datetime
from typing import Optional
import json


class Task:
    """待办任务模型"""

    def __init__(
        self,
        task_id: int,
        title: str,
        status: str,
        created_date: str,
        completed_date: Optional[str] = None,
        task_type: str = 'daily',
        uuid: Optional[str] = None,
        updated_at: Optional[str] = None,
        deleted: int = 0,
        deleted_at: Optional[str] = None,
        dirty: int = 0,
        has_voice: int = 0,
        audio_path: Optional[str] = None,
        audio_url: Optional[str] = None,
        transcript: Optional[str] = None,
        transcribe_status: Optional[str] = None
    ):
        """
        初始化任务对象

        Args:
            task_id: 本地自增 ID（设备内部使用）
            title: 任务标题
            status: 任务状态 (todo/in_progress/done)
            created_date: 创建日期 (YYYY-MM-DD)
            completed_date: 完成日期 (YYYY-MM-DD) 可选
            task_type: 任务类型 (daily/one_time)
            uuid: 全局唯一 ID（跨设备同步主键）
            updated_at: 最后修改时间（UTC，LWW 冲突判定用）
            deleted: 软删除墓碑标记 (0/1)
            deleted_at: 删除时间
            dirty: 本地待推送标记 (0/1)
            has_voice: 是否带语音 (0/1)
            audio_path: 本地录音文件路径
            audio_url: 云端 Storage 上录音的路径/URL
            transcript: 语音转出的文字
            transcribe_status: 转写状态 (pending/done/failed)
        """
        self.task_id = task_id
        self.title = title
        self.status = status
        self.created_date = created_date
        self.completed_date = completed_date
        self.task_type = task_type
        self.uuid = uuid
        self.updated_at = updated_at
        self.deleted = deleted
        self.deleted_at = deleted_at
        self.dirty = dirty
        self.has_voice = has_voice
        self.audio_path = audio_path
        self.audio_url = audio_url
        self.transcript = transcript
        self.transcribe_status = transcribe_status

    def to_dict(self) -> dict:
        """转换为字典（包含所有本地字段）"""
        return {
            'task_id': self.task_id,
            'title': self.title,
            'status': self.status,
            'created_date': self.created_date,
            'completed_date': self.completed_date,
            'task_type': self.task_type,
            'uuid': self.uuid,
            'updated_at': self.updated_at,
            'deleted': self.deleted,
            'deleted_at': self.deleted_at,
            'dirty': self.dirty,
            'has_voice': self.has_voice,
            'audio_path': self.audio_path,
            'audio_url': self.audio_url,
            'transcript': self.transcript,
            'transcribe_status': self.transcribe_status
        }

    def to_remote_dict(self) -> dict:
        """转换为云端同步载荷（只含需要上云的字段，剔除本地专用字段）"""
        return {
            'uuid': self.uuid,
            'title': self.title,
            'status': self.status,
            'created_date': self.created_date,
            'completed_date': self.completed_date,
            'task_type': self.task_type,
            'updated_at': self.updated_at,
            'deleted': self.deleted,
            'deleted_at': self.deleted_at,
            'has_voice': self.has_voice,
            'audio_url': self.audio_url,
            'transcript': self.transcript,
            'transcribe_status': self.transcribe_status
        }

    @staticmethod
    def from_dict(data: dict) -> 'Task':
        """从字典创建Task对象（对旧字典也兼容）"""
        return Task(
            task_id=data.get('task_id'),
            title=data['title'],
            status=data['status'],
            created_date=data['created_date'],
            completed_date=data.get('completed_date'),
            task_type=data.get('task_type', 'daily'),
            uuid=data.get('uuid'),
            updated_at=data.get('updated_at'),
            deleted=data.get('deleted', 0),
            deleted_at=data.get('deleted_at'),
            dirty=data.get('dirty', 0),
            has_voice=data.get('has_voice', 0),
            audio_path=data.get('audio_path'),
            audio_url=data.get('audio_url'),
            transcript=data.get('transcript'),
            transcribe_status=data.get('transcribe_status')
        )

    def __repr__(self):
        return f"Task(id={self.task_id}, uuid={self.uuid}, title='{self.title}', status='{self.status}')"
