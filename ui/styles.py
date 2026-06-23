"""
QSS 样式表 - 现代化极简浅色 (Light) 主题
与用户设计的 Legal AI Assistant 风格保持一致：白底、细腻灰线、亮绿（Emerald）点缀。
将任务列表改写为带有精致下分隔线的极简列表布局。
"""

STYLESHEET = """
* {
    margin: 0;
    padding: 0;
}

QWidget {
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, 'Microsoft YaHei', sans-serif;
    font-size: 10pt;
    color: #1e293b; /* slate-800 */
}

/* 主容器：圆角边框，极简白底，带微弱阴影质感 */
#mainContainer {
    background-color: #ffffff;
    border-radius: 12px;
    border: 1px solid #e2e8f0; /* slate-200 */
}

/* ===== 标题栏 ===== */
#titleBar {
    background-color: #ffffff;
    border-top-left-radius: 12px;
    border-top-right-radius: 12px;
    border-bottom: 1px solid #f1f5f9; /* slate-100 */
}

QLabel#titleLabel {
    font-size: 11pt;
    font-weight: bold;
    color: #0f172a; /* slate-900 */
    padding-left: 4px;
    background-color: transparent;
}

/* ===== 标题修改输入框与确认按钮 ===== */
QLineEdit#titleEditField {
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 2px 6px;
    background-color: #f8fafc;
    color: #0f172a;
    font-size: 10pt;
}

QLineEdit#titleEditField:focus {
    border: 1.5px solid #6366f1;
    background-color: #ffffff;
    outline: none;
}

QPushButton#titleConfirmBtn {
    background-color: #6366f1; /* 蓝色确认按钮 */
    color: white;
    border: none;
    border-radius: 6px;
    font-weight: bold;
    font-size: 11pt;
    padding: 0px;
}

QPushButton#titleConfirmBtn:hover {
    background-color: #4f46e5;
}

QPushButton#titleConfirmBtn:pressed {
    background-color: #3730a3;
}

/* ===== 标题栏控制按钮 ===== */
QPushButton#menuButton, QPushButton#minimizeBtn, QPushButton#closeBtn, QPushButton#refreshBtn, QPushButton#deleteBtnHeader {
    border: none;
    border-radius: 6px;
    padding: 0px;
    font-weight: bold;
    font-size: 11pt;
}

QPushButton#menuButton {
    background-color: transparent;
    color: #64748b; /* slate-500 */
    border: 1px solid #e2e8f0;
}

QPushButton#menuButton:hover {
    background-color: #f8fafc;
    border-color: #cbd5e1;
    color: #0f172a;
}

QPushButton#minimizeBtn {
    background-color: transparent;
    color: #64748b;
}

QPushButton#minimizeBtn:hover {
    background-color: #f1f5f9;
    color: #0f172a;
}

QPushButton#closeBtn {
    background-color: transparent;
    color: #64748b;
}

QPushButton#closeBtn:hover {
    background-color: #fee2e2; /* red-50 */
    color: #ef4444; /* red-500 */
}

QPushButton#refreshBtn {
    background-color: transparent;
    color: #64748b;
    font-size: 14pt;
}

QPushButton#refreshBtn:hover {
    background-color: #f1f5f9;
    color: #0f172a;
}

QPushButton#deleteBtnHeader {
    background-color: transparent;
    color: #64748b;
    font-size: 12pt;
}

QPushButton#deleteBtnHeader:hover {
    background-color: #fee2e2; /* red-50 background for delete hover */
    color: #ef4444; /* red-500 text for delete hover */
}

/* ===== 标签页导航栏 ===== */
#tabButton {
    background-color: #ffffff;
    color: #64748b;
    border: none;
    border-bottom: 3.5px solid transparent;
    font-weight: bold;
    font-size: 10pt;
    padding: 6px 4px;
}

#tabButton:hover {
    background-color: #f8fafc;
    color: #0f172a;
}

#tabButtonActive {
    background-color: #ffffff;
    color: #059669; /* emerald-600 */
    border: none;
    border-bottom: 3.5px solid #10b981; /* emerald-500 */
    font-weight: bold;
    font-size: 10pt;
    padding: 6px 4px;
}

/* ===== 任务列表视图区域 ===== */
QListWidget {
    border: none;
    background-color: #f8fafc; /* slate-50 列表微灰底色，与白色卡片区分 */
    outline: none;
}

QListWidget::item {
    padding: 0px;
    margin: 0px;
    background-color: transparent;
}

QListWidget::item:selected {
    background-color: transparent;
    outline: none;
}

QListWidget::item:hover {
    background-color: transparent;
}

/* ===== 任务列表单项 (列表底线风格) ===== */
#taskItemWidget {
    background-color: #ffffff;
    border-bottom: 1px solid #e2e8f0; /* 任务与任务之间浅浅的灰色分隔线 */
    padding: 12px 14px;
    margin: 0px;
}

#taskItemWidget:hover {
    background-color: #f0fdf4; /* emerald-50 */
    border-bottom: 1px solid #cbd5e1;
}

#taskTitleLabel {
    color: #1e293b; /* slate-800 */
    font-size: 10pt;
    line-height: 1.4;
    background-color: transparent;
}

/* ===== 列表内按钮 (删除、编辑、保存、取消) ===== */
QPushButton#deleteBtn, QPushButton#editBtn, QPushButton#saveBtn, QPushButton#cancelBtn {
    background-color: transparent;
    border: none;
    border-radius: 4px;
    padding: 0px;
    min-width: 24px;
    max-width: 24px;
    min-height: 24px;
    max-height: 24px;
}

QPushButton#deleteBtn {
    color: #94a3b8;
    font-size: 11pt;
}

QPushButton#deleteBtn:hover {
    background-color: #fee2e2;
    color: #ef4444;
}

QPushButton#editBtn {
    color: #94a3b8;
    font-size: 10pt;
}

QPushButton#editBtn:hover {
    background-color: #f1f5f9;
    color: #475569;
}

QPushButton#saveBtn {
    color: #10b981;
    font-size: 11pt;
    font-weight: bold;
}

QPushButton#saveBtn:hover {
    background-color: #f0fdf4;
    color: #059669;
}

QPushButton#cancelBtn {
    color: #94a3b8;
    font-size: 11pt;
}

QPushButton#cancelBtn:hover {
    background-color: #fee2e2;
    color: #ef4444;
}

/* ===== 任务修改输入框 ===== */
#taskEditInput {
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 4px 6px;
    background-color: #f8fafc;
    color: #0f172a;
    font-size: 10pt;
}

#taskEditInput:focus {
    border: 1.5px solid #10b981;
    background-color: #ffffff;
    outline: none;
}

/* ===== 底部任务输入区域 ===== */
#taskInput {
    background-color: #ffffff;
    border-top: 1px solid #f1f5f9;
    border-bottom-left-radius: 12px;
    border-bottom-right-radius: 12px;
}

QLineEdit {
    border: 1px solid #cbd5e1; /* slate-300 */
    border-radius: 8px;
    padding: 8px 12px;
    background-color: #f8fafc; /* slate-50 */
    color: #0f172a;
    font-size: 10pt;
    selection-background-color: #a7f3d0; /* emerald-200 */
    selection-color: #047857;
}

QLineEdit:focus {
    border: 1.5px solid #10b981; /* focus emerald border */
    background-color: #ffffff;
    outline: none;
}

QLineEdit::placeholder {
    color: #94a3b8;
}

QPushButton#addBtn {
    background-color: #10b981; /* emerald-500 */
    color: white;
    border: none;
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: bold;
    font-size: 10pt;
    min-height: 32px;
}

QPushButton#addBtn:hover {
    background-color: #059669; /* emerald-600 */
}

QPushButton#addBtn:pressed {
    background-color: #047857; /* emerald-700 */
}

/* ===== 上下文菜单 ===== */
QMenu {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 4px;
}

QMenu::item {
    color: #334155;
    padding: 6px 20px;
    border-radius: 4px;
}

QMenu::item:selected {
    background-color: #f0fdf4; /* emerald-50 */
    color: #059669; /* emerald-600 */
}

QMenu::separator {
    height: 1px;
    background-color: #e2e8f0;
    margin: 4px 0px;
}

/* ===== 滚动条 ===== */
QScrollBar:vertical {
    border: none;
    background: transparent;
    width: 6px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background: #cbd5e1; /* slate-300 */
    border-radius: 3px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background: #94a3b8; /* slate-400 */
}

QScrollBar::sub-line:vertical, QScrollBar::add-line:vertical {
    border: none;
    background: none;
    height: 0px;
}

QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical {
    border: none;
    background: none;
}

/* ===== 任务类型下拉按钮 ===== */
QPushButton#taskTypeBtn {
    background-color: #f1f5f9;
    color: #475569;
    border: none;
    border-radius: 6px;
    padding: 2px 8px;
    font-size: 8.5pt;
    font-weight: bold;
    min-height: 22px;
    max-height: 22px;
}

QPushButton#taskTypeBtn:hover {
    background-color: #e2e8f0;
    color: #0f172a;
}

QPushButton#taskTypeBtn::menu-indicator {
    image: none;
}

/* ===== 历史记录表格 ===== */
QTableWidget#historyTable {
    background-color: #ffffff;
    border: none;
    gridline-color: #f1f5f9;
    outline: none;
    border-bottom-left-radius: 11px;
    border-bottom-right-radius: 11px;
}

QTableWidget::item {
    padding: 10px 12px;
    border-bottom: 1px solid #f1f5f9;
    color: #334155;
}

QTableWidget::item:selected {
    background-color: #f0fdf4;
    color: #059669;
}

QHeaderView::section {
    background-color: #f8fafc;
    color: #475569;
    padding: 8px 12px;
    font-weight: bold;
    border: none;
    border-bottom: 2px solid #e2e8f0;
}

/* ===== 标签栏内部排序按钮 ===== */
QPushButton#tabSortBtn {
    background-color: transparent;
    color: #64748b; /* slate-500 */
    border: none;
    font-size: 13pt;
    font-weight: bold;
    padding: 0px;
    min-width: 44px;
    max-width: 44px;
    min-height: 44px;
    max-height: 44px;
}

QPushButton#tabSortBtn:hover {
    background-color: #f8fafc;
    color: #0f172a;
}

QPushButton#tabSortBtnActive {
    background-color: transparent;
    color: #10b981; /* emerald-500 */
    border: none;
    font-size: 13pt;
    font-weight: bold;
    padding: 0px;
    min-width: 44px;
    max-width: 44px;
    min-height: 44px;
    max-height: 44px;
}

QPushButton#tabSortBtnActive:hover {
    background-color: #f0fdf4;
    color: #059669;
}
"""


def apply_styles(widget):
    """应用样式表到 widget"""
    widget.setStyleSheet(STYLESHEET)
