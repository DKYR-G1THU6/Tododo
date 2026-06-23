"""
应用配置常量
"""
import os
from pathlib import Path

# 应用基本信息
APP_NAME = "Tododo"
APP_VERSION = "1.1.2"

# GitHub Release 信息
GITHUB_REPO_OWNER = "DKYR-G1THU6"
GITHUB_REPO_NAME = "Tododo"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/releases/latest"
GITHUB_RELEASE_URL = f"https://github.com/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/releases/latest"

# 数据库 Schema 版本
DB_SCHEMA_VERSION = 2

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
from language.CN import TRANSLATION as cn_translation
from language.EN import TRANSLATION as en_translation

TRANSLATIONS = {
    "zh": cn_translation,
    "en": en_translation
}

