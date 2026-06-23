"""
版本更新交互弹窗
"""
import os
import sys
import logging
import subprocess
from pathlib import Path
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTextBrowser, QProgressBar, QWidget, QApplication
)
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QFont, QIcon

import config
from services.update_service import UpdateDownloadWorker
from ui.styles import apply_styles

logger = logging.getLogger(__name__)


class UpdateWindow(QDialog):
    """自定义现代化无边框更新弹窗"""
    
    def __init__(self, version: str, changelog: str, download_url: str, 
                 notification_service, language: str = None, parent=None):
        super().__init__(parent)
        self.version = version
        self.changelog = changelog
        self.download_url = download_url
        self.notification_service = notification_service
        self.language = language or config.CURRENT_LANGUAGE
        
        self.drag_start_pos = None
        self.download_worker = None
        self.temp_file_path = ""
        self.is_download_in_bg = False
        
        # 判断是否为打包后的 exe 运行环境
        self.is_frozen = getattr(sys, 'frozen', False)
        
        self.init_ui()
        
    def init_ui(self):
        """初始化界面"""
        t = config.TRANSLATIONS[self.language]
        self.setWindowTitle(t["update_title"])
        self.setFixedSize(config.WINDOW_WIDTH, config.WINDOW_HEIGHT - 60) # 稍矮于主窗口
        
        # 窗口标志：无边框、置顶、对话框
        self.setWindowFlags(
            Qt.Dialog | 
            Qt.FramelessWindowHint | 
            Qt.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # 设置图标
        icon_path = Path(__file__).parent.parent / "resources" / "tododo.ico"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
            
        outer_layout = QVBoxLayout()
        outer_layout.setContentsMargins(10, 10, 10, 10)
        outer_layout.setSpacing(0)
        
        # 主容器
        container = QWidget()
        container.setObjectName("mainContainer")
        container_layout = QVBoxLayout()
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        
        # 1. 标题栏
        self.title_bar = QWidget()
        self.title_bar.setObjectName("titleBar")
        self.title_bar.setFixedHeight(50)
        
        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(12, 0, 12, 0)
        title_layout.setSpacing(8)
        
        self.title_label = QLabel(f"{t['update_title']} (v{self.version})")
        self.title_label.setObjectName("titleLabel")
        font = QFont()
        font.setPointSize(11)
        font.setBold(True)
        self.title_label.setFont(font)
        
        # 关闭按钮
        self.close_button = QPushButton("×")
        self.close_button.setObjectName("closeBtn")
        self.close_button.setFixedSize(36, 36)
        self.close_button.setCursor(Qt.PointingHandCursor)
        self.close_button.clicked.connect(self.on_close_clicked)
        
        title_layout.addWidget(self.title_label, 1)
        title_layout.addWidget(self.close_button)
        
        # 2. 内容主体
        body_widget = QWidget()
        body_layout = QVBoxLayout(body_widget)
        body_layout.setContentsMargins(16, 16, 16, 16)
        body_layout.setSpacing(12)
        
        # 更新日志标题
        changelog_title = QLabel(t["update_changelog"])
        changelog_title.setStyleSheet("font-weight: bold; font-size: 10.5pt; color: #475569;")
        
        # 更新日志展示区（只读 QTextBrowser，支持 HTML/Markdown 式换行）
        self.changelog_browser = QTextBrowser()
        self.changelog_browser.setObjectName("changelogBrowser")
        self.changelog_browser.setHtml(self.format_changelog(self.changelog))
        
        # 开发/源码模式提示
        self.dev_tip_label = QLabel(t["update_dev_mode_tip"])
        self.dev_tip_label.setWordWrap(True)
        self.dev_tip_label.setStyleSheet("color: #e11d48; font-size: 9pt; font-weight: 500;")
        if self.is_frozen:
            self.dev_tip_label.hide()
            
        # 下载进度指示区（默认隐藏）
        self.progress_container = QWidget()
        progress_layout = QVBoxLayout(self.progress_container)
        progress_layout.setContentsMargins(0, 0, 0, 0)
        progress_layout.setSpacing(6)
        
        self.status_label = QLabel(t["update_downloading"])
        self.status_label.setStyleSheet("color: #475569; font-size: 9.5pt;")
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("updateProgressBar")
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(8)
        
        self.speed_label = QLabel("")
        self.speed_label.setStyleSheet("color: #64748b; font-size: 9pt;")
        
        progress_layout.addWidget(self.status_label)
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.speed_label)
        
        self.progress_container.hide()
        
        body_layout.addWidget(changelog_title)
        body_layout.addWidget(self.changelog_browser, 1)
        body_layout.addWidget(self.dev_tip_label)
        body_layout.addWidget(self.progress_container)
        
        # 3. 底部操作栏
        footer_widget = QWidget()
        footer_layout = QHBoxLayout(footer_widget)
        footer_layout.setContentsMargins(16, 0, 16, 16)
        footer_layout.setSpacing(12)
        
        # 稍后再说按钮
        self.later_button = QPushButton(t["update_btn_later"])
        self.later_button.setObjectName("laterBtn")
        self.later_button.setCursor(Qt.PointingHandCursor)
        self.later_button.setFixedHeight(36)
        self.later_button.clicked.connect(self.on_later_clicked)
        
        # 确认更新按钮
        self.confirm_button = QPushButton()
        self.confirm_button.setObjectName("confirmBtn")
        self.confirm_button.setCursor(Qt.PointingHandCursor)
        self.confirm_button.setFixedHeight(36)
        self.confirm_button.clicked.connect(self.on_confirm_clicked)
        
        # 初始化确认按钮文本与可用性
        if self.is_frozen:
            self.confirm_button.setText(t["update_btn_now"])
            if not self.download_url:
                self.confirm_button.setEnabled(False)
        else:
            # 源码运行模式下，只显示打开发布页面
            self.confirm_button.setObjectName("confirmBtnDev")
            self.confirm_button.setText(t["update_btn_open_release"])
            
        footer_layout.addStretch(1)
        footer_layout.addWidget(self.later_button)
        footer_layout.addWidget(self.confirm_button)
        
        container_layout.addWidget(self.title_bar)
        container_layout.addWidget(body_widget, 1)
        container_layout.addWidget(footer_widget)
        container.setLayout(container_layout)
        
        outer_layout.addWidget(container)
        self.setLayout(outer_layout)
        
        apply_styles(self)
        
    def format_changelog(self, text: str) -> str:
        """转换 Changelog 为 HTML 格式"""
        if not text:
            t = config.TRANSLATIONS[self.language]
            return f"<p style='color:#64748b; font-style:italic; line-height: 1.4;'>{t.get('update_no_notes', '此版本未提供详细更新日志。')}</p>"
        
        lines = text.split('\n')
        html_lines = []
        for line in lines:
            line_str = line.strip()
            if not line_str:
                html_lines.append("<br>")
                continue
            
            # Markdown 标题解析
            if line_str.startswith("### "):
                html_lines.append(f"<h3 style='color:#0f172a; margin-top:8px; margin-bottom:4px;'>{line_str[4:]}</h3>")
            elif line_str.startswith("## "):
                html_lines.append(f"<h2 style='color:#0f172a; margin-top:10px; margin-bottom:6px;'>{line_str[3:]}</h2>")
            elif line_str.startswith("- ") or line_str.startswith("* "):
                # 解析加粗语法 **bold**
                content = line_str[2:]
                content = self._parse_bold(content)
                html_lines.append(f"<li style='margin-left: 10px; color:#334155; line-height: 1.4;'>{content}</li>")
            else:
                content = self._parse_bold(line_str)
                html_lines.append(f"<p style='color:#334155; line-height: 1.4;'>{content}</p>")
                
        return "".join(html_lines)
        
    def _parse_bold(self, text: str) -> str:
        """简单解析 **加粗**"""
        import re
        return re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)

    def on_confirm_clicked(self):
        """点击确认按钮"""
        t = config.TRANSLATIONS[self.language]
        
        if not self.is_frozen:
            # 源码运行：直接打开网页
            import webbrowser
            webbrowser.open(config.GITHUB_RELEASE_URL)
            self.accept()
            return
            
        # 打包运行：判断当前所处阶段
        if self.temp_file_path:
            # 下载已完成，重启并应用更新
            self.install_and_restart()
        else:
            # 开始下载
            self.start_download()
            
    def start_download(self):
        """启动下载"""
        t = config.TRANSLATIONS[self.language]
        
        # 禁用或切换按钮
        self.later_button.setEnabled(False) # 下载中禁止点击取消关闭（可使用后台下载）
        self.later_button.hide()
        
        # 确认按钮变更为“后台下载”
        self.confirm_button.setText(t["update_btn_bg"])
        
        # 显示进度条
        self.progress_container.show()
        self.changelog_browser.hide() # 腾出高度
        
        # 准备下载路径
        dest_dir = config.APP_DATA_DIR / "updates"
        dest_path = dest_dir / "Tododo_new.exe"
        
        self.download_worker = UpdateDownloadWorker(self.download_url, str(dest_path))
        self.download_worker.progress.connect(self.on_download_progress)
        self.download_worker.completed.connect(self.on_download_completed)
        self.download_worker.failed.connect(self.on_download_failed)
        self.download_worker.start()
        
    def on_download_progress(self, percent: int, speed: float):
        """更新下载进度"""
        t = config.TRANSLATIONS[self.language]
        self.progress_bar.setValue(percent)
        
        # 格式化速度
        if speed >= 1024.0:
            speed_str = f"{speed/1024.0:.2f} MB/s"
        else:
            speed_str = f"{speed:.1f} KB/s"
            
        self.speed_label.setText(t["update_download_speed"].format(speed=speed_str, percent=percent))
        
    def on_download_completed(self, file_path: str):
        """下载完成"""
        t = config.TRANSLATIONS[self.language]
        self.temp_file_path = file_path
        
        # 恢复“取消”按钮，变更为关闭
        self.later_button.setText(t["update_btn_later"])
        self.later_button.setEnabled(True)
        self.later_button.show()
        
        # 确认按钮变更为“立即重启”
        self.confirm_button.setText(t["update_btn_restart"])
        self.confirm_button.setEnabled(True)
        self.confirm_button.show()
        
        self.status_label.setText(t["update_download_success"])
        self.speed_label.setText("")
        
        # 如果是在后台下载，发送系统托盘通知
        if self.is_download_in_bg:
            self.notification_service.notify(
                t["toast_system_title"],
                t["update_download_success"],
                duration=5
            )
            # 用户可能已经关闭了窗口，通知后自动清理或静默
            
    def on_download_failed(self, error_msg: str):
        """下载失败"""
        t = config.TRANSLATIONS[self.language]
        self.download_worker = None
        
        # 恢复状态
        self.later_button.setText(t["update_btn_later"])
        self.later_button.setEnabled(True)
        self.later_button.show()
        
        self.confirm_button.setText(t["update_btn_now"])
        self.confirm_button.setEnabled(True)
        
        self.status_label.setText(t["update_download_failed"].format(error=error_msg))
        self.speed_label.setText("")
        
        # 重新拉起日志展示，便于重新点击
        self.changelog_browser.show()
        self.progress_container.hide()
        
        if self.is_download_in_bg:
            self.notification_service.notify(
                t["toast_system_title"],
                t["update_download_failed"].format(error=error_msg),
                duration=5
            )
            
    def install_and_restart(self):
        """写入批处理脚本覆盖旧文件并重启"""
        target_path = sys.executable
        temp_path = self.temp_file_path
        
        # 覆盖路径为当前 exe 所在目录
        helper_path = os.path.join(os.path.dirname(temp_path), "update_helper.bat")
        
        # 编写批处理，循环检测文件锁并覆盖
        bat_content = f"""@echo off
setlocal enabledelayedexpansion

:: 等待主进程完全关闭 (循环检测进程或延迟)
timeout /t 1 /nobreak > nul

set "MAX_TRIES=15"
set "TRY=0"

:loop
move /y "{temp_path}" "{target_path}" > nul
if !errorlevel! neq 0 (
    set /a TRY+=1
    if !TRY! gtr !MAX_TRIES! (
        echo Failed to apply update. File locked.
        exit /b 1
    )
    timeout /t 1 /nobreak > nul
    goto loop
)

:: 启动新版 exe
start "" "{target_path}"

:: 自我删除
del "%~f0"
"""
        try:
            with open(helper_path, "w", encoding="gbk") as f:
                f.write(bat_content)
                
            # 后台安静启动批处理脚本
            subprocess.Popen(
                f'cmd.exe /c "{helper_path}"', 
                shell=True, 
                creationflags=0x00000010 | 0x00000008 # CREATE_NEW_CONSOLE | DETACHED_PROCESS
            )
            
            # 关闭主程序进程
            QApplication.quit()
        except Exception as e:
            logger.error(f"Failed to start update helper: {e}")
            t = config.TRANSLATIONS[self.language]
            self.status_label.setText(f"Restart failed: {e}")
            
    def on_later_clicked(self):
        """点击稍后再说"""
        self.reject()
        
    def on_close_clicked(self):
        """点击关闭按钮"""
        # 如果下载 worker 正在运行，则代表用户选择“后台下载”
        if self.download_worker and self.download_worker.isRunning():
            self.is_download_in_bg = True
            logger.info("Update window closed. Downloading in background.")
        self.reject()
        
    def mousePressEvent(self, event):
        """拖动窗口按下"""
        if event.button() == Qt.LeftButton:
            if event.y() < self.title_bar.height():
                self.drag_start_pos = event.globalPos() - self.frameGeometry().topLeft()
                
    def mouseMoveEvent(self, event):
        """拖动窗口移动"""
        if self.drag_start_pos is not None:
            self.move(event.globalPos() - self.drag_start_pos)
            
    def mouseReleaseEvent(self, event):
        """释放拖动"""
        self.drag_start_pos = None
