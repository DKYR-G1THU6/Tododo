"""
开机提醒服务
应用启动时检查待办任务数量，发送一次 Toast 通知
"""
import logging

logger = logging.getLogger(__name__)


class BootNotifierService:
    """开机提醒服务"""
    
    def __init__(self, task_service, notification_service):
        """
        初始化开机提醒服务
        
        Args:
            task_service: TaskService 实例
            notification_service: NotificationService 实例
        """
        self.task_service = task_service
        self.notification_service = notification_service
    
    def notify_on_boot(self):
        """应用启动时发送提醒"""
        try:
            # 获取今日待办任务数量
            count = self.task_service.get_today_tasks_count()
            
            # 发送通知
            self.notification_service.notify_tasks_summary(count)
            logger.info(f"Boot notification sent: {count} tasks")
        except Exception as e:
            logger.error(f"Failed to send boot notification: {e}")
