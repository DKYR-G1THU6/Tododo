"""
开机启动服务
"""
import sys
import winreg
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class AutoStartService:
    """开机启动管理"""
    
    @staticmethod
    def _get_app_path() -> str:
        """获取应用程序路径"""
        if getattr(sys, 'frozen', False):
            # PyInstaller 打包后的 .exe 文件路径
            return sys.executable
        else:
            # 开发环境，使用 Python 脚本
            return f'"{sys.executable}" "{Path(__file__).parent.parent / "main.py"}"'
    
    @staticmethod
    def enable_autostart(app_path: str = None) -> bool:
        """
        启用开机启动
        
        Args:
            app_path: 应用程序路径，如不指定则自动检测
        
        Returns:
            是否成功
        """
        if not app_path:
            app_path = AutoStartService._get_app_path()
        
        try:
            # 打开注册表
            registry_key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                "Software\\Microsoft\\Windows\\CurrentVersion\\Run",
                0,
                winreg.KEY_SET_VALUE
            )
            
            # 写入注册表项
            winreg.SetValueEx(registry_key, "Tododo", 0, winreg.REG_SZ, app_path)
            winreg.CloseKey(registry_key)
            
            logger.info(f"Autostart enabled: {app_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to enable autostart: {e}")
            return False
    
    @staticmethod
    def disable_autostart() -> bool:
        """
        禁用开机启动
        
        Returns:
            是否成功
        """
        try:
            # 打开注册表
            registry_key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                "Software\\Microsoft\\Windows\\CurrentVersion\\Run",
                0,
                winreg.KEY_SET_VALUE
            )
            
            # 删除注册表项
            try:
                winreg.DeleteValue(registry_key, "Tododo")
                logger.info("Autostart disabled")
            except FileNotFoundError:
                # 项不存在，说明未启用
                pass
            
            winreg.CloseKey(registry_key)
            return True
        except Exception as e:
            logger.error(f"Failed to disable autostart: {e}")
            return False
    
    @staticmethod
    def is_autostart_enabled() -> bool:
        """
        检查是否已启用开机启动
        
        Returns:
            是否已启用
        """
        try:
            registry_key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                "Software\\Microsoft\\Windows\\CurrentVersion\\Run",
                0,
                winreg.KEY_READ
            )
            
            try:
                winreg.QueryValueEx(registry_key, "Tododo")
                result = True
            except FileNotFoundError:
                result = False
            
            winreg.CloseKey(registry_key)
            return result
        except Exception as e:
            logger.error(f"Failed to check autostart status: {e}")
            return False
