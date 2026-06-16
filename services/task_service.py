"""
任务业务逻辑服务
"""
from typing import List, Callable
import config
from models.task import Task
from storage.database import Database


class TaskService:
    """任务服务类"""
    
    def __init__(self, db: Database):
        """初始化任务服务"""
        self.db = db
        self.update_callbacks: List[Callable] = []  # UI 更新回调
    
    def register_update_callback(self, callback: Callable):
        """注册 UI 更新回调"""
        self.update_callbacks.append(callback)
    
    def notify_update(self):
        """触发所有回调"""
        for callback in self.update_callbacks:
            callback()
    
    def add_task(self, title: str) -> int:
        """添加新任务"""
        task_id = self.db.add_task(title, config.TASK_STATUS_TODO)
        self.notify_update()
        return task_id
    
    def delete_task(self, task_id: int) -> bool:
        """删除任务"""
        result = self.db.delete_task(task_id)
        if result:
            self.notify_update()
        return result
    
    def update_task_status(self, task_id: int, new_status: str) -> bool:
        """更新任务状态"""
        if new_status not in config.TASK_STATUSES:
            return False
        
        result = self.db.update_task_status(task_id, new_status)
        if result:
            self.notify_update()
        return result
    
    def update_task_title(self, task_id: int, new_title: str) -> bool:
        """更新任务标题"""
        result = self.db.update_task_title(task_id, new_title)
        if result:
            self.notify_update()
        return result
    
    def get_next_status(self, current_status: str) -> str:
        """获取下一个状态"""
        status_flow = {
            config.TASK_STATUS_TODO: config.TASK_STATUS_IN_PROGRESS,
            config.TASK_STATUS_IN_PROGRESS: config.TASK_STATUS_DONE,
            config.TASK_STATUS_DONE: config.TASK_STATUS_TODO
        }
        return status_flow.get(current_status, config.TASK_STATUS_TODO)
    
    def get_all_tasks(self) -> List[Task]:
        """获取所有任务"""
        return self.db.get_all_tasks()
    
    def get_tasks_by_status(self, status: str) -> List[Task]:
        """按状态获取任务"""
        return self.db.get_tasks_by_status(status)
    
    def get_today_tasks_count(self) -> int:
        """获取今天的待办任务数量"""
        tasks = self.db.get_today_tasks()
        return len(tasks)
    
    def reset_daily_tasks(self) -> int:
        """每日重置任务"""
        reset_count = self.db.reset_daily_tasks()
        if reset_count > 0:
            self.notify_update()
        return reset_count
