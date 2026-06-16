"""
应用配置常量
"""
import os
from pathlib import Path

# 应用基本信息
APP_NAME = "Tododo"
APP_VERSION = "1.0.0"

# 数据存储路径
APP_DATA_DIR = Path(os.path.expandvars(r"%APPDATA%\Tododo"))
APP_DATA_DIR.mkdir(parents=True, exist_ok=True)

# 数据库文件路径
DATABASE_FILE = APP_DATA_DIR / "tasks.db"

# 配置文件路径
CONFIG_FILE = APP_DATA_DIR / "config.json"

# UI 配置
WINDOW_WIDTH = 380
WINDOW_HEIGHT = 520
WINDOW_MIN_WIDTH = 360
WINDOW_MIN_HEIGHT = 420

# 任务状态常量
TASK_STATUS_TODO = "todo"
TASK_STATUS_IN_PROGRESS = "in_progress"
TASK_STATUS_DONE = "done"

TASK_STATUSES = [TASK_STATUS_TODO, TASK_STATUS_IN_PROGRESS, TASK_STATUS_DONE]

# 列表标题
COLUMN_TITLES = {
    TASK_STATUS_TODO: "To Do",
    TASK_STATUS_IN_PROGRESS: "In Progress",
    TASK_STATUS_DONE: "Done"
}

# 列表顺序
COLUMN_ORDER = [TASK_STATUS_TODO, TASK_STATUS_IN_PROGRESS, TASK_STATUS_DONE]

# 注册表开机启动键
AUTOSTART_REGISTRY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
AUTOSTART_ENTRY_NAME = "Tododo"

# 当前活动语言 ("zh" 或 "en")
CURRENT_LANGUAGE = "zh"

# 中英文翻译映射
TRANSLATIONS = {
    "zh": {
        "title": "Tododo",
        "tab_todo": "待办",
        "tab_in_progress": "进行中",
        "tab_done": "已完成",
        "input_placeholder": "输入新任务...",
        "add_btn": "添加",
        "menu_autostart": "开机启动",
        "menu_always_on_top": "始终置顶",
        "menu_language": "语言 / Language",
        "menu_exit": "退出",
        "toast_autostart_on": "已启用开机启动",
        "toast_autostart_off": "已禁用开机启动",
        "toast_always_on_top_on": "已启用始终置顶",
        "toast_always_on_top_off": "已禁用始终置顶",
        "toast_task_completed": "✓ 任务完成: {title}",
        "toast_no_tasks": "今天没有待办任务",
        "toast_one_task": "您有 1 个待办任务",
        "toast_many_tasks": "您有 {count} 个待办任务",
        "toast_boot_title": "Tododo - 每日提醒",
        "toast_system_title": "Tododo"
    },
    "en": {
        "title": "Tododo",
        "tab_todo": "To Do",
        "tab_in_progress": "In Progress",
        "tab_done": "Done",
        "input_placeholder": "Enter new task...",
        "add_btn": "Add",
        "menu_autostart": "Start on Boot",
        "menu_always_on_top": "Always on Top",
        "menu_language": "Language / 语言",
        "menu_exit": "Exit",
        "toast_autostart_on": "Start on Boot enabled",
        "toast_autostart_off": "Start on Boot disabled",
        "toast_always_on_top_on": "Always on Top enabled",
        "toast_always_on_top_off": "Always on Top disabled",
        "toast_task_completed": "✓ Task Completed: {title}",
        "toast_no_tasks": "No tasks for today",
        "toast_one_task": "You have 1 task",
        "toast_many_tasks": "You have {count} tasks",
        "toast_boot_title": "Tododo - Daily Reminder",
        "toast_system_title": "Tododo"
    }
}

