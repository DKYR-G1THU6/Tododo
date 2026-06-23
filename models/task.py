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
        task_type: str = 'daily'
    ):
        """
        初始化任务对象
        
        Args:
            task_id: 任务ID
            title: 任务标题
            status: 任务状态 (todo/in_progress/done)
            created_date: 创建日期 (YYYY-MM-DD)
            completed_date: 完成日期 (YYYY-MM-DD) 可选
            task_type: 任务类型 (daily/one_time)
        """
        self.task_id = task_id
        self.title = title
        self.status = status
        self.created_date = created_date
        self.completed_date = completed_date
        self.task_type = task_type
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'task_id': self.task_id,
            'title': self.title,
            'status': self.status,
            'created_date': self.created_date,
            'completed_date': self.completed_date,
            'task_type': self.task_type
        }
    
    @staticmethod
    def from_dict(data: dict) -> 'Task':
        """从字典创建Task对象"""
        return Task(
            task_id=data['task_id'],
            title=data['title'],
            status=data['status'],
            created_date=data['created_date'],
            completed_date=data.get('completed_date'),
            task_type=data.get('task_type', 'daily')
        )
    
    def __repr__(self):
        return f"Task(id={self.task_id}, title='{self.title}', status='{self.status}')"
