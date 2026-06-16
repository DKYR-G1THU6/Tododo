from PyQt5.QtWidgets import QWidget, QHBoxLayout, QPushButton
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QVariantAnimation, QEasingCurve
from PyQt5.QtGui import QFont, QColor


class TabBar(QWidget):
    """现代化标签栏组件"""
    
    # 信号：当标签被点击时
    tab_changed = pyqtSignal(str)  # 发出被点击的标签ID
    
    def __init__(self, tabs: dict):
        """
        初始化标签栏
        
        Args:
            tabs: {tab_id: tab_label} 字典
            例如: {"todo": "To Do", "in_progress": "In Progress", "done": "Done"}
        """
        super().__init__()
        self.tabs = tabs
        self.active_tab = list(tabs.keys())[0]  # 默认第一个标签为active
        self.tab_buttons = {}
        
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        for tab_id, tab_label in self.tabs.items():
            btn = QPushButton(tab_label)
            btn.setObjectName("tabButton")
            btn.setCheckable(True)
            btn.setMinimumHeight(40)
            btn.setMinimumWidth(80)
            btn.setFont(QFont("Segoe UI", 10, QFont.Bold))
            
            # 设置第一个按钮为选中状态
            if tab_id == self.active_tab:
                btn.setChecked(True)
                btn.setObjectName("tabButtonActive")
            
            btn.clicked.connect(lambda checked, tid=tab_id: self.on_tab_clicked(tid))
            self.tab_buttons[tab_id] = btn
            layout.addWidget(btn, 1)
        
        self.setLayout(layout)
        self.setMinimumHeight(44)
        self.setMaximumHeight(44)
    
    def on_tab_clicked(self, tab_id: str):
        """处理标签点击"""
        if tab_id == self.active_tab:
            return
        
        # 取消之前选中的按钮
        self.tab_buttons[self.active_tab].setChecked(False)
        self.tab_buttons[self.active_tab].setObjectName("tabButton")
        self.tab_buttons[self.active_tab].style().unpolish(self.tab_buttons[self.active_tab])
        self.tab_buttons[self.active_tab].style().polish(self.tab_buttons[self.active_tab])
        
        # 设置新的选中按钮
        self.active_tab = tab_id
        self.tab_buttons[tab_id].setChecked(True)
        self.tab_buttons[tab_id].setObjectName("tabButtonActive")
        self.tab_buttons[tab_id].style().unpolish(self.tab_buttons[tab_id])
        self.tab_buttons[tab_id].style().polish(self.tab_buttons[tab_id])
        
        # 发出信号
        self.tab_changed.emit(tab_id)
    
    def get_active_tab(self) -> str:
        """获取当前选中的标签"""
        return self.active_tab

    def flash_tab(self, tab_id: str):
        """让指定的标签按钮以呼吸灯形式（慢进慢出）闪烁一次以示感知"""
        btn = self.tab_buttons.get(tab_id)
        if not btn or tab_id == self.active_tab:
            return
            
        # 如果已经有动画在运行，先停止它
        if hasattr(btn, "flash_anim") and btn.flash_anim:
            btn.flash_anim.stop()
            
        # 建立数值插值动画：0.0 -> 1.0 (最深) -> 0.0
        anim = QVariantAnimation(btn)
        anim.setStartValue(0.0)
        anim.setKeyValueAt(0.5, 1.0)
        anim.setEndValue(0.0)
        anim.setDuration(1000)  # 1.0秒的呼吸效果
        anim.setEasingCurve(QEasingCurve.InOutQuad)  # 慢进慢出插值曲线
        
        # 定义起止颜色
        c_bg_start = QColor("#ffffff")
        c_bg_end = QColor("#a7f3d0")  # 翡翠绿底色
        c_text_start = QColor("#64748b")  # 默认文字颜色
        c_text_end = QColor("#047857")    # 深绿文字颜色
        
        def interpolate_color(c1, c2, factor):
            r = int(c1.red() + (c2.red() - c1.red()) * factor)
            g = int(c1.green() + (c2.green() - c1.green()) * factor)
            b = int(c1.blue() + (c2.blue() - c1.blue()) * factor)
            return QColor(r, g, b)
            
        def update_style(factor):
            bg = interpolate_color(c_bg_start, c_bg_end, factor)
            txt = interpolate_color(c_text_start, c_text_end, factor)
            btn.setStyleSheet(f"background-color: {bg.name()}; color: {txt.name()}; border-bottom: 3.5px solid transparent;")
            
        anim.valueChanged.connect(update_style)
        
        def on_finished():
            btn.setStyleSheet("")  # 清除样式重置，还原全局 QSS
            btn.flash_anim = None
            
        anim.finished.connect(on_finished)
        btn.flash_anim = anim
        anim.start()
        
    def retranslate_ui(self, titles: dict):
        """动态翻译标签文本"""
        for tab_id, text in titles.items():
            btn = self.tab_buttons.get(tab_id)
            if btn:
                btn.setText(text)
