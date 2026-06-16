"""
版本更新检查服务
后台线程检查 GitHub Release，不阻塞 UI
"""
import json
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
    
    # 信号：发现新版本 (版本号字符串)
    update_available = pyqtSignal(str)
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
                # 有新版本
                # 清理版本号前缀以统一格式
                version_str = tag_name.lstrip('vV')
                logger.info(f"Update available: v{version_str}")
                self.update_available.emit(version_str)
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
