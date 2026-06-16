"""
定时重置服务
每天零点自动重置前日的 In Progress 和 Done 任务为 To Do
"""
from PyQt5.QtCore import QTimer, QTime, QDateTime
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class SchedulerService:
    """定时任务调度服务"""
    
    def __init__(self, task_service):
        """
        初始化定时服务
        
        Args:
            task_service: TaskService 实例
        """
        self.task_service = task_service
        self.timer = QTimer()
        self.timer.timeout.connect(self._check_daily_reset)
        self.last_reset_date = None
    
    def start(self):
        """启动定时器"""
        # 每秒检查一次
        self.timer.start(1000)
        logger.info("Scheduler started")
    
    def stop(self):
        """停止定时器"""
        self.timer.stop()
        logger.info("Scheduler stopped")
    
    def _check_daily_reset(self):
        """检查是否需要每日重置"""
        today = datetime.now().strftime("%Y-%m-%d")
        
        # 只在每天第一次检查时执行重置
        if self.last_reset_date != today:
            self.last_reset_date = today
            reset_count = self.task_service.reset_daily_tasks()
            if reset_count > 0:
                logger.info(f"Daily reset completed: {reset_count} tasks reset")
