"""
任务输入框组件
"""
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLineEdit, QPushButton, QMenu
from PyQt5.QtCore import pyqtSignal, Qt
import config


class TaskInputWidget(QWidget):
    """任务输入框组件"""
    
    # 信号：当用户提交新任务时 (title, task_type)
    task_added = pyqtSignal(str, str)
    
    def __init__(self):
        super().__init__()
        self.current_type = "daily"  # 默认每日任务
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
        
        # 右侧预留药丸按钮的位置 (48 像素)
        self.input_field.setTextMargins(0, 0, 48, 0)
        
        # 类型切换按钮 (放置在输入框内部)
        self.type_button = QPushButton()
        self.type_button.setObjectName("taskTypeBtn")
        self.type_button.setCursor(Qt.PointingHandCursor)
        
        # 类型选择菜单
        self.type_menu = QMenu(self)
        self.type_menu.setObjectName("taskTypeMenu")
        self.daily_action = self.type_menu.addAction("")
        self.one_time_action = self.type_menu.addAction("")
        self.daily_action.triggered.connect(lambda: self.set_task_type("daily"))
        self.one_time_action.triggered.connect(lambda: self.set_task_type("one_time"))
        self.type_button.setMenu(self.type_menu)
        
        # 将按钮以局部的 QHBoxLayout 放入 QLineEdit 内部
        input_layout = QHBoxLayout(self.input_field)
        input_layout.setContentsMargins(0, 0, 6, 0)
        input_layout.addStretch()
        input_layout.addWidget(self.type_button)
        
        # 添加按钮
        self.add_button = QPushButton("Add")
        self.add_button.setObjectName("addBtn")
        self.add_button.setCursor(Qt.PointingHandCursor)
        self.add_button.clicked.connect(self.on_add_task)
        
        layout.addWidget(self.input_field, 1)
        layout.addWidget(self.add_button)
        
        self.setLayout(layout)
        
        # 初始化文本和菜单内容
        self.retranslate_ui("输入新任务...", "Add")
    
    def set_task_type(self, task_type: str):
        """设置当前任务类型"""
        self.current_type = task_type
        self.update_type_button_text()
        
    def update_type_button_text(self):
        """更新类型切换按钮文字（仅显示圆圈 + 三角形）"""
        if self.current_type == "daily":
            self.type_button.setText("🟢 ▼")
        else:
            self.type_button.setText("🔵 ▼")
    
    def on_add_task(self):
        """处理添加任务"""
        text = self.input_field.text().strip()
        if text:
            self.task_added.emit(text, self.current_type)
            self.input_field.clear()
            self.input_field.setFocus()
            
    def retranslate_ui(self, placeholder: str, add_btn_text: str):
        """动态翻译输入控件文本"""
        self.input_field.setPlaceholderText(placeholder)
        self.add_button.setText(add_btn_text)
        
        # 翻译下拉选项与按钮
        t = config.TRANSLATIONS[config.CURRENT_LANGUAGE]
        self.daily_action.setText(t.get("task_type_daily", "🟢 每日任务"))
        self.one_time_action.setText(t.get("task_type_one_time", "🔵 一次性任务"))
        self.update_type_button_text()

