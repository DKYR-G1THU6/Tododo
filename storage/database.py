"""
SQLite 数据库操作层
"""
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Optional
import config
from models.task import Task


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
        """初始化数据库表结构"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建tasks表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                task_id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                status TEXT NOT NULL,
                created_date TEXT NOT NULL,
                completed_date TEXT,
                task_type TEXT DEFAULT 'daily',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_task(self, title: str, status: str = config.TASK_STATUS_TODO, task_type: str = 'daily') -> int:
        """添加新任务"""
        today = datetime.now().strftime("%Y-%m-%d")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO tasks (title, status, created_date, task_type)
            VALUES (?, ?, ?, ?)
        ''', (title, status, today, task_type))
        
        conn.commit()
        task_id = cursor.lastrowid
        conn.close()
        
        return task_id
    
    def delete_task(self, task_id: int) -> bool:
        """删除任务"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM tasks WHERE task_id = ?', (task_id,))
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
            SET status = ?, completed_date = ?, updated_at = CURRENT_TIMESTAMP
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
            SET title = ?, updated_at = CURRENT_TIMESTAMP
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
            SET task_type = ?, updated_at = CURRENT_TIMESTAMP
            WHERE task_id = ?
        ''', (new_type, task_id))
        
        conn.commit()
        updated = cursor.rowcount > 0
        conn.close()
        
        return updated
    
    def get_task(self, task_id: int) -> Optional[Task]:
        """获取单个任务"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT task_id, title, status, created_date, completed_date, task_type
            FROM tasks WHERE task_id = ?
        ''', (task_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return Task(
                task_id=row[0],
                title=row[1],
                status=row[2],
                created_date=row[3],
                completed_date=row[4],
                task_type=row[5]
            )
        return None
    
    def get_all_tasks(self) -> List[Task]:
        """获取所有要在当前主界面显示的任务（包括所有每日任务，以及未完成的一次性任务，和今天完成的一次性任务）"""
        today = datetime.now().strftime("%Y-%m-%d")
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT task_id, title, status, created_date, completed_date, task_type
            FROM tasks 
            WHERE task_type = 'daily'
            OR (
                task_type = 'one_time'
                AND (
                    status != ?
                    OR (status = ? AND completed_date = ?)
                )
            )
            ORDER BY created_at ASC
        ''', (config.TASK_STATUS_DONE, config.TASK_STATUS_DONE, today))
        
        rows = cursor.fetchall()
        conn.close()
        
        tasks = [
            Task(
                task_id=row[0],
                title=row[1],
                status=row[2],
                created_date=row[3],
                completed_date=row[4],
                task_type=row[5]
            )
            for row in rows
        ]
        return tasks
    
    def get_tasks_by_status(self, status: str) -> List[Task]:
        """按状态获取任务（用于列展示，包括所有每日任务，以及未完成的一次性任务，和今天完成的一次性任务）"""
        today = datetime.now().strftime("%Y-%m-%d")
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT task_id, title, status, created_date, completed_date, task_type
            FROM tasks 
            WHERE status = ? 
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
        
        tasks = [
            Task(
                task_id=row[0],
                title=row[1],
                status=row[2],
                created_date=row[3],
                completed_date=row[4],
                task_type=row[5]
            )
            for row in rows
        ]
        return tasks
    
    def get_today_tasks(self) -> List[Task]:
        """获取今天需要统计的待办和进行中任务（用于每日启动通知计数，包含每日任务和未完成的一次性任务）"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT task_id, title, status, created_date, completed_date, task_type
            FROM tasks 
            WHERE (status = ? OR status = ?)
            AND (
                task_type = 'daily'
                OR (task_type = 'one_time' AND status != ?)
            )
            ORDER BY created_at ASC
        ''', (config.TASK_STATUS_TODO, config.TASK_STATUS_IN_PROGRESS, config.TASK_STATUS_DONE))
        
        rows = cursor.fetchall()
        conn.close()
        
        tasks = [
            Task(
                task_id=row[0],
                title=row[1],
                status=row[2],
                created_date=row[3],
                completed_date=row[4],
                task_type=row[5]
            )
            for row in rows
        ]
        return tasks
    
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
            WHERE task_type = 'daily' AND created_date < ? AND (status = ? OR status = ?)
        ''', (today, config.TASK_STATUS_IN_PROGRESS, config.TASK_STATUS_DONE))
        
        tasks_to_reset = cursor.fetchall()
        
        # 更新这些任务为 To Do
        for (task_id,) in tasks_to_reset:
            cursor.execute('''
                UPDATE tasks 
                SET status = ?, completed_date = NULL, updated_at = CURRENT_TIMESTAMP
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
        
        cursor.execute('''
            SELECT task_id, title, status, created_date, completed_date, task_type
            FROM tasks 
            WHERE task_type = 'one_time' AND status = ?
            ORDER BY completed_date DESC, created_at DESC
        ''', (config.TASK_STATUS_DONE,))
        
        rows = cursor.fetchall()
        conn.close()
        
        tasks = [
            Task(
                task_id=row[0],
                title=row[1],
                status=row[2],
                created_date=row[3],
                completed_date=row[4],
                task_type=row[5]
            )
            for row in rows
        ]
        return tasks
