# UI 现代化更新 - Tab 导航设计

## 更新概述

应用已升级为现代化标签栏（Tab Bar）导航设计，替代了原有的三列 Kanban 布局。

## 新增功能

### 1. 标签栏导航（TabBar）
- **位置**：应用顶部，在标题栏下方
- **标签**：三个独立标签按钮
  - "To Do" - 待办任务
  - "In Progress" - 进行中任务
  - "Done" - 已完成任务
- **样式**：现代化设计
  - 活跃标签：蓝色下划线 (#2563eb)
  - 非活跃标签：灰色背景 (#f5f5f5)
  - 悬停效果：浅灰色背景 (#e8e8e8)
  - 点击时平滑切换

### 2. 单列视图（SingleColumnView）
- 根据选中的标签显示对应的任务列表
- 显示该状态下的所有任务
- 支持任务操作（勾选、删除）

### 3. 现代化样式
- **配色方案**：
  - 主色：#2563eb（蓝色）
  - 辅助色：#10b981（绿色）、#ef4444（红色）
  - 背景：#ffffff（白色）、#f9fafb（浅灰）
  - 文字：#1a1a1a（深灰）

- **排版**：
  - 字体：Segoe UI（Windows 原生字体）
  - 标签栏按钮：11pt，加粗（Bold 600-700）
  - 应用标题：13pt，加粗

- **圆角和间距**：
  - 按钮圆角：6px
  - 任务项圆角：6px
  - 列表容器：8px
  - 间距：8-12px

## 技术实现

### 新增文件

1. **ui/tab_bar.py**
   - TabBar 组件类
   - 信号：`tab_changed(tab_id: str)`
   - 方法：`on_tab_clicked(tab_id: str)`, `get_active_tab()`

2. **ui/single_column_view.py**
   - SingleColumnView 组件类
   - 单个状态的任务列表视图
   - 信号：`status_changed(task_id, new_status)`, `deleted(task_id)`

### 修改的文件

1. **ui/main_window.py**
   - 集成 TabBar 和 SingleColumnView
   - 使用 QStackedWidget 管理多个视图
   - 连接标签栏信号到视图切换

2. **ui/styles.py**
   - 完整重写样式表
   - 添加现代化配色方案
   - 优化所有组件的外观

## 用户交互流程

```
用户启动应用
    ↓
应用显示标题栏 + 标签栏 + 任务列表 + 输入框
    ↓
用户点击标签（To Do / In Progress / Done）
    ↓
对应标签的视图加载并显示
    ↓
用户可以：
  • 勾选任务→状态改变
  • 删除任务→任务移除
  • 输入新任务→添加到 To Do
    ↓
用户点击另一个标签
    ↓
视图平滑切换，显示新的任务列表
```

## 新增组件属性

### TabBar
```python
tabs: dict  # {status_id: display_label}
active_tab: str  # 当前活跃标签的 ID
tab_buttons: dict  # {status_id: QPushButton}
```

### SingleColumnView
```python
status: str  # 该视图对应的任务状态
tasks: dict  # {task_id: Task}
item_widgets: dict  # {task_id: TaskItemWidget}
list_widget: QListWidget  # 任务列表
```

## 样式应用

所有样式通过 QSS（Qt Stylesheet）实现，具体规则见 `ui/styles.py`：

- `#tabButton` - 非活跃标签按钮
- `#tabButtonActive` - 活跃标签按钮
- `#tabButton:hover` - 标签悬停状态
- `#columnContainer` - 列容器
- `#taskItemWidget` - 任务项
- 等等

## 对标现代化 UI 框架

虽然 PyQt5 无法直接使用 shadcn/ui 和 Framer Motion（React 库），但本设计实现了类似的效果：

| shadcn/ui 特性 | PyQt5 实现 |
|----------------|----------|
| 标签导航组件 | TabBar（自定义 QWidget）|
| 状态管理 | PyQt5 信号/槽机制 |
| 条件渲染 | QStackedWidget 视图切换 |
| 响应式设计 | QLayout 自适应布局 |
| 现代配色 | QSS 现代化配色方案 |
| 交互动画 | QPropertyAnimation（可选扩展）|

## 后续优化建议

1. **动画效果**
   - 使用 QPropertyAnimation 实现标签页过渡动画
   - 任务列表加载动画

2. **快捷键**
   - Ctrl+1: 切换到 To Do
   - Ctrl+2: 切换到 In Progress
   - Ctrl+3: 切换到 Done

3. **拖拽功能**
   - 支持在不同标签间拖拽任务

4. **搜索功能**
   - 在当前视图中搜索任务

5. **过滤选项**
   - 按优先级、日期等过滤任务

## 测试验证

运行测试脚本验证功能：
```bash
python test_ui.py
```

预期输出：
- ✓ To Do: 1
- ✓ In Progress: 1
- ✓ Done: 1

## 常见问题

**Q: 为什么样式表显示 "Unknown property" 警告？**
A: PyQt5 QSS 不支持某些 CSS 属性（如 transition、transform）。这些警告是非致命的，应用功能正常。

**Q: 如何在标签间快速切换？**
A: 点击顶部标签栏的按钮即可。每个标签都是独立的按钮，点击会立即切换视图。

**Q: 任务是否会在切换标签时丢失？**
A: 不会。所有任务都存储在 SQLite 数据库中，切换标签只是改变显示的视图，任务数据不变。
