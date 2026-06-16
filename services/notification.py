"""
Windows 通知服务
"""
import logging

logger = logging.getLogger(__name__)


class NotificationService:
    """Windows Toast 通知服务"""
    
    def __init__(self):
        """初始化通知服务"""
        self._notifier = None
        
    @property
    def notifier(self):
        """延迟加载并获取 ToastNotifier 实例"""
        if self._notifier is None:
            try:
                from win10toast import ToastNotifier
                self._notifier = ToastNotifier()
            except Exception as e:
                logger.error(f"Failed to import or initialize win10toast: {e}")
        return self._notifier

    
    def notify(self, title: str, message: str, duration: int = 5) -> bool:
        """
        显示 Windows Toast 通知
        
        Args:
            title: 通知标题
            message: 通知内容
            duration: 显示时长（秒）
        
        Returns:
            是否成功显示
        """
        try:
            notifier = self.notifier
            if not notifier:
                logger.error("ToastNotifier is not available.")
                return False
            # 在 Windows 上显示 Toast 通知
            notifier.show_toast(
                title=title,
                msg=message,
                duration=duration,
                threaded=True
            )
            logger.debug(f"Notification shown: {title}")
            return True
        except Exception as e:
            logger.error(f"Failed to show notification: {e}")
            return False
    
    def get_text(self, key: str, **kwargs) -> str:
        """获取本地化翻译文本"""
        import config
        lang = getattr(config, "CURRENT_LANGUAGE", "zh")
        return config.TRANSLATIONS[lang][key].format(**kwargs)

    def notify_task_completed(self, task_title: str) -> bool:
        """通知任务完成"""
        title = self.get_text("toast_system_title")
        msg = self.get_text("toast_task_completed", title=task_title)
        return self.notify(title, msg, duration=5)
    
    def notify_tasks_summary(self, count: int) -> bool:
        """通知今日任务摘要"""
        title = self.get_text("toast_boot_title")
        if count == 0:
            msg = self.get_text("toast_no_tasks")
        elif count == 1:
            msg = self.get_text("toast_one_task")
        else:
            msg = self.get_text("toast_many_tasks", count=count)
        
        return self.notify(title, msg, duration=5)
