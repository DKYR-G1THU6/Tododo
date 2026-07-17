"""
MiniBar — 迷你模式浮动条
当主窗口收缩到迷你模式时，显示标题、放大按钮和退出按钮。
"""
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import Qt, pyqtSignal, QPoint
from PyQt5.QtGui import QFont


class MiniBar(QWidget):
    """迷你模式浮动条（内嵌在 MainWindow 中作为唯一可见内容）"""

    restore_clicked = pyqtSignal()   # 点击放大按钮
    close_clicked = pyqtSignal()     # 点击退出按钮

    def __init__(self, parent=None):
        super().__init__(parent)
        self._drag_start_pos: QPoint | None = None
        self.init_ui()

    def init_ui(self):
        """初始化 UI"""
        self.setObjectName("miniBarContainer")
        self.setAttribute(Qt.WA_StyledBackground, True)

        layout = QHBoxLayout()
        layout.setContentsMargins(10, 0, 6, 0)
        layout.setSpacing(4)

        # 标题标签（占用剩余空间，同时作为拖动区域）
        self.title_label = QLabel("Tododo")
        self.title_label.setObjectName("miniTitleLabel")
        font = QFont()
        font.setPointSize(10)
        font.setBold(True)
        self.title_label.setFont(font)
        self.title_label.setCursor(Qt.SizeAllCursor)  # 提示可拖动

        # 放大按钮
        self.restore_btn = QPushButton("⬜")
        self.restore_btn.setObjectName("miniRestoreBtn")
        self.restore_btn.setToolTip("恢复窗口 / Restore window")
        self.restore_btn.setCursor(Qt.PointingHandCursor)
        self.restore_btn.clicked.connect(self.restore_clicked.emit)

        # 退出按钮
        self.close_btn = QPushButton("×")
        self.close_btn.setObjectName("miniCloseBtn")
        self.close_btn.setToolTip("退出 / Quit")
        self.close_btn.setCursor(Qt.PointingHandCursor)
        self.close_btn.clicked.connect(self.close_clicked.emit)

        layout.addWidget(self.title_label, 1)
        layout.addWidget(self.restore_btn)
        layout.addWidget(self.close_btn)

        self.setLayout(layout)

    def set_title(self, title: str):
        """更新标题文字"""
        self.title_label.setText(title)

    # ──────────────────────────────────────────
    # 拖动支持（标题区域 → 拖动整个父窗口）
    # ──────────────────────────────────────────

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # 只有点在标题标签上才启动拖动
            if self.title_label.geometry().contains(event.pos()):
                self._drag_start_pos = event.globalPos() - self.window().frameGeometry().topLeft()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_start_pos is not None and event.buttons() & Qt.LeftButton:
            self.window().move(event.globalPos() - self._drag_start_pos)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_start_pos = None
        super().mouseReleaseEvent(event)
