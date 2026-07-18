"""
账号对话框（M5）

用途：让 PC 和手机认作同一个人。
  - 绑定邮箱：把当前匿名账号升级为正式账号（user_id 不变，本机数据全部保留）
  - 邮箱登录：在这台设备上登录另一台设备已绑定的账号（会切换身份）

所有网络调用都放在 QThread 里，避免离线时把界面卡住（超时可达 15 秒）。
"""
import logging

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFrame
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal

import config

logger = logging.getLogger(__name__)


class AuthWorker(QThread):
    """在后台线程执行一个账号相关的网络操作"""

    succeeded = pyqtSignal(object)
    failed = pyqtSignal(str)

    def __init__(self, fn, *args, parent=None):
        super().__init__(parent)
        self._fn = fn
        self._args = args

    def run(self):
        try:
            self.succeeded.emit(self._fn(*self._args))
        except Exception as e:
            self.failed.emit(str(e))


class AccountDialog(QDialog):
    """账号管理对话框"""

    # 登录到了另一个账号：主窗口需要清空本地数据并全量重新同步
    account_switched = pyqtSignal()

    def __init__(self, auth_service, parent=None):
        super().__init__(parent)
        self.auth_service = auth_service
        self._worker = None

        t = config.TRANSLATIONS[config.CURRENT_LANGUAGE]
        self.setWindowTitle(t.get("account_title", "账号 / 设备同步"))
        self.setMinimumWidth(380)

        self.init_ui()
        self.load_status()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # 当前账号状态
        self.status_label = QLabel("...")
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(self.status_label)

        layout.addWidget(self._separator())

        # —— 绑定邮箱 ——
        layout.addWidget(QLabel("绑定邮箱（把本机账号升级为正式账号，数据保留）"))
        bind_row = QHBoxLayout()
        self.bind_email_input = QLineEdit()
        self.bind_email_input.setPlaceholderText("you@example.com")
        self.bind_btn = QPushButton("发送确认邮件")
        self.bind_btn.setCursor(Qt.PointingHandCursor)
        self.bind_btn.clicked.connect(self.on_bind_email)
        bind_row.addWidget(self.bind_email_input, 1)
        bind_row.addWidget(self.bind_btn)
        layout.addLayout(bind_row)

        layout.addWidget(self._separator())

        # —— 用邮箱登录（切换到已有账号）——
        layout.addWidget(QLabel("用邮箱登录（登录另一台设备上已绑定的账号）"))
        code_row1 = QHBoxLayout()
        self.login_email_input = QLineEdit()
        self.login_email_input.setPlaceholderText("you@example.com")
        self.send_code_btn = QPushButton("发送验证码")
        self.send_code_btn.setCursor(Qt.PointingHandCursor)
        self.send_code_btn.clicked.connect(self.on_send_code)
        code_row1.addWidget(self.login_email_input, 1)
        code_row1.addWidget(self.send_code_btn)
        layout.addLayout(code_row1)

        code_row2 = QHBoxLayout()
        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("邮件里的 6 位验证码")
        self.code_input.setMaxLength(10)
        self.login_btn = QPushButton("登录")
        self.login_btn.setCursor(Qt.PointingHandCursor)
        self.login_btn.clicked.connect(self.on_verify_code)
        code_row2.addWidget(self.code_input, 1)
        code_row2.addWidget(self.login_btn)
        layout.addLayout(code_row2)

        # 提示信息
        self.message_label = QLabel("")
        self.message_label.setWordWrap(True)
        self.message_label.setStyleSheet("color: #6b7280;")
        layout.addWidget(self.message_label)

    @staticmethod
    def _separator() -> QFrame:
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        return line

    # ============================
    # 状态
    # ============================

    def load_status(self):
        self.status_label.setText("正在读取账号信息...")
        self._run(self.auth_service.get_account_info, on_ok=self._show_status)

    def _show_status(self, info):
        if not isinstance(info, dict):
            return
        if info.get("email"):
            self.status_label.setText(f"当前账号：{info['email']}")
        else:
            self.status_label.setText(
                f"当前账号：匿名（{(info.get('user_id') or '')[:8]}…）\n"
                "绑定邮箱后才能在手机上登录同一个账号。"
            )

    # ============================
    # 操作
    # ============================

    def on_bind_email(self):
        email = self.bind_email_input.text().strip()
        if not email or "@" not in email:
            self._message("请输入有效的邮箱地址", error=True)
            return
        self._message("正在发送确认邮件...")
        self._run(
            self.auth_service.bind_email, email,
            on_ok=lambda _: self._message(
                f"确认邮件已发到 {email}，请到邮箱点击链接完成绑定。\n"
                "完成后在手机上用这个邮箱登录，就能看到这里的全部任务。"
            ),
        )

    def on_send_code(self):
        email = self.login_email_input.text().strip()
        if not email or "@" not in email:
            self._message("请输入有效的邮箱地址", error=True)
            return
        self._message("正在发送验证码...")
        self._run(
            self.auth_service.send_login_code, email,
            on_ok=lambda _: self._message(f"验证码已发到 {email}，请查收后填入下方。"),
        )

    def on_verify_code(self):
        email = self.login_email_input.text().strip()
        code = self.code_input.text().strip()
        if not email or not code:
            self._message("请填写邮箱和验证码", error=True)
            return
        self._message("正在登录...")
        self._run(
            self.auth_service.sign_in_with_code, email, code,
            on_ok=self._on_signed_in,
        )

    def _on_signed_in(self, switched):
        self.code_input.clear()
        self.load_status()
        if switched:
            self._message("登录成功，已切换账号。正在清空本机旧数据并重新同步...")
            self.account_switched.emit()
        else:
            self._message("登录成功（仍是同一个账号）。")

    # ============================
    # 辅助
    # ============================

    def _run(self, fn, *args, on_ok=None):
        """把一个网络操作丢到后台线程，期间禁用按钮"""
        self._set_busy(True)

        worker = AuthWorker(fn, *args, parent=self)

        def handle_ok(result):
            self._set_busy(False)
            if on_ok:
                on_ok(result)

        def handle_err(msg):
            self._set_busy(False)
            self._message(self._friendly_error(msg), error=True)

        worker.succeeded.connect(handle_ok)
        worker.failed.connect(handle_err)
        worker.finished.connect(lambda: setattr(self, "_worker", None))
        self._worker = worker
        worker.start()

    @staticmethod
    def _friendly_error(msg: str) -> str:
        """把 Supabase 的原始报错翻译成人能看懂的话"""
        lowered = msg.lower()
        if "network error" in lowered:
            return "连不上服务器，请检查网络后重试。"
        if "otp_expired" in lowered or "expired" in lowered:
            return "验证码已过期，请重新发送。"
        if "invalid" in lowered and "token" in lowered:
            return "验证码不正确，请检查后重试。"
        if "email_exists" in lowered or "already been registered" in lowered:
            return "该邮箱已被注册。请改用下方「用邮箱登录」。"
        if "rate limit" in lowered or "429" in lowered:
            return "发送太频繁，请过几分钟再试。"
        return f"操作失败：{msg}"

    def _set_busy(self, busy: bool):
        for btn in (self.bind_btn, self.send_code_btn, self.login_btn):
            btn.setEnabled(not busy)

    def _message(self, text: str, error: bool = False):
        self.message_label.setStyleSheet(f"color: {'#dc2626' if error else '#6b7280'};")
        self.message_label.setText(text)
