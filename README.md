# Tododo - PyQt5 待办事项 Kanban 应用

## 🚀 直接下载使用 (Windows)

如果您不想安装 Python 环境，只想运行本软件：
1. 点击前往本项目的 [Releases](https://github.com/您的用户名/Tododo/releases) 页面。
2. 下载最新版本发布中的 **`Tododo.exe`**。
3. 双击 `Tododo.exe` 即可直接启动使用！

## 📋 项目简介

Tododo 是一个轻量级的 Windows 待办事项应用，采用 Python + PyQt5 开发，提供 Kanban 式的任务管理界面。应用显示在屏幕右下角，支持开机自启、本地数据存储、自动每日重置等功能。

## 🎯 核心功能

✅ **任务管理**
- 添加、删除、修改任务
- Kanban 三列布局：To Do → In Progress → Done
- 任务状态自动流转（复选框控制）

✅ **自动化功能**
- 每天零点自动重置：将前日的 In Progress 和 Done 任务移回 To Do
- 应用启动时发送一次 Toast 通知，显示待办任务数量
- 完成任务时弹出完成通知

✅ **开机启动**
- 支持启用/禁用开机自启动
- 通过 Windows 注册表管理

✅ **本地数据存储**
- 使用 SQLite 数据库
- 数据自动保存到 `%APPDATA%\Tododo\`
- 应用重启数据不丢失

✅ **右下角显示**
- 无边框窗口，始终置顶
- 可拖动标题栏移动
- 记忆上次窗口大小和位置

## 📁 项目结构

```
tododo/
├── main.py                    # 应用入口
├── config.py                  # 配置常量
├── requirements.txt           # 依赖包列表
│
├── models/
│   ├── __init__.py
│   └── task.py                # Task 数据模型
│
├── storage/
│   ├── __init__.py
│   └── database.py            # SQLite 数据库操作层
│
├── services/
│   ├── __init__.py
│   ├── task_service.py        # 任务业务逻辑
│   ├── notification.py        # Windows Toast 通知
│   ├── autostart.py           # 开机启动管理
│   ├── scheduler.py           # 定时重置服务
│   └── boot_notifier.py       # 开机提醒服务
│
├── ui/
│   ├── __init__.py
│   ├── main_window.py         # 主窗口
│   ├── kanban_board.py        # Kanban 组件
│   ├── task_input.py          # 任务输入组件
│   └── styles.py              # QSS 样式表
│
└── utils/
    └── __init__.py
```

## 🚀 快速开始

### 1. 环境要求
- Python 3.8+
- Windows 10/11

### 2. 安装依赖
```bash
cd tododo
pip install -r requirements.txt
```

### 3. 运行应用
```bash
python main.py
```

### 4. 打包成 .exe（可选）
```bash
# 本地打包生成 Tododo.exe
pyinstaller --noconsole --onefile --icon=resources/tododo.ico --add-data "resources;resources" main.py
```

## 📖 使用说明

### 基本操作

1. **添加任务**
   - 在底部输入框输入任务标题
   - 点击 "Add" 按钮或按 Enter
   - 任务出现在 "To Do" 列

2. **转移任务状态**
   - 在 "To Do" 列点击任务 Checkbox：状态 → "In Progress"
   - 在 "In Progress" 列点击任务 Checkbox：状态 → "Done"
   - 完成后会发送完成通知

3. **删除任务**
   - 点击任务右侧的 "×" 按钮删除

4. **每日重置**
   - 每天零点自动触发（无需手动操作）
   - 前日的 In Progress 和 Done 任务自动移回 To Do

5. **开机启动**
   - 点击窗口左上角菜单（☰）
   - 选择 "开机启动" 启用/禁用
   - 重启电脑后自动启动应用

### 快捷操作

- **拖动窗口**：在标题栏点击拖动
- **最小化**：点击 "_" 按钮（最小化到后台）
- **关闭**：点击 "×" 按钮
- **菜单**：点击 "☰" 按钮显示选项菜单

## 🔧 配置文件

数据存储位置：`C:\Users\<YourUsername>\AppData\Roaming\Tododo\`

- `tasks.db` - SQLite 数据库文件
- `window.json` - 窗口状态配置
- `tododo.log` - 应用日志

## 🎨 样式配置

所有 UI 样式定义在 `ui/styles.py`，使用 PyQt5 的 QSS（类似 CSS）。可直接修改 STYLESHEET 变量自定义界面外观。

## 🐛 故障排除

### 应用启动提示"导入错误"
- 确保已安装所有依赖：`pip install -r requirements.txt`
- 检查 Python 版本是否 >= 3.8

### Windows Toast 通知不显示
- 检查 Windows 通知设置是否已启用
- 确认 `win10toast` 已正确安装

### 开机启动不工作
- 检查注册表：`HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run`
- 应确认 "Tododo" 项指向正确的应用路径

### 数据丢失
- 检查 `%APPDATA%\Tododo\` 是否存在 `tasks.db` 文件
- 如无法恢复，删除该目录后重新启动应用重建数据库

## 📊 技术栈

| 组件 | 技术 | 版本 |
|------|------|------|
| 框架 | PyQt5 | 5.15.9 |
| 通知 | win10toast | 0.9 |
| 数据库 | SQLite3 | 内置 |
| 打包 | PyInstaller | 6.21.0 |

## 🚀 后续扩展计划

- [ ] 统计页面（本周/本月完成数统计）
- [ ] 任务优先级标记
- [ ] 分类标签
- [ ] 系统托盘集成
- [ ] 快捷键支持（Ctrl+N 快速添加）
- [ ] 任务搜索筛选
- [ ] 导出功能
- [ ] 多主题支持

## 📝 更新日志

### v1.0.0 (2026-06-16)
- ✅ 基础 CRUD 操作
- ✅ Kanban 三列布局
- ✅ 每日零点自动重置
- ✅ 开机一次性通知
- ✅ 开机启动功能
- ✅ 本地 SQLite 存储
- ✅ Windows Toast 通知

## 📄 许可证

MIT License

---

**开发者**: Xina  
**首次发布**: 2026-06-16  
**项目路径**: `d:\Xina_App\Tododo`
