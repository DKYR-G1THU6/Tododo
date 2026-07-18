"""
Supabase REST 客户端（仅用标准库 urllib，零新增依赖）

只封装 Tododo 需要的那部分：匿名登录、刷新会话、tasks 表的推/拉。
沿用 services/update_service.py 的 urllib 风格，避免为打包引入重型依赖。
"""
import json
import logging
import urllib.request
import urllib.error
import urllib.parse
from typing import List, Optional

import config

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 15


class SupabaseError(Exception):
    """Supabase 调用失败"""

    def __init__(self, message: str, status: Optional[int] = None):
        super().__init__(message)
        self.status = status


class SupabaseClient:
    """Supabase Auth + PostgREST 的轻量客户端"""

    def __init__(self, url: str = config.SUPABASE_URL, anon_key: str = config.SUPABASE_ANON_KEY):
        self.url = url.rstrip('/')
        self.anon_key = anon_key
        self.auth_url = f"{self.url}/auth/v1"
        self.rest_url = f"{self.url}/rest/v1"

    # ============================
    # 内部：HTTP
    # ============================

    def _request(
        self,
        method: str,
        url: str,
        body: Optional[dict or list] = None,
        token: Optional[str] = None,
        extra_headers: Optional[dict] = None,
        timeout: int = DEFAULT_TIMEOUT,
    ):
        """发一个 JSON 请求，返回解析后的结果（无内容时返回 None）"""
        headers = {
            "apikey": self.anon_key,
            "Authorization": f"Bearer {token or self.anon_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": f"Tododo/{config.APP_VERSION}",
        }
        if extra_headers:
            headers.update(extra_headers)

        data = json.dumps(body).encode("utf-8") if body is not None else None
        req = urllib.request.Request(url, data=data, headers=headers, method=method)

        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read().decode("utf-8").strip()
                return json.loads(raw) if raw else None
        except urllib.error.HTTPError as e:
            detail = ""
            try:
                detail = e.read().decode("utf-8")
            except Exception:
                pass
            raise SupabaseError(f"HTTP {e.code} on {method} {url}: {detail}", status=e.code) from e
        except urllib.error.URLError as e:
            # 断网/DNS 失败等，同步层据此判定“离线”
            raise SupabaseError(f"network error on {method} {url}: {e.reason}") from e

    # ============================
    # Auth
    # ============================

    def sign_in_anonymously(self) -> dict:
        """
        匿名登录，创建一个只属于本人的匿名用户。
        返回 {access_token, refresh_token, expires_in, user_id}
        """
        result = self._request("POST", f"{self.auth_url}/signup", body={"data": {}})
        return self._to_session(result)

    def refresh_session(self, refresh_token: str) -> dict:
        """用 refresh_token 换新的 access_token"""
        result = self._request(
            "POST",
            f"{self.auth_url}/token?grant_type=refresh_token",
            body={"refresh_token": refresh_token},
        )
        return self._to_session(result)

    def get_user(self, access_token: str) -> dict:
        """获取当前登录用户信息（用于判断是匿名还是已绑定邮箱）"""
        return self._request("GET", f"{self.auth_url}/user", token=access_token) or {}

    def update_user_email(self, access_token: str, email: str) -> dict:
        """
        给当前账号绑定邮箱。

        匿名账号绑定邮箱后会升级为正式账号，原有数据（user_id）全部保留。
        Supabase 会发一封确认邮件，用户点击链接后绑定才生效。
        """
        return self._request(
            "PUT", f"{self.auth_url}/user", body={"email": email}, token=access_token
        ) or {}

    def set_password(self, access_token: str, password: str) -> dict:
        """
        给当前账号设置登录密码。

        设了密码后，另一台设备就能用「邮箱 + 密码」登录同一账号，
        整个过程不需要发任何邮件（Supabase 内置邮件限 2 封/小时，且
        改邮件模板还要求先配自定义 SMTP）。
        """
        return self._request(
            "PUT", f"{self.auth_url}/user", body={"password": password}, token=access_token
        ) or {}

    def sign_in_with_password(self, email: str, password: str) -> dict:
        """用邮箱 + 密码登录，返回会话。不发邮件。"""
        result = self._request(
            "POST",
            f"{self.auth_url}/token?grant_type=password",
            body={"email": email, "password": password},
        )
        return self._to_session(result)

    def send_email_otp(self, email: str) -> None:
        """给邮箱发一封登录验证码（6 位数字）"""
        self._request(
            "POST",
            f"{self.auth_url}/otp",
            body={"email": email, "create_user": False},
        )

    def verify_email_otp(self, email: str, code: str) -> dict:
        """
        校验邮箱验证码，成功后返回该邮箱账号的会话。
        用于在第二台设备上登录同一个账号。
        """
        result = self._request(
            "POST",
            f"{self.auth_url}/verify",
            body={"email": email, "token": code, "type": "email"},
        )
        return self._to_session(result)

    @staticmethod
    def _to_session(result: dict) -> dict:
        """把 GoTrue 返回体收敛成我们自己的 session 结构"""
        if not result or not result.get("access_token"):
            raise SupabaseError(f"unexpected auth response: {result}")
        user = result.get("user") or {}
        return {
            "access_token": result["access_token"],
            "refresh_token": result.get("refresh_token"),
            "expires_in": result.get("expires_in", 3600),
            "user_id": user.get("id"),
        }

    # ============================
    # tasks 表
    # ============================

    def upsert_tasks(self, access_token: str, rows: List[dict]) -> list:
        """
        按 uuid upsert 一批任务（INSERT ... ON CONFLICT DO UPDATE）。
        user_id 不传，由云端 default auth.uid() 填充。
        """
        if not rows:
            return []
        return self._request(
            "POST",
            f"{self.rest_url}/tasks",
            body=rows,
            token=access_token,
            extra_headers={"Prefer": "resolution=merge-duplicates,return=representation"},
        ) or []

    # ============================
    # Storage / Edge Function（语音用）
    # ============================

    def upload_storage_object(
        self, access_token: str, bucket: str, path: str, data: bytes, content_type: str
    ) -> None:
        """
        上传二进制对象到 Storage。

        路径必须以 {user_id}/ 开头 —— Storage 的 RLS 策略就是按首段判断归属的。
        走独立方法而不是 _request，因为这里发的是二进制而不是 JSON。
        """
        url = f"{self.url}/storage/v1/object/{bucket}/{path}"
        headers = {
            "apikey": self.anon_key,
            "Authorization": f"Bearer {access_token}",
            "Content-Type": content_type,
            "x-upsert": "true",
            "User-Agent": f"Tododo/{config.APP_VERSION}",
        }
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                resp.read()
        except urllib.error.HTTPError as e:
            detail = ""
            try:
                detail = e.read().decode("utf-8")
            except Exception:
                pass
            raise SupabaseError(f"storage upload failed HTTP {e.code}: {detail}", status=e.code) from e
        except urllib.error.URLError as e:
            raise SupabaseError(f"storage upload network error: {e.reason}") from e

    def create_signed_url(
        self, access_token: str, bucket: str, path: str, expires_in: int = 3600
    ) -> str:
        """给私有桶里的对象生成临时可播放地址"""
        result = self._request(
            "POST",
            f"{self.url}/storage/v1/object/sign/{bucket}/{path}",
            body={"expiresIn": expires_in},
            token=access_token,
        ) or {}
        signed = result.get("signedURL") or result.get("signedUrl")
        if not signed:
            raise SupabaseError(f"unexpected sign response: {result}")
        return f"{self.url}/storage/v1{signed}"

    def invoke_function(self, access_token: str, name: str, payload: dict) -> dict:
        """调用 Edge Function（转写用）"""
        return self._request(
            "POST", f"{self.url}/functions/v1/{name}", body=payload, token=access_token, timeout=120
        ) or {}

    def fetch_tasks_since(self, access_token: str, cursor: Optional[str] = None, limit: int = 1000) -> list:
        """
        增量拉取：取 updated_at 晚于 cursor 的行（cursor 为 RFC3339 UTC 字符串）。
        cursor 为空时拉取全部（首次同步）。
        """
        params = {
            "select": "*",
            "order": "updated_at.asc",
            "limit": str(limit),
        }
        if cursor:
            params["updated_at"] = f"gt.{cursor}"

        query = urllib.parse.urlencode(params)
        return self._request("GET", f"{self.rest_url}/tasks?{query}", token=access_token) or []
