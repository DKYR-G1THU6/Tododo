"""
应用主入口
"""
import sys
import logging
from pathlib import Path

# 添加当前目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

import config
from storage.database import Database
from services.task_service import TaskService
from services.notification import NotificationService
from services.scheduler import SchedulerService
from services.boot_notifier import BootNotifierService
from ui.main_window import MainWindow


# 配置日志
def setup_logging():
    """设置日志"""
    log_file = config.APP_DATA_DIR / "tododo.log"
    
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )


def main():
    """应用主函数"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 60)
    logger.info(f"Starting {config.APP_NAME} v{config.APP_VERSION}")
    logger.info(f"Data directory: {config.APP_DATA_DIR}")
    
    # 创建 QApplication
    app = QApplication(sys.argv)
    
    try:
        # 初始化服务
        logger.info("Initializing services...")
        
        # 数据库
        database = Database()
        
        # 任务服务
        task_service = TaskService(database)
        
        # 通知服务
        notification_service = NotificationService()
        
        # 定时重置服务
        scheduler_service = SchedulerService(task_service)
        
        # 开机提醒服务
        boot_notifier_service = BootNotifierService(task_service, notification_service)
        
        # 创建主窗口
        logger.info("Creating main window...")
        main_window = MainWindow(task_service, notification_service)
        main_window.show()
        
        # 启动服务
        logger.info("Starting services...")
        scheduler_service.start()
        
        # 延迟 1.5 秒触发开机提醒通知，避开启动时的 CPU 占用以提升启动响应速度
        QTimer.singleShot(1500, boot_notifier_service.notify_on_boot)
        
        logger.info("Application started successfully")
        
        # 运行应用
        sys.exit(app.exec_())
    
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
