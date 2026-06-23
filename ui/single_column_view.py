"""
单列视图组件 - 用于标签页显示
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QListWidget, QListWidgetItem
)
from PyQt5.QtCore import pyqtSignal, Qt
import config
from models.task import Task
from ui.kanban_board import TaskItemWidget


class SingleColumnView(QWidget):
    """单列任务视图"""
    
    status_changed = pyqtSignal(int, str)  # (task_id, new_status)
    deleted = pyqtSignal(int)  # (task_id)
    title_changed = pyqtSignal(int, str)  # (task_id, new_title)
    type_changed = pyqtSignal(int, str)  # (task_id, new_type)
    
    def __init__(self, status: str):
        super().__init__()
        self.status = status
        self.tasks = {}  # {task_id: Task}
        self.item_widgets = {}  # {task_id: TaskItemWidget}
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        
        # 任务列表
        self.list_widget = QListWidget()
        self.list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.list_widget.setStyleSheet("""
            QListWidget {
                border: none;
                background-color: transparent;
            }
        """)
        
        layout.addWidget(self.list_widget, 1)
        self.setLayout(layout)
    
    def add_task(self, task: Task):
        """添加任务"""
        if task.task_id in self.tasks:
            return
        
        self.tasks[task.task_id] = task
        
        # 创建任务项
        item_widget = TaskItemWidget(task)
        item_widget.status_changed.connect(self.on_task_status_changed)
        item_widget.deleted.connect(self.on_task_deleted)
        item_widget.title_changed.connect(self.on_task_title_changed)
        item_widget.type_changed.connect(self.on_task_type_changed)
        
        self.item_widgets[task.task_id] = item_widget
        
        # 添加到列表
        list_item = QListWidgetItem()
        item_widget.list_item = list_item
        list_item.setSizeHint(item_widget.sizeHint())
        self.list_widget.addItem(list_item)
        self.list_widget.setItemWidget(list_item, item_widget)
    
    def remove_task(self, task_id: int):
        """移除任务"""
        if task_id not in self.tasks:
            return
        
        del self.tasks[task_id]
        
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
    
    def refresh(self, tasks: list):
        """刷新任务列表"""
        self.clear()
        for task in tasks:
            if task.status == self.status:
                self.add_task(task)
    
    def on_task_status_changed(self, task_id: int, new_status: str):
        """处理任务状态改变"""
        self.status_changed.emit(task_id, new_status)
    
    def on_task_deleted(self, task_id: int):
        """处理任务删除"""
        self.deleted.emit(task_id)
        
    def on_task_title_changed(self, task_id: int, new_title: str):
        """处理任务标题改变"""
        self.title_changed.emit(task_id, new_title)
        
    def on_task_type_changed(self, task_id: int, new_type: str):
        """处理任务类型改变"""
        self.type_changed.emit(task_id, new_type)
