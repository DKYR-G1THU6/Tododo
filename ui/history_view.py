"""
已完成的一次性任务历史记录视图组件
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

import config
from services.task_service import TaskService
from ui.styles import apply_styles


class HistoryView(QWidget):
    """历史记录视图子页面"""
    
    def __init__(self, task_service: TaskService, parent=None):
        super().__init__(parent)
        self.task_service = task_service
        self.language = config.CURRENT_LANGUAGE
        self.init_ui()
        self.load_data()
        
        # 注册数据库更新自动回调
        self.task_service.register_update_callback(self.load_data)
        
    def init_ui(self):
        """初始化 UI"""
        t = config.TRANSLATIONS[self.language]
        
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        
        # 1. 顶部工具栏 (显示标题 + 功能按钮)
        self.toolbar = QWidget()
        toolbar_layout = QHBoxLayout(self.toolbar)
        toolbar_layout.setContentsMargins(0, 0, 0, 0)
        toolbar_layout.setSpacing(6)
        
        # 内部标题
        self.table_title = QLabel(t["history_title"])
        self.table_title.setStyleSheet("font-weight: bold; color: #475569; font-size: 10.5pt;")
        
        # 删除按钮
        self.delete_button = QPushButton("🗑")
        self.delete_button.setObjectName("deleteBtnHeader")
        self.delete_button.setFixedSize(32, 32)
        self.delete_button.setCursor(Qt.PointingHandCursor)
        self.delete_button.clicked.connect(self.on_delete_selected)
        
        # 刷新按钮
        self.refresh_button = QPushButton("↻")
        self.refresh_button.setObjectName("refreshBtn")
        self.refresh_button.setFixedSize(32, 32)
        self.refresh_button.setCursor(Qt.PointingHandCursor)
        self.refresh_button.clicked.connect(self.load_data)
        
        toolbar_layout.addWidget(self.table_title, 1)
        toolbar_layout.addWidget(self.delete_button)
        toolbar_layout.addWidget(self.refresh_button)
        
        # 2. 数据表格
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.MultiSelection)
        self.table.setShowGrid(False) # 扁平化，不显示网格线
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setHighlightSections(False)
        self.table.verticalHeader().setVisible(False) # 隐藏默认行号
        self.table.setObjectName("historyTable")
        self.table.setWordWrap(True)
        self.table.viewport().setCursor(Qt.PointingHandCursor)
        
        # 调整列宽以适应较窄的主窗口
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        self.table.setColumnWidth(0, 40)  # 序号列
        self.table.setColumnWidth(2, 110) # 日期列
        
        self.retranslate_headers()
        
        layout.addWidget(self.toolbar)
        layout.addWidget(self.table, 1)
        self.setLayout(layout)
        
        apply_styles(self)
        
    def retranslate_headers(self):
        """翻译表头"""
        t = config.TRANSLATIONS[self.language]
        headers = [t["history_col_no"], t["history_col_task"], t["history_col_date"]]
        self.table.setHorizontalHeaderLabels(headers)
        self.table_title.setText(t["history_title"])
        self.delete_button.setToolTip(t["delete_selected"])
        self.refresh_button.setToolTip("手动刷新 / Refresh")
        
    def load_data(self):
        """加载已完成的一次性任务数据"""
        tasks = self.task_service.get_completed_one_time_tasks()
        self.table.setRowCount(len(tasks))
        
        for idx, task in enumerate(tasks):
            # 序号从 1 开始
            no_item = QTableWidgetItem(str(idx + 1))
            no_item.setTextAlignment(Qt.AlignCenter)
            no_item.setData(Qt.UserRole, task.task_id)  # 绑定 task_id 供删除
            
            title_item = QTableWidgetItem(task.title)
            title_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            title_item.setToolTip(task.title)
            
            date_item = QTableWidgetItem(task.completed_date or task.created_date)
            date_item.setTextAlignment(Qt.AlignCenter)
            
            self.table.setItem(idx, 0, no_item)
            self.table.setItem(idx, 1, title_item)
            self.table.setItem(idx, 2, date_item)
            
        self.table.resizeRowsToContents()
        
    def on_delete_selected(self):
        """删除选中的任务"""
        selected_ranges = self.table.selectedRanges()
        if not selected_ranges:
            return
            
        # 收集所有选中的行号
        selected_rows = set()
        for r_range in selected_ranges:
            for r in range(r_range.topRow(), r_range.bottomRow() + 1):
                selected_rows.add(r)
                
        if not selected_rows:
            return
            
        task_ids_to_delete = []
        for row in selected_rows:
            item = self.table.item(row, 0)
            if item:
                task_id = item.data(Qt.UserRole)
                if task_id:
                    task_ids_to_delete.append(task_id)
                    
        if not task_ids_to_delete:
            return
            
        # 临时注销回调，避免循环删除时重复触发刷新
        self.task_service.unregister_update_callback(self.load_data)
        
        for task_id in task_ids_to_delete:
            self.task_service.delete_task(task_id)
            
        # 重新注册并刷新
        self.task_service.register_update_callback(self.load_data)
        self.load_data()
        
    def set_language(self, lang: str):
        """主窗口切换语言时同步本视图语言"""
        self.language = lang
        self.retranslate_headers()
        self.load_data()
