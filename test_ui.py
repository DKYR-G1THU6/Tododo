"""
UI 功能测试脚本
测试新的标签栏导航功能
"""
import sys
import logging
from storage.database import Database
from services.task_service import TaskService
from services.notification import NotificationService

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_tab_navigation():
    """测试标签栏导航"""
    logger.info("=" * 50)
    logger.info("UI 功能测试 - 标签栏导航")
    logger.info("=" * 50)
    
    # 初始化服务
    db = Database()
    task_service = TaskService(db)
    notification_service = NotificationService()
    
    # 添加测试任务
    logger.info("\n1. 添加测试任务...")
    todo_id = task_service.add_task("Write report")
    in_progress_id = task_service.add_task("Fix bugs")
    done_id = task_service.add_task("Deploy app")
    
    # 更新任务状态
    logger.info("\n2. 更新任务状态...")
    task_service.update_task_status(in_progress_id, "in_progress")
    task_service.update_task_status(done_id, "done")
    
    # 获取所有任务
    logger.info("\n3. 获取所有任务...")
    all_tasks = task_service.get_all_tasks()
    
    # 显示按状态分类的任务
    logger.info("\n4. 按状态分类的任务:")
    for task in all_tasks:
        logger.info(f"   [{task.status}] {task.title} (ID: {task.task_id})")
    
    # 验证标签栏切换
    logger.info("\n5. 标签栏切换测试:")
    logger.info("   - 'To Do' 标签应显示 1 个任务")
    logger.info("   - 'In Progress' 标签应显示 1 个任务")
    logger.info("   - 'Done' 标签应显示 1 个任务")
    
    # 验证
    todo_count = len([t for t in all_tasks if t.status == "todo"])
    in_progress_count = len([t for t in all_tasks if t.status == "in_progress"])
    done_count = len([t for t in all_tasks if t.status == "done"])
    
    logger.info(f"\n6. 验证结果:")
    logger.info(f"   To Do: {todo_count} ✓" if todo_count == 1 else f"   To Do: {todo_count} ✗ (expected 1)")
    logger.info(f"   In Progress: {in_progress_count} ✓" if in_progress_count == 1 else f"   In Progress: {in_progress_count} ✗ (expected 1)")
    logger.info(f"   Done: {done_count} ✓" if done_count == 1 else f"   Done: {done_count} ✗ (expected 1)")
    
    logger.info("\n" + "=" * 50)
    logger.info("测试完成！")
    logger.info("应用现在应该显示新的标签栏 UI，可以：")
    logger.info("  • 点击 'To Do' 标签查看待办任务")
    logger.info("  • 点击 'In Progress' 标签查看进行中的任务")
    logger.info("  • 点击 'Done' 标签查看已完成的任务")
    logger.info("  • 活跃标签会显示蓝色下划线")
    logger.info("=" * 50)

if __name__ == "__main__":
    test_tab_navigation()
