"""
SQLite 数据库操作层
"""
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional
import config
from models.task import Task


# 所有 SELECT 统一使用的列顺序，与 _row_to_task 一一对应
_TASK_COLUMNS = (
    "task_id, uuid, title, status, created_date, completed_date, task_type, "
    "updated_at, deleted, deleted_at, dirty, has_voice, audio_path, audio_url, "
    "transcript, transcribe_status"
)


class Database:
    """数据库管理类"""

    def __init__(self, db_path: Path = config.DATABASE_FILE):
        """初始化数据库连接"""
        self.db_path = db_path
        self.init_db()

        # 运行 Schema 迁移
        from storage.migrator import DatabaseMigrator
        migrator = DatabaseMigrator(self.db_path)
        migrator.migrate(config.DB_SCHEMA_VERSION)

    def init_db(self):
        """初始化数据库表结构（全新安装时创建含同步字段的完整表）"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 创建tasks表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                task_id INTEGER PRIMARY KEY AUTOINCREMENT,
                uuid TEXT,
                title TEXT NOT NULL,
                status TEXT NOT NULL,
                created_date TEXT NOT NULL,
                completed_date TEXT,
                task_type TEXT DEFAULT 'daily',
                deleted INTEGER DEFAULT 0,
                deleted_at TIMESTAMP,
                dirty INTEGER DEFAULT 0,
                has_voice INTEGER DEFAULT 0,
                audio_path TEXT,
                audio_url TEXT,
                transcript TEXT,
                transcribe_status TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        conn.close()

    @staticmethod
    def _row_to_task(row) -> Task:
        """把一行（按 _TASK_COLUMNS 顺序）转换为 Task 对象"""
        return Task(
            task_id=row[0],
            uuid=row[1],
            title=row[2],
            status=row[3],
            created_date=row[4],
            completed_date=row[5],
            task_type=row[6],
            updated_at=row[7],
            deleted=row[8],
            deleted_at=row[9],
            dirty=row[10],
            has_voice=row[11],
            audio_path=row[12],
            audio_url=row[13],
            transcript=row[14],
            transcribe_status=row[15],
        )

    def add_task(self, title: str, status: str = config.TASK_STATUS_TODO, task_type: str = 'daily') -> int:
        """添加新任务（生成全局 uuid，并标记为待推送）"""
        today = datetime.now().strftime("%Y-%m-%d")
        new_uuid = str(uuid.uuid4())

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO tasks (uuid, title, status, created_date, task_type, dirty)
            VALUES (?, ?, ?, ?, ?, 1)
        ''', (new_uuid, title, status, today, task_type))

        conn.commit()
        task_id = cursor.lastrowid
        conn.close()

        return task_id

    def delete_task(self, task_id: int) -> bool:
        """删除任务（软删除：打墓碑标记，让删除可同步）"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE tasks
            SET deleted = 1, deleted_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP, dirty = 1
            WHERE task_id = ? AND deleted = 0
        ''', (task_id,))
        conn.commit()

        deleted = cursor.rowcount > 0
        conn.close()

        return deleted

    def update_task_status(self, task_id: int, new_status: str) -> bool:
        """更新任务状态"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        completed_date = None
        if new_status == config.TASK_STATUS_DONE:
            completed_date = datetime.now().strftime("%Y-%m-%d")

        cursor.execute('''
            UPDATE tasks
            SET status = ?, completed_date = ?, updated_at = CURRENT_TIMESTAMP, dirty = 1
            WHERE task_id = ?
        ''', (new_status, completed_date, task_id))

        conn.commit()
        updated = cursor.rowcount > 0
        conn.close()

        return updated

    def update_task_title(self, task_id: int, new_title: str) -> bool:
        """更新任务标题"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE tasks
            SET title = ?, updated_at = CURRENT_TIMESTAMP, dirty = 1
            WHERE task_id = ?
        ''', (new_title, task_id))

        conn.commit()
        updated = cursor.rowcount > 0
        conn.close()

        return updated

    def update_task_type(self, task_id: int, new_type: str) -> bool:
        """更新任务类型 (daily 或 one_time)"""
        if new_type not in ('daily', 'one_time'):
            return False
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE tasks
            SET task_type = ?, updated_at = CURRENT_TIMESTAMP, dirty = 1
            WHERE task_id = ?
        ''', (new_type, task_id))

        conn.commit()
        updated = cursor.rowcount > 0
        conn.close()

        return updated

    def get_task(self, task_id: int) -> Optional[Task]:
        """获取单个任务（按本地 task_id，不过滤 deleted，供内部/同步使用）"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(f'''
            SELECT {_TASK_COLUMNS}
            FROM tasks WHERE task_id = ?
        ''', (task_id,))

        row = cursor.fetchone()
        conn.close()

        if row:
            return self._row_to_task(row)
        return None

    def get_all_tasks(self) -> List[Task]:
        """获取所有要在当前主界面显示的任务（包括所有每日任务，以及未完成的一次性任务，和今天完成的一次性任务）"""
        today = datetime.now().strftime("%Y-%m-%d")
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(f'''
            SELECT {_TASK_COLUMNS}
            FROM tasks
            WHERE deleted = 0
            AND (
                task_type = 'daily'
                OR (
                    task_type = 'one_time'
                    AND (
                        status != ?
                        OR (status = ? AND completed_date = ?)
                    )
                )
            )
            ORDER BY created_at ASC
        ''', (config.TASK_STATUS_DONE, config.TASK_STATUS_DONE, today))

        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_task(row) for row in rows]

    def get_tasks_by_status(self, status: str) -> List[Task]:
        """按状态获取任务（用于列展示，包括所有每日任务，以及未完成的一次性任务，和今天完成的一次性任务）"""
        today = datetime.now().strftime("%Y-%m-%d")
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(f'''
            SELECT {_TASK_COLUMNS}
            FROM tasks
            WHERE deleted = 0
            AND status = ?
            AND (
                task_type = 'daily'
                OR (
                    task_type = 'one_time'
                    AND (
                        status != ?
                        OR (status = ? AND completed_date = ?)
                    )
                )
            )
            ORDER BY created_at ASC
        ''', (status, config.TASK_STATUS_DONE, config.TASK_STATUS_DONE, today))

        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_task(row) for row in rows]

    def get_today_tasks(self) -> List[Task]:
        """获取今天需要统计的待办和进行中任务（用于每日启动通知计数，包含每日任务和未完成的一次性任务）"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(f'''
            SELECT {_TASK_COLUMNS}
            FROM tasks
            WHERE deleted = 0
            AND (status = ? OR status = ?)
            AND (
                task_type = 'daily'
                OR (task_type = 'one_time' AND status != ?)
            )
            ORDER BY created_at ASC
        ''', (config.TASK_STATUS_TODO, config.TASK_STATUS_IN_PROGRESS, config.TASK_STATUS_DONE))

        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_task(row) for row in rows]

    def reset_daily_tasks(self) -> int:
        """
        每日重置：将前日的 In Progress 和 Done 状态的每日任务改为 To Do
        返回重置的任务数量
        """
        today = datetime.now().strftime("%Y-%m-%d")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 只查询前日的 task_type 为 daily 的 in_progress 和 done 任务
        cursor.execute('''
            SELECT task_id FROM tasks
            WHERE deleted = 0 AND task_type = 'daily' AND created_date < ? AND (status = ? OR status = ?)
        ''', (today, config.TASK_STATUS_IN_PROGRESS, config.TASK_STATUS_DONE))

        tasks_to_reset = cursor.fetchall()

        # 更新这些任务为 To Do
        for (task_id,) in tasks_to_reset:
            cursor.execute('''
                UPDATE tasks
                SET status = ?, completed_date = NULL, updated_at = CURRENT_TIMESTAMP, dirty = 1
                WHERE task_id = ?
            ''', (config.TASK_STATUS_TODO, task_id))

        conn.commit()
        reset_count = len(tasks_to_reset)
        conn.close()

        return reset_count

    def get_completed_one_time_tasks(self) -> List[Task]:
        """获取所有已完成的一次性任务历史记录，按完成时间降序排列"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(f'''
            SELECT {_TASK_COLUMNS}
            FROM tasks
            WHERE deleted = 0 AND task_type = 'one_time' AND status = ?
            ORDER BY completed_date DESC, created_at DESC
        ''', (config.TASK_STATUS_DONE,))

        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_task(row) for row in rows]

    # ============================
    # 同步用方法（本地操作，供 M3 的 sync_service 调用）
    # ============================

    def get_dirty_tasks(self) -> List[Task]:
        """获取所有本地待推送（dirty=1）的任务，含已软删除的墓碑行"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(f"SELECT {_TASK_COLUMNS} FROM tasks WHERE dirty = 1")
        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_task(row) for row in rows]

    def mark_synced(self, uuids: List[str]) -> None:
        """把指定 uuid 的行标记为已同步（dirty=0）"""
        if not uuids:
            return
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        placeholders = ",".join("?" for _ in uuids)
        cursor.execute(f"UPDATE tasks SET dirty = 0 WHERE uuid IN ({placeholders})", tuple(uuids))
        conn.commit()
        conn.close()

    def get_max_updated_at(self) -> Optional[str]:
        """获取本地最大的 updated_at，作为增量拉取游标"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT MAX(updated_at) FROM tasks")
        row = cursor.fetchone()
        conn.close()

        return row[0] if row and row[0] else None

    def upsert_from_remote(self, remote_rows: List[dict]) -> int:
        """
        把云端行合并进本地（LWW：仅当 remote.updated_at 更新时才覆盖）。

        remote_rows 每项至少包含 uuid、updated_at 及任务字段。
        注意：调用方（sync_service）需保证 updated_at 为可按字符串比较的统一 UTC 格式。
        返回实际写入（新增或更新）的行数。
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        written = 0
        try:
            for r in remote_rows:
                r_uuid = r.get('uuid')
                if not r_uuid:
                    continue

                cursor.execute("SELECT updated_at FROM tasks WHERE uuid = ?", (r_uuid,))
                existing = cursor.fetchone()

                if existing is None:
                    cursor.execute('''
                        INSERT INTO tasks (
                            uuid, title, status, created_date, completed_date, task_type,
                            updated_at, deleted, deleted_at, dirty, has_voice, audio_url,
                            transcript, transcribe_status
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?)
                    ''', (
                        r_uuid, r.get('title'), r.get('status'), r.get('created_date'),
                        r.get('completed_date'), r.get('task_type', 'daily'),
                        r.get('updated_at'), r.get('deleted', 0), r.get('deleted_at'),
                        r.get('has_voice', 0), r.get('audio_url'),
                        r.get('transcript'), r.get('transcribe_status')
                    ))
                    written += 1
                else:
                    local_updated = existing[0]
                    remote_updated = r.get('updated_at')
                    if remote_updated and (local_updated is None or remote_updated > local_updated):
                        cursor.execute('''
                            UPDATE tasks SET
                                title = ?, status = ?, created_date = ?, completed_date = ?,
                                task_type = ?, updated_at = ?, deleted = ?, deleted_at = ?,
                                has_voice = ?, audio_url = ?, transcript = ?, transcribe_status = ?,
                                dirty = 0
                            WHERE uuid = ?
                        ''', (
                            r.get('title'), r.get('status'), r.get('created_date'),
                            r.get('completed_date'), r.get('task_type', 'daily'),
                            remote_updated, r.get('deleted', 0), r.get('deleted_at'),
                            r.get('has_voice', 0), r.get('audio_url'),
                            r.get('transcript'), r.get('transcribe_status'), r_uuid
                        ))
                        written += 1

            conn.commit()
        finally:
            conn.close()

        return written
