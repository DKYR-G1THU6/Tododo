"""
登录会话管理

个人自用场景：首次运行自动匿名登录，拿到一个属于自己的 user_id，
会话存到 %APPDATA%\\Tododo\\session.json，之后自动刷新。
（扫码配对第二台设备、可选绑定邮箱找回放在 M5。）
"""
import json
import logging
import time
from pathlib import Path
from typing import Optional

import config
from services.supabase_client import SupabaseClient, SupabaseError

logger = logging.getLogger(__name__)

# 提前这么多秒就认为 token 该刷新了，避免边界失效
EXPIRY_SKEW_SECONDS = 120


class AuthService:
    """匿名登录 + 会话持久化"""

    def __init__(self, client: Optional[SupabaseClient] = None, session_file: Path = config.SESSION_FILE):
        self.client = client or SupabaseClient()
        self.session_file = session_file
        self._session: Optional[dict] = self._load_session()

    # ============================
    # 会话读写
    # ============================

    def _load_session(self) -> Optional[dict]:
        if not self.session_file.exists():
            return None
        try:
            with open(self.session_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to read session file, ignoring: {e}")
            return None

    def _save_session(self, session: dict):
        """把 session 落盘（带绝对过期时间，便于下次启动判断）"""
        session = dict(session)
        session["expires_at"] = time.time() + float(session.pop("expires_in", 3600))
        try:
            with open(self.session_file, "w", encoding="utf-8") as f:
                json.dump(session, f)
            self._session = session
        except Exception as e:
            logger.error(f"Failed to persist session: {e}")
            self._session = session  # 内存里仍可用

    def clear_session(self):
        """清除本地会话（退出登录/重新配对时用）"""
        self._session = None
        try:
            if self.session_file.exists():
                self.session_file.unlink()
        except Exception as e:
            logger.warning(f"Failed to remove session file: {e}")

    # ============================
    # 对外
    # ============================

    @property
    def user_id(self) -> Optional[str]:
        return (self._session or {}).get("user_id")

    @property
    def is_signed_in(self) -> bool:
        return bool(self._session and self._session.get("access_token"))

    def _is_expired(self) -> bool:
        expires_at = (self._session or {}).get("expires_at", 0)
        return time.time() >= (expires_at - EXPIRY_SKEW_SECONDS)

    # ============================
    # 账号（M5：让两台设备认作同一个人）
    # ============================

    def get_account_info(self) -> dict:
        """返回 {user_id, email, is_anonymous}，用于界面展示当前账号状态"""
        token = self.ensure_session()
        user = self.client.get_user(token)
        email = user.get("email") or None
        return {
            "user_id": user.get("id"),
            "email": email,
            "is_anonymous": bool(user.get("is_anonymous", email is None)),
        }

    def bind_email(self, email: str):
        """
        给当前账号绑定邮箱。

        匿名账号绑定后升级为正式账号，**user_id 不变**，所以本机已有的任务
        全部保留、无需重新同步。Supabase 会发确认邮件，用户点链接后才生效。
        """
        token = self.ensure_session()
        self.client.update_user_email(token, email)
        logger.info("Email binding requested; confirmation mail sent")

    def send_login_code(self, email: str):
        """给邮箱发登录验证码（用于在另一台设备上登录同一账号）"""
        self.client.send_email_otp(email)

    def sign_in_with_code(self, email: str, code: str) -> bool:
        """
        用邮箱验证码登录。

        返回 True 表示登录到了**另一个** user —— 此时本地数据属于旧账号，
        调用方必须清空本地库和同步游标后重新全量拉取，否则会把旧账号的数据
        推到新账号里去。
        """
        previous_user_id = self.user_id
        session = self.client.verify_email_otp(email, code)
        self._save_session(session)
        switched = session.get("user_id") != previous_user_id
        logger.info(f"Signed in via email OTP; user switched={switched}")
        return switched

    def ensure_session(self) -> str:
        """
        确保有一个可用的 access_token，必要时匿名登录或刷新。
        返回 access_token；失败抛 SupabaseError（同步层据此判定离线/出错）。
        """
        # 完全没有会话 -> 匿名登录
        if not self.is_signed_in:
            logger.info("No local session, signing in anonymously...")
            session = self.client.sign_in_anonymously()
            self._save_session(session)
            logger.info(f"Anonymous sign-in ok, user_id={session.get('user_id')}")
            return self._session["access_token"]

        # 有会话但快过期 -> 刷新
        if self._is_expired():
            refresh_token = self._session.get("refresh_token")
            if refresh_token:
                try:
                    logger.info("Access token expiring, refreshing...")
                    session = self.client.refresh_session(refresh_token)
                    # 刷新响应可能不带 user_id，沿用旧的
                    session.setdefault("user_id", self._session.get("user_id"))
                    self._save_session(session)
                    return self._session["access_token"]
                except SupabaseError as e:
                    # refresh token 失效（例如很久没上线）-> 退回匿名登录
                    logger.warning(f"Refresh failed ({e}), falling back to anonymous sign-in")
                    self.clear_session()
                    session = self.client.sign_in_anonymously()
                    self._save_session(session)
                    return self._session["access_token"]

        return self._session["access_token"]
