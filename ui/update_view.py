"""
版本更新视图组件 (单窗口整合版)
"""
import os
import sys
import logging
import subprocess
from pathlib import Path
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTextBrowser, QProgressBar, QApplication
)
from PyQt5.QtCore import Qt, pyqtSignal

import config
from services.update_service import UpdateDownloadWorker
from ui.styles import apply_styles

logger = logging.getLogger(__name__)


class UpdateView(QWidget):
    """自定义页面级更新面板，内嵌入主窗口"""
    
    # 信号：请求返回上一个界面
    back_requested = pyqtSignal()
    
    def __init__(self, notification_service, parent=None):
        super().__init__(parent)
        self.notification_service = notification_service
        self.language = config.CURRENT_LANGUAGE
        
        self.version = ""
        self.changelog = ""
        self.download_url = ""
        
        self.download_worker = None
        self.temp_file_path = ""
        self.is_download_in_bg = False
        
        # 判断是否为打包后的 exe 运行环境
        self.is_frozen = getattr(sys, 'frozen', False)
        
        self.init_ui()
        
    def init_ui(self):
        """初始化界面"""
        t = config.TRANSLATIONS[self.language]
        
        layout = QVBoxLayout()
        layout.setContentsMargins(16, 12, 16, 16)
        layout.setSpacing(12)
        
        # 更新日志标题
        changelog_title = QLabel(t["update_changelog"])
        changelog_title.setStyleSheet("font-weight: bold; font-size: 10.5pt; color: #475569;")
        
        # 更新日志展示区 (自适应样式)
        self.changelog_browser = QTextBrowser()
        self.changelog_browser.setObjectName("changelogBrowser")
        
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
        
        layout.addWidget(changelog_title)
        layout.addWidget(self.changelog_browser, 1)
        layout.addWidget(self.dev_tip_label)
        layout.addWidget(self.progress_container)
        
        # 底部操作栏
        footer_widget = QWidget()
        footer_layout = QHBoxLayout(footer_widget)
        footer_layout.setContentsMargins(0, 0, 0, 0)
        footer_layout.setSpacing(12)
        
        # 稍后再说按钮 (返回上页)
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
        
        footer_layout.addStretch(1)
        footer_layout.addWidget(self.later_button)
        footer_layout.addWidget(self.confirm_button)
        layout.addWidget(footer_widget)
        
        self.setLayout(layout)
        apply_styles(self)
        
    def set_update_info(self, version: str, changelog: str, download_url: str):
        """设置更新数据"""
        self.version = version
        self.changelog = changelog
        self.download_url = download_url
        
        t = config.TRANSLATIONS[self.language]
        
        self.changelog_browser.setHtml(self.format_changelog(self.changelog))
        
        # 重置下载状态
        self.temp_file_path = ""
        self.is_download_in_bg = False
        self.progress_container.hide()
        self.changelog_browser.show()
        
        self.later_button.setText(t["update_btn_later"])
        self.later_button.setEnabled(True)
        self.later_button.show()
        
        self.confirm_button.setEnabled(True)
        if self.is_frozen:
            self.confirm_button.setObjectName("confirmBtn")
            self.confirm_button.setText(t["update_btn_now"])
            if not self.download_url:
                self.confirm_button.setEnabled(False)
        else:
            self.confirm_button.setObjectName("confirmBtnDev")
            self.confirm_button.setText(t["update_btn_open_release"])
            
        apply_styles(self)

    def set_language(self, lang: str):
        """主窗口切换语言"""
        self.language = lang
        if self.version:
            # 重新加载文字描述
            self.set_update_info(self.version, self.changelog, self.download_url)
            
    def format_changelog(self, text: str) -> str:
        """转换 Changelog 为 HTML 格式"""
        if not text:
            t = config.TRANSLATIONS[self.language]
            return f"<p style='color:#64748b; font-style:italic; line-height: 1.4;'>{t.get('update_no_notes', '此版本未提供详细更新日志。')}</p>"
        
        import re
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
                content = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', content)
                html_lines.append(f"<li style='margin-left: 10px; color:#334155; line-height: 1.4;'>{content}</li>")
            else:
                content = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', line_str)
                html_lines.append(f"<p style='color:#334155; line-height: 1.4;'>{content}</p>")
                
        return "".join(html_lines)

    def on_confirm_clicked(self):
        """点击确认"""
        if not self.is_frozen:
            # 源码运行，用默认浏览器打开发布页
            import webbrowser
            webbrowser.open(config.GITHUB_RELEASE_URL)
            self.back_requested.emit()
            return
            
        if self.temp_file_path:
            # 下载已完成，重启程序应用更新
            self.install_and_restart()
        else:
            # 开始下载
            self.start_download()
            
    def start_download(self):
        """开始下载新版本"""
        t = config.TRANSLATIONS[self.language]
        
        # 隐藏稍后再说按钮，避免用户在下载中取消
        self.later_button.hide()
        
        # 将确定按钮改写为“后台下载”，用户点击可以隐藏页面并不影响下载
        self.confirm_button.setText(t["update_btn_bg"])
        
        # 显示进度条
        self.progress_container.show()
        self.changelog_browser.hide()
        
        dest_dir = config.APP_DATA_DIR / "updates"
        dest_path = dest_dir / "Tododo_new.exe"
        
        self.download_worker = UpdateDownloadWorker(self.download_url, str(dest_path))
        self.download_worker.progress.connect(self.on_download_progress)
        self.download_worker.completed.connect(self.on_download_completed)
        self.download_worker.failed.connect(self.on_download_failed)
        self.download_worker.start()
        
    def on_download_progress(self, percent: int, speed: float):
        t = config.TRANSLATIONS[self.language]
        self.progress_bar.setValue(percent)
        
        if speed >= 1024.0:
            speed_str = f"{speed/1024.0:.2f} MB/s"
        else:
            speed_str = f"{speed:.1f} KB/s"
            
        self.speed_label.setText(t["update_download_speed"].format(speed=speed_str, percent=percent))
        
    def on_download_completed(self, file_path: str):
        t = config.TRANSLATIONS[self.language]
        self.temp_file_path = file_path
        
        # 恢复操作按钮，确认按钮改写为“立即重启并安装”
        self.later_button.setText(t["update_btn_later"])
        self.later_button.show()
        
        self.confirm_button.setText(t["update_btn_restart"])
        self.confirm_button.show()
        
        self.status_label.setText(t["update_download_success"])
        self.speed_label.setText("")
        
        # 后台静默模式下弹出 Toast 提醒
        if self.is_download_in_bg:
            self.notification_service.notify(
                t["toast_system_title"],
                t["update_download_success"],
                duration=5
            )
            
    def on_download_failed(self, error_msg: str):
        t = config.TRANSLATIONS[self.language]
        self.download_worker = None
        
        self.later_button.setText(t["update_btn_later"])
        self.later_button.show()
        
        self.confirm_button.setText(t["update_btn_now"])
        
        self.status_label.setText(t["update_download_failed"].format(error=error_msg))
        self.speed_label.setText("")
        
        self.changelog_browser.show()
        self.progress_container.hide()
        
        if self.is_download_in_bg:
            self.notification_service.notify(
                t["toast_system_title"],
                t["update_download_failed"].format(error=error_msg),
                duration=5
            )
            
    def notify_exited_page(self):
        """当用户点击返回退出本页面时，通知转入后台下载模式"""
        if self.download_worker and self.download_worker.isRunning():
            self.is_download_in_bg = True
            logger.info("User returned to main list. Download running in background.")
            
    def install_and_restart(self):
        """退出当前程序，启动批处理脚本进行文件替换并重启"""
        target_path = sys.executable
        temp_path = self.temp_file_path
        helper_path = os.path.join(os.path.dirname(temp_path), "update_helper.bat")
        
        bat_content = f"""@echo off
setlocal enabledelayedexpansion
timeout /t 1 /nobreak > nul

set "MAX_TRIES=15"
set "TRY=0"

:loop
move /y "{temp_path}" "{target_path}" > nul
if !errorlevel! neq 0 (
    set /a TRY+=1
    if !TRY! gtr !MAX_TRIES! (
        echo Failed to apply update.
        exit /b 1
    )
    timeout /t 1 /nobreak > nul
    goto loop
)
start "" "{target_path}"
del "%~f0"
"""
        try:
            with open(helper_path, "w", encoding="gbk") as f:
                f.write(bat_content)
                
            subprocess.Popen(
                f'cmd.exe /c "{helper_path}"', 
                shell=True, 
                creationflags=0x00000010 | 0x00000008
            )
            QApplication.quit()
        except Exception as e:
            logger.error(f"Failed to start update helper: {e}")
            self.status_label.setText(f"Restart failed: {e}")
            
    def on_later_clicked(self):
        """点击取消/返回，发出返回信号"""
        self.back_requested.emit()
