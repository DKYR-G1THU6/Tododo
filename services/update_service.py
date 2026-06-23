"""
版本更新检查及下载服务
后台线程处理网络请求与文件下载，不阻塞 UI
"""
import os
import json
import time
import logging
import urllib.request
import urllib.error
from PyQt5.QtCore import QThread, pyqtSignal

import config

logger = logging.getLogger(__name__)


def compare_versions(local: str, remote: str) -> int:
    """
    比较语义化版本号
    
    Returns:
        -1: local < remote (有更新)
         0: local == remote (已是最新)
         1: local > remote
    """
    def parse(v: str):
        # 去掉前缀 'v' 或 'V'
        v = v.strip().lstrip('vV')
        parts = []
        for p in v.split('.'):
            try:
                parts.append(int(p))
            except ValueError:
                parts.append(0)
        # 补齐到至少 3 段
        while len(parts) < 3:
            parts.append(0)
        return tuple(parts)
    
    local_t = parse(local)
    remote_t = parse(remote)
    
    if local_t < remote_t:
        return -1
    elif local_t == remote_t:
        return 0
    else:
        return 1


class UpdateCheckWorker(QThread):
    """后台版本检查线程"""
    
    # 信号：发现新版本 (版本号, 更新日志, 下载链接)
    update_available = pyqtSignal(str, str, str)
    # 信号：已是最新版本
    already_latest = pyqtSignal()
    # 信号：检查失败 (错误信息)
    check_failed = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
    
    def run(self):
        """执行版本检查"""
        try:
            logger.info("Starting update check...")
            
            # 构造请求
            req = urllib.request.Request(
                config.GITHUB_API_URL,
                headers={
                    'Accept': 'application/vnd.github.v3+json',
                    'User-Agent': f'{config.APP_NAME}/{config.APP_VERSION}'
                }
            )
            
            # 发送请求 (超时 10 秒)
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
            
            # 提取最新版本号
            tag_name = data.get('tag_name', '')
            if not tag_name:
                logger.warning("No tag_name found in GitHub release response")
                self.check_failed.emit("Invalid release data")
                return
            
            logger.info(f"Latest release: {tag_name}, local: v{config.APP_VERSION}")
            
            # 比较版本
            result = compare_versions(config.APP_VERSION, tag_name)
            
            if result < 0:
                # 有新版本，解析更新日志和 Tododo.exe 的下载链接
                version_str = tag_name.lstrip('vV')
                changelog = data.get('body') or ""
                
                # 寻找 Tododo.exe 的下载链接
                download_url = ""
                for asset in data.get('assets', []):
                    if asset.get('name') == 'Tododo.exe':
                        download_url = asset.get('browser_download_url', '')
                        break
                
                logger.info(f"Update available: v{version_str}, download: {download_url}")
                self.update_available.emit(version_str, changelog, download_url)
            else:
                logger.info("Already using the latest version")
                self.already_latest.emit()
                
        except urllib.error.URLError as e:
            error_msg = str(e.reason) if hasattr(e, 'reason') else str(e)
            logger.warning(f"Update check failed (network): {error_msg}")
            self.check_failed.emit(error_msg)
        except Exception as e:
            logger.warning(f"Update check failed: {e}")
            self.check_failed.emit(str(e))


class UpdateDownloadWorker(QThread):
    """后台下载新版本线程"""
    
    # 信号：下载进度 (百分比 %, 速度 KB/s)
    progress = pyqtSignal(int, float)
    # 信号：下载完成 (临时文件路径)
    completed = pyqtSignal(str)
    # 信号：下载失败 (错误信息)
    failed = pyqtSignal(str)
    
    def __init__(self, url: str, dest_path: str, parent=None):
        super().__init__(parent)
        self.url = url
        self.dest_path = dest_path
        self._is_cancelled = False
        
    def run(self):
        """执行下载逻辑"""
        try:
            logger.info(f"Starting download from {self.url} to {self.dest_path}")
            
            # 确保父目录存在
            os.makedirs(os.path.dirname(self.dest_path), exist_ok=True)
            
            req = urllib.request.Request(
                self.url,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                }
            )
            
            with urllib.request.urlopen(req, timeout=15) as response:
                total_size = int(response.info().get('Content-Length', 0))
                downloaded = 0
                start_time = time.time()
                last_update_time = start_time
                last_downloaded = 0
                
                with open(self.dest_path, 'wb') as f:
                    chunk_size = 16384  # 16KB 缓冲区
                    while True:
                        if self._is_cancelled:
                            f.close()
                            # 清理未下载完的文件
                            try:
                                if os.path.exists(self.dest_path):
                                    os.remove(self.dest_path)
                            except Exception as ex:
                                logger.error(f"Failed to cleanup temp file: {ex}")
                            self.failed.emit("Cancelled")
                            return
                        
                        chunk = response.read(chunk_size)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        curr_time = time.time()
                        # 每 0.25 秒或完成时更新一次速度和进度
                        if curr_time - last_update_time >= 0.25 or downloaded == total_size:
                            elapsed = curr_time - last_update_time
                            if elapsed > 0:
                                speed = (downloaded - last_downloaded) / elapsed / 1024.0
                            else:
                                speed = 0.0
                            
                            percent = int((downloaded / total_size) * 100) if total_size > 0 else 0
                            self.progress.emit(percent, speed)
                            
                            last_update_time = curr_time
                            last_downloaded = downloaded
            
            if not self._is_cancelled:
                logger.info("Download completed successfully")
                self.completed.emit(self.dest_path)
                
        except urllib.error.URLError as e:
            error_msg = str(e.reason) if hasattr(e, 'reason') else str(e)
            logger.warning(f"Download failed (network): {error_msg}")
            self.failed.emit(error_msg)
        except Exception as e:
            logger.warning(f"Download failed: {e}")
            self.failed.emit(str(e))
            
    def cancel(self):
        """取消下载"""
        self._is_cancelled = True
