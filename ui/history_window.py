"""
已完成的一次性任务历史记录窗口
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTableWidget, QTableWidgetItem, QHeaderView, QApplication
)
from PyQt5.QtCore import Qt, QPoint, QEvent
from PyQt5.QtGui import QFont, QIcon
from pathlib import Path

import config
from services.task_service import TaskService
from ui.styles import apply_styles


class HistoryWindow(QWidget):
    """历史记录窗口"""
    
    def __init__(self, task_service: TaskService, language: str = "zh", always_on_top: bool = True):
        super().__init__()
        self.task_service = task_service
        self.language = language
        self.always_on_top = always_on_top
        self.drag_start_pos = None
        
        self.init_ui()
        self.load_data()
        
        # 注册数据更新自动回调
        self.task_service.register_update_callback(self.load_data)
        
    def init_ui(self):
        """初始化 UI"""
        t = config.TRANSLATIONS[self.language]
        self.setWindowTitle(t["history_title"])
        self.setFixedSize(config.WINDOW_WIDTH, config.WINDOW_HEIGHT)
        
        # 窗口标志：无边框，可在任务栏显示
        flags = Qt.Window | Qt.FramelessWindowHint | Qt.WindowMinimizeButtonHint
        if self.always_on_top:
            flags |= Qt.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        
        # 窗口图标
        icon_path = Path(__file__).parent.parent / "resources" / "tododo.ico"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
            
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # 外层布局
        outer_layout = QVBoxLayout()
        outer_layout.setContentsMargins(10, 10, 10, 10)
        outer_layout.setSpacing(0)
        
        # 主容器
        container = QWidget()
        container.setObjectName("mainContainer")
        container_layout = QVBoxLayout()
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        
        # 标题栏
        self.title_bar = QWidget()
        self.title_bar.setObjectName("titleBar")
        self.title_bar.setFixedHeight(50)
        
        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(12, 0, 12, 0)
        title_layout.setSpacing(8)
        
        # 标题 Label
        self.title_label = QLabel(t["history_title"])
        self.title_label.setObjectName("titleLabel")
        font = QFont()
        font.setPointSize(11)
        font.setBold(True)
        self.title_label.setFont(font)
        
        # 刷新按钮
        self.refresh_button = QPushButton("↻")
        self.refresh_button.setObjectName("refreshBtn")
        self.refresh_button.setFixedSize(36, 36)
        self.refresh_button.setCursor(Qt.PointingHandCursor)
        self.refresh_button.clicked.connect(self.load_data)
        
        # 删除按钮
        self.delete_button = QPushButton("🗑")
        self.delete_button.setObjectName("deleteBtnHeader")
        self.delete_button.setFixedSize(36, 36)
        self.delete_button.setCursor(Qt.PointingHandCursor)
        self.delete_button.clicked.connect(self.on_delete_selected)
        
        # 关闭按钮
        self.close_button = QPushButton("×")
        self.close_button.setObjectName("closeBtn")
        self.close_button.setFixedSize(36, 36)
        self.close_button.setCursor(Qt.PointingHandCursor)
        self.close_button.clicked.connect(self.close)
        
        title_layout.addWidget(self.title_label, 1)
        title_layout.addWidget(self.refresh_button)
        title_layout.addWidget(self.delete_button)
        title_layout.addWidget(self.close_button)
        
        # 数据表格
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.MultiSelection)
        self.table.setShowGrid(False) # 扁平化设计，不显示网格线
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setHighlightSections(False)
        self.table.verticalHeader().setVisible(False) # 隐藏默认行号
        self.table.setObjectName("historyTable")
        self.table.setWordWrap(True)
        self.table.viewport().setCursor(Qt.PointingHandCursor)  # 设置单元格区域为手型光标
        
        # 调整并锁定表头大小，防止用户拖拽导致展示不全
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        self.table.setColumnWidth(0, 55)
        self.table.setColumnWidth(2, 135)
        
        self.retranslate_headers()
        
        container_layout.addWidget(self.title_bar)
        container_layout.addWidget(self.table, 1)
        container.setLayout(container_layout)
        
        outer_layout.addWidget(container)
        self.setLayout(outer_layout)
        
        apply_styles(self)
        
    def retranslate_headers(self):
        """翻译表头"""
        t = config.TRANSLATIONS[self.language]
        headers = [t["history_col_no"], t["history_col_task"], t["history_col_date"]]
        self.table.setHorizontalHeaderLabels(headers)
        self.title_label.setText(t["history_title"])
        self.setWindowTitle(t["history_title"])
        self.delete_button.setToolTip(t["delete_selected"])
        
    def load_data(self):
        """加载已完成的一次性任务"""
        tasks = self.task_service.get_completed_one_time_tasks()
        self.table.setRowCount(len(tasks))
        
        for idx, task in enumerate(tasks):
            # 序号从 1 开始
            no_item = QTableWidgetItem(str(idx + 1))
            no_item.setTextAlignment(Qt.AlignCenter)
            no_item.setData(Qt.UserRole, task.task_id)  # 绑定 task_id 供删除使用
            
            title_item = QTableWidgetItem(task.title)
            title_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            title_item.setToolTip(task.title) # 长文本悬浮显示完整内容
            
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
            
    def mousePressEvent(self, event):
        """处理鼠标按下事件（用于拖动窗口）"""
        if event.button() == Qt.LeftButton:
            if event.y() < self.title_bar.height():
                self.drag_start_pos = event.globalPos() - self.frameGeometry().topLeft()
                
    def mouseMoveEvent(self, event):
        """处理鼠标移动事件（用于拖动窗口）"""
        if self.drag_start_pos is not None:
            self.move(event.globalPos() - self.drag_start_pos)
            
    def mouseReleaseEvent(self, event):
        """处理鼠标释放事件"""
        self.drag_start_pos = None
        
    def closeEvent(self, event):
        """窗口关闭时注销回调，防止内存泄漏"""
        self.task_service.unregister_update_callback(self.load_data)
        super().closeEvent(event)
