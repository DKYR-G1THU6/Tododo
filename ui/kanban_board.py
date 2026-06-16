"""
Kanban 任务板组件
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QListWidget, QListWidgetItem, QCheckBox, QPushButton, QLineEdit, QPlainTextEdit
)
from PyQt5.QtCore import Qt, pyqtSignal, QEvent, QRect, QSize
from PyQt5.QtGui import QFontMetrics
import config
from models.task import Task


class TaskItemWidget(QWidget):
    """单个任务项组件"""
    
    status_changed = pyqtSignal(int, str)  # (task_id, new_status)
    deleted = pyqtSignal(int)  # (task_id)
    title_changed = pyqtSignal(int, str)  # (task_id, new_title)
    
    def __init__(self, task: Task):
        super().__init__()
        self.task = task
        self.is_editing = False
        self.list_item = None  # 将由父视图关联并设置
        self.init_ui()
    
    def init_ui(self):
        """初始化任务项 UI"""
        self.setObjectName("taskItemWidget")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setCursor(Qt.PointingHandCursor)  # 设置为手型光标暗示可点击
        
        layout = QHBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        
        # 任务标题
        self.title_label = QLabel(self.task.title)
        self.title_label.setObjectName("taskTitleLabel")
        self.title_label.setWordWrap(True)
        
        # 编辑输入框 (换用 QPlainTextEdit 以支持自动换行)
        self.edit_input = QPlainTextEdit()
        self.edit_input.setPlainText(self.task.title)
        self.edit_input.setObjectName("taskEditInput")
        self.edit_input.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.edit_input.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.edit_input.setLineWrapMode(QPlainTextEdit.WidgetWidth)
        self.edit_input.hide()
        self.edit_input.textChanged.connect(self.on_edit_text_changed)
        self.edit_input.installEventFilter(self)
        
        # 编辑按钮 (🖊)
        self.edit_btn = QPushButton("🖊")
        self.edit_btn.setObjectName("editBtn")
        self.edit_btn.setFixedSize(24, 24)
        self.edit_btn.setToolTip("修改任务")
        self.edit_btn.clicked.connect(self.on_start_edit)
        
        # 确认保存按钮 (✓)
        self.save_btn = QPushButton("✓")
        self.save_btn.setObjectName("saveBtn")
        self.save_btn.setFixedSize(24, 24)
        self.save_btn.setToolTip("保存")
        self.save_btn.hide()
        self.save_btn.clicked.connect(self.on_save_edit)
        
        # 删除按钮
        self.delete_btn = QPushButton("×")
        self.delete_btn.setObjectName("deleteBtn")
        self.delete_btn.setFixedSize(24, 24)
        self.delete_btn.setToolTip("删除任务")
        self.delete_btn.clicked.connect(self.on_delete)
        
        # 取消编辑按钮 (×)
        self.cancel_btn = QPushButton("×")
        self.cancel_btn.setObjectName("cancelBtn")
        self.cancel_btn.setFixedSize(24, 24)
        self.cancel_btn.setToolTip("取消")
        self.cancel_btn.hide()
        self.cancel_btn.clicked.connect(self.on_cancel_edit)
        
        layout.addWidget(self.title_label, 1)
        layout.addWidget(self.edit_input, 1)
        layout.addWidget(self.edit_btn)
        layout.addWidget(self.save_btn)
        layout.addWidget(self.delete_btn)
        layout.addWidget(self.cancel_btn)
        
        self.setLayout(layout)
    
    def mousePressEvent(self, event):
        """点击卡片本身触发状态流转"""
        if self.is_editing:
            super().mousePressEvent(event)
            return
            
        if event.button() == Qt.LeftButton:
            if self.task.status == config.TASK_STATUS_TODO:
                self.status_changed.emit(self.task.task_id, config.TASK_STATUS_IN_PROGRESS)
            elif self.task.status == config.TASK_STATUS_IN_PROGRESS:
                self.status_changed.emit(self.task.task_id, config.TASK_STATUS_DONE)
            super().mousePressEvent(event)
    
    def on_start_edit(self):
        """开始编辑"""
        self.is_editing = True
        self.title_label.hide()
        self.edit_btn.hide()
        self.delete_btn.hide()
        
        self.edit_input.setPlainText(self.task.title)
        self.edit_input.show()
        self.save_btn.show()
        self.cancel_btn.show()
        
        self.edit_input.setFocus()
        # 选中所有文本
        text_cursor = self.edit_input.textCursor()
        text_cursor.select(text_cursor.Document)
        self.edit_input.setTextCursor(text_cursor)
        
        self.update_item_height()
        
    def on_cancel_edit(self):
        """取消编辑"""
        self.is_editing = False
        self.edit_input.hide()
        self.save_btn.hide()
        self.cancel_btn.hide()
        
        self.title_label.show()
        self.edit_btn.show()
        self.delete_btn.show()
        self.update_item_height()
        
    def on_save_edit(self):
        """保存编辑内容"""
        new_title = self.edit_input.toPlainText().strip()
        if new_title and new_title != self.task.title:
            self.title_changed.emit(self.task.task_id, new_title)
        else:
            self.on_cancel_edit()
            
    def on_delete(self):
        """处理删除按钮"""
        self.deleted.emit(self.task.task_id)
        
    def on_edit_text_changed(self):
        """当编辑框内容改变时，动态调整高度"""
        self.update_item_height()
        
    def eventFilter(self, obj, event):
        if obj is self.edit_input and event.type() == QEvent.KeyPress:
            if event.key() in (Qt.Key_Return, Qt.Key_Enter):
                # 如果同时按下了 Shift 键，则换行，否则保存修改
                if event.modifiers() & Qt.ShiftModifier:
                    return False
                self.on_save_edit()
                return True
            elif event.key() == Qt.Key_Escape:
                self.on_cancel_edit()
                return True
        return super().eventFilter(obj, event)

    def sizeHint(self):
        # 根据当前宽度和文本计算高度
        width = self.width()
        # 如果宽度尚未分配（为0）或使用了默认的640宽，则使用适应视窗大小的默认宽（如310）
        if width <= 0 or width > 340:
            width = 310
            
        if self.is_editing:
            font = self.edit_input.font()
            metrics = QFontMetrics(font)
            label_width = width - 84
            if label_width < 50:
                label_width = 50
            # 减去 QPlainTextEdit 内部左右 padding
            text_width = label_width - 12
            rect = metrics.boundingRect(
                QRect(0, 0, text_width, 9999),
                Qt.TextWordWrap,
                self.edit_input.toPlainText()
            )
            # 行内输入框留出舒适的上下 margin
            height = max(50, rect.height() + 28)
        else:
            font = self.title_label.font()
            metrics = QFontMetrics(font)
            label_width = width - 84
            if label_width < 50:
                label_width = 50
            rect = metrics.boundingRect(
                QRect(0, 0, label_width, 9999),
                Qt.TextWordWrap,
                self.task.title
            )
            label_height = rect.height()
            height = max(44, label_height + 20)
        return QSize(width, height)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_item_height()
        
    def update_item_height(self):
        if self.list_item:
            width = self.width()
            if width <= 0 or width > 340:
                width = 310
                
            if self.is_editing:
                font = self.edit_input.font()
                metrics = QFontMetrics(font)
                label_width = width - 84
                if label_width < 50:
                    label_width = 50
                text_width = label_width - 12
                rect = metrics.boundingRect(
                    QRect(0, 0, text_width, 9999),
                    Qt.TextWordWrap,
                    self.edit_input.toPlainText()
                )
                height = max(50, rect.height() + 28)
            else:
                font = self.title_label.font()
                metrics = QFontMetrics(font)
                label_width = width - 84
                if label_width < 50:
                    label_width = 50
                rect = metrics.boundingRect(
                    QRect(0, 0, label_width, 9999),
                    Qt.TextWordWrap,
                    self.task.title
                )
                label_height = rect.height()
                height = max(44, label_height + 20)
            
            current_hint = self.list_item.sizeHint()
            if current_hint.height() != height or current_hint.width() != width:
                self.list_item.setSizeHint(QSize(width, height))


class TaskColumn(QWidget):
    """Kanban 列"""
    
    status_changed = pyqtSignal(int, str)  # (task_id, new_status)
    deleted = pyqtSignal(int)  # (task_id)
    title_changed = pyqtSignal(int, str)  # (task_id, new_title)
    
    def __init__(self, status: str):
        super().__init__()
        self.status = status
        self.tasks = {}  # {task_id: Task}
        self.item_widgets = {}  # {task_id: TaskItemWidget}
        self.init_ui()
    
    def init_ui(self):
        """初始化列 UI"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 列标题
        title_label = QLabel(config.COLUMN_TITLES[self.status])
        title_label.setObjectName("columnTitle")
        title_label.setFixedHeight(32)
        
        # 任务列表
        self.list_widget = QListWidget()
        self.list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.list_widget.setMinimumHeight(200)
        
        layout.addWidget(title_label)
        layout.addWidget(self.list_widget, 1)
        
        self.setLayout(layout)
    
    def add_task(self, task: Task):
        """添加任务到列"""
        if task.task_id in self.tasks:
            return
        
        self.tasks[task.task_id] = task
        
        # 创建任务项 widget
        item_widget = TaskItemWidget(task)
        item_widget.status_changed.connect(self.on_task_status_changed)
        item_widget.deleted.connect(self.on_task_deleted)
        item_widget.title_changed.connect(self.on_task_title_changed)
        
        self.item_widgets[task.task_id] = item_widget
        
        # 添加到列表
        list_item = QListWidgetItem()
        item_widget.list_item = list_item
        list_item.setSizeHint(item_widget.sizeHint())
        self.list_widget.addItem(list_item)
        self.list_widget.setItemWidget(list_item, item_widget)
    
    def remove_task(self, task_id: int):
        """从列移除任务"""
        if task_id not in self.tasks:
            return
        
        del self.tasks[task_id]
        
        # 从列表移除
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            widget = self.list_widget.itemWidget(item)
            if widget is self.item_widgets[task_id]:
                self.list_widget.takeItem(i)
                break
        
        del self.item_widgets[task_id]
    
    def clear(self):
        """清空所有任务"""
        self.tasks.clear()
        self.item_widgets.clear()
        self.list_widget.clear()
    
    def on_task_status_changed(self, task_id: int, new_status: str):
        """处理任务状态改变"""
        self.status_changed.emit(task_id, new_status)
    
    def on_task_deleted(self, task_id: int):
        """处理任务删除"""
        self.deleted.emit(task_id)
        
    def on_task_title_changed(self, task_id: int, new_title: str):
        """处理任务标题改变"""
        self.title_changed.emit(task_id, new_title)
    
    def update_task(self, task: Task):
        """更新任务显示"""
        if task.task_id in self.item_widgets:
            self.item_widgets[task.task_id].task = task


