"""
任务输入框组件
"""
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLineEdit, QPushButton
from PyQt5.QtCore import pyqtSignal, Qt


class TaskInputWidget(QWidget):
    """任务输入框组件"""
    
    # 信号：当用户提交新任务时
    task_added = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        """初始化 UI"""
        self.setAttribute(Qt.WA_StyledBackground, True)
        layout = QHBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # 输入框
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("输入新任务...")
        self.input_field.returnPressed.connect(self.on_add_task)
        
        # 添加按钮
        self.add_button = QPushButton("Add")
        self.add_button.setObjectName("addBtn")
        self.add_button.clicked.connect(self.on_add_task)
        
        layout.addWidget(self.input_field, 1)
        layout.addWidget(self.add_button)
        
        self.setLayout(layout)
    
    def on_add_task(self):
        """处理添加任务"""
        text = self.input_field.text().strip()
        if text:
            self.task_added.emit(text)
            self.input_field.clear()
            self.input_field.setFocus()
            
    def retranslate_ui(self, placeholder: str, add_btn_text: str):
        """动态翻译输入控件文本"""
        self.input_field.setPlaceholderText(placeholder)
        self.add_button.setText(add_btn_text)