class KanbanBoard(QWidget):
    """Kanban 任务板"""
    
    status_changed = pyqtSignal(int, str)  # (task_id, new_status)
    deleted = pyqtSignal(int)  # (task_id)
    title_changed = pyqtSignal(int, str)  # (task_id, new_title)
    
    def __init__(self):
        super().__init__()
        self.columns = {}  # {status: TaskColumn}
        self.init_ui()
    
    def init_ui(self):
        """初始化 Kanban 板"""
        layout = QHBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # 创建三列
        for status in config.COLUMN_ORDER:
            column = TaskColumn(status)
            column.status_changed.connect(self.on_column_status_changed)
            column.deleted.connect(self.on_column_task_deleted)
            column.title_changed.connect(self.on_column_task_title_changed)
            
            self.columns[status] = column
            layout.addWidget(column, 1)
        
        self.setLayout(layout)
    
    def add_task(self, task: Task):
        """添加任务"""
        if task.status in self.columns:
            self.columns[task.status].add_task(task)
    
    def remove_task(self, task_id: int, status: str):
        """删除任务"""
        if status in self.columns:
            self.columns[status].remove_task(task_id)
    
    def move_task(self, task: Task, old_status: str):
        """移动任务到新列"""
        if old_status in self.columns:
            self.columns[old_status].remove_task(task.task_id)
        
        if task.status in self.columns:
            self.columns[task.status].add_task(task)
    
    def refresh(self, tasks: list):
        """刷新显示所有任务"""
        # 清空所有列
        for column in self.columns.values():
            column.clear()
        
        # 重新添加任务
        for task in tasks:
            self.add_task(task)
    
    def on_column_status_changed(self, task_id: int, new_status: str):
        """处理列中的任务状态改变"""
        self.status_changed.emit(task_id, new_status)
    
    def on_column_task_deleted(self, task_id: int):
        """处理列中的任务删除"""
        self.deleted.emit(task_id)
        
    def on_column_task_title_changed(self, task_id: int, new_title: str):
        """处理列中的任务标题改变"""
        self.title_changed.emit(task_id, new_title)
