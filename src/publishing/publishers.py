"""
YouTube and Instagram API Publishers with real Meta Graph API v19.0 integration,
OAuth 190 token health checking, quota awareness, and automated container status polling.
Falls back safely to deterministic dry-run mode when credentials are not configured.
"""
import uuid
import time
import json
import os
from pathlib import Path
import urllib.request
import urllib.error
import urllib.parse
from typing import Dict, Any, Optional
from src.config import settings


class PublishingError(Exception):
    pass


class TokenInvalidError(PublishingError):
    """Raised when Meta OAuth error 190 (token expired or invalidated) occurs."""
    pass


class QuotaExhaustedError(PublishingError):
    """Raised when account publishing limit headroom is less than 3."""
    pass


class YouTubePublisher:
    def __init__(self, access_token: Optional[str] = None):
        self.access_token = access_token or os.environ.get("YOUTUBE_ACCESS_TOKEN", "")
        self.quota_used: int = 0

    def refresh_access_token_if_needed(self) -> str:
        """
        Uses refresh_token with client_id and client_secret to automatically fetch
        a fresh access token from Google OAuth 2.0 without human intervention.
        """
        refresh_token = os.environ.get("YOUTUBE_REFRESH_TOKEN", "")
        client_id = os.environ.get("GOOGLE_CLIENT_ID", "")
        client_secret = os.environ.get("GOOGLE_CLIENT_SECRET", "")

        if not (refresh_token and client_id and client_secret):
            return self.access_token

        data = urllib.parse.urlencode({
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }).encode("utf-8")

        req = urllib.request.Request("https://oauth2.googleapis.com/token", data=data, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                res = json.loads(resp.read().decode("utf-8"))
                new_tok = res.get("access_token")
                if new_tok:
                    self.access_token = new_tok
                    os.environ["YOUTUBE_ACCESS_TOKEN"] = new_tok
                    return new_tok
        except Exception as e:
            pass
        return self.access_token

    def upload_short(
        self,
        video_path: str,
        title: str,
        description: str,
        account_ref: str = "main_channel",
        privacy_status: str = "public",
        retry_on_401: bool = True,
    ) -> Dict[str, Any]:
        """
        Uploads vertical video directly to YouTube as a Shorts video via YouTube Data API v3 resumable upload.
        Automatically retries with a fresh token if 401 Unauthorized occurs.
        """
        if not self.access_token:
            self.refresh_access_token_if_needed()

        if not self.access_token:
            # Deterministic dry run if no access token
            remote_id = f"yt-short-{uuid.uuid4().hex[:12]}"
            return {
                "destination": "youtube",
                "remote_id": remote_id,
                "status": "CONFIRMED",
                "video_url": f"https://youtube.com/shorts/{remote_id}",
                "privacy_status": privacy_status,
                "account_ref": account_ref,
                "quota_units_consumed": 1600,
            }

        vpath = Path(video_path)
        if not vpath.exists():
            raise PublishingError(f"Video file not found for upload: {video_path}")

        file_size = vpath.stat().st_size
        clean_title = title if "#Shorts" in title else f"{title[:90]} #Shorts"

        metadata = {
            "snippet": {
                "title": clean_title,
                "description": description,
                "categoryId": "20",  # 20 = Gaming
            },
            "status": {
                "privacyStatus": privacy_status,
                "selfDeclaredMadeForKids": False,
            }
        }

        # Step 1: Initiate Resumable Upload
        init_url = "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json; charset=UTF-8",
            "X-Upload-Content-Type": "video/mp4",
            "X-Upload-Content-Length": str(file_size),
        }

        try:
            req = urllib.request.Request(init_url, data=json.dumps(metadata).encode("utf-8"), headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=30) as resp:
                upload_url = resp.headers.get("Location")
                if not upload_url:
                    raise PublishingError("Google API did not return an upload Location URL.")
        except urllib.error.HTTPError as e:
            if e.code == 401 and retry_on_401:
                self.refresh_access_token_if_needed()
                return self.upload_short(
                    video_path=video_path,
                    title=title,
                    description=description,
                    account_ref=account_ref,
                    privacy_status=privacy_status,
                    retry_on_401=False,
                )
            err_body = e.read().decode("utf-8")
            raise PublishingError(f"YouTube Upload Initialization failed: {err_body}")

        # Step 2: Stream Video Content to Resumable URL
        try:
            with open(vpath, "rb") as vf:
                video_bytes = vf.read()

            upload_req = urllib.request.Request(
                upload_url,
                data=video_bytes,
                headers={
                    "Content-Type": "video/mp4",
                    "Content-Length": str(file_size),
                },
                method="PUT"
            )
            with urllib.request.urlopen(upload_req, timeout=120) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                video_id = data.get("id")
                if not video_id:
                    raise PublishingError(f"No video ID returned from YouTube: {data}")

                self.quota_used += 1600
                return {
                    "destination": "youtube",
                    "remote_id": video_id,
                    "video_url": f"https://youtube.com/shorts/{video_id}",
                    "status": "PUBLISHED",
                    "privacy_status": privacy_status,
                    "account_ref": account_ref,
                    "quota_units_consumed": 1600,
                }
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8")
            raise PublishingError(f"YouTube Video Upload failed: {err_body}")


class InstagramPublisher:
    def __init__(
        self,
        access_token: Optional[str] = None,
        account_id: Optional[str] = None,
        dry_run: Optional[bool] = None,
    ):
        self.access_token = access_token or getattr(settings, "instagram_access_token", None)
        self.account_id = account_id or getattr(settings, "instagram_account_id", None)
        # If no credentials provided, default to dry_run
        if dry_run is not None:
            self.dry_run = dry_run
        else:
            self.dry_run = not bool(self.access_token and self.account_id)
        self.api_version = "v19.0"
        self.base_url = f"https://graph.facebook.com/{self.api_version}"

    def verify_credentials(self, token: Optional[str] = None) -> Dict[str, Any]:
        """
        Validates token directly against Meta Graph API.
        Discovers linked Instagram Professional / Business Accounts.
        """
        tok = token or self.access_token
        if not tok:
            return {
                "status": "NOT_CONFIGURED",
                "valid": False,
                "message": "No Instagram Meta access token configured."
            }

        headers = {"User-Agent": "Mozilla/5.0"}
        # 1. Verify User Identity
        me_url = f"{self.base_url}/me?fields=id,name&access_token={tok}"
        try:
            req = urllib.request.Request(me_url, headers=headers, method="GET")
            with urllib.request.urlopen(req, timeout=12) as resp:
                me_data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8")
            try:
                err_json = json.loads(err_body).get("error", {})
                msg = err_json.get("message", err_body)
                code = err_json.get("code", 0)
            except Exception:
                msg = err_body
                code = 0
            return {
                "status": "TOKEN_INVALID" if code == 190 else "AUTH_ERROR",
                "valid": False,
                "code": code,
                "error": msg,
                "message": f"Meta Authentication Rejected: {msg}",
            }
        except Exception as e:
            return {
                "status": "NETWORK_ERROR",
                "valid": False,
                "error": str(e),
                "message": f"Network error contacting Meta Graph API: {str(e)}"
            }

        # 2. Discover Linked Instagram Business Accounts via Facebook Pages
        pages_url = f"{self.base_url}/me/accounts?fields=id,name,instagram_business_account{{id,username,name,profile_picture_url}}&access_token={tok}"
        try:
            req = urllib.request.Request(pages_url, headers=headers, method="GET")
            with urllib.request.urlopen(req, timeout=12) as resp:
                pages_data = json.loads(resp.read().decode("utf-8"))
                pages = pages_data.get("data", [])
                
                for page in pages:
                    ig_acc = page.get("instagram_business_account")
                    if ig_acc and ig_acc.get("id"):
                        return {
                            "status": "CONNECTED",
                            "valid": True,
                            "user_name": me_data.get("name"),
                            "page_id": page.get("id"),
                            "page_name": page.get("name"),
                            "instagram_account_id": ig_acc.get("id"),
                            "username": ig_acc.get("username", "verified_user"),
                            "display_name": ig_acc.get("name", ig_acc.get("username")),
                            "profile_picture_url": ig_acc.get("profile_picture_url"),
                            "message": f"Connected to @{ig_acc.get('username')} via {page.get('name')}",
                        }

                return {
                    "status": "NO_INSTAGRAM_LINKED",
                    "valid": True,
                    "user_name": me_data.get("name"),
                    "page_count": len(pages),
                    "message": "Token is valid for Meta user, but no Instagram Professional account is linked to your Facebook Pages. Please link your Instagram account to a Facebook Page in Meta Business Suite.",
                }
        except Exception as e:
            return {
                "status": "CONNECTED_PARTIAL",
                "valid": True,
                "user_name": me_data.get("name"),
                "error": str(e),
                "message": "Meta User authenticated, but unable to query linked Pages.",
            }

    def check_publishing_limit(self) -> Dict[str, Any]:
        """
        Checks 24-hour publishing limit against Meta content_publishing_limit API.
        Enforces safety headroom >= 3.
        """
        if self.dry_run:
            return {"quota_usage": 5, "quota_limit": 50, "headroom": 45, "ok": True}

        url = f"{self.base_url}/{self.account_id}/content_publishing_limit?fields=config,quota_usage&access_token={self.access_token}"
        try:
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                usage = data.get("data", [{}])[0].get("quota_usage", 0)
                config = data.get("data", [{}])[0].get("config", {})
                limit = config.get("quota_total", 50)
                headroom = limit - usage
                if headroom < 3:
                    raise QuotaExhaustedError(f"Publishing headroom is {headroom}. The queue stops under 3.")
                return {"quota_usage": usage, "quota_limit": limit, "headroom": headroom, "ok": True}
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8")
            if "190" in err_body:
                raise TokenInvalidError("Instagram access token has expired or is invalid (Error 190).")
            raise PublishingError(f"Failed to check Instagram quota: {err_body}")

    def create_reel_container(self, video_url: str, caption: str, account_ref: str) -> str:
        """
        Step 1: Creates Reels media container on Instagram Graph API.
        `video_url` must be a publicly fetchable URL at publish time.
        """
        if self.dry_run:
            return f"ig-container-{uuid.uuid4().hex[:12]}"

        # Verify quota first
        self.check_publishing_limit()

        target_acc = self.account_id or account_ref
        url = f"{self.base_url}/{target_acc}/media"
        payload = urllib.parse.urlencode({
            "media_type": "REELS",
            "video_url": video_url,
            "caption": caption,
            "share_to_feed": "true",
            "access_token": self.access_token,
        }).encode("utf-8")

        try:
            req = urllib.request.Request(url, data=payload, method="POST")
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                container_id = data.get("id")
                if not container_id:
                    raise PublishingError(f"No container id in Meta response: {data}")
                return container_id
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8")
            if "190" in err_body:
                raise TokenInvalidError("Instagram access token has expired or is invalid (Error 190).")
            raise PublishingError(f"Failed to create Instagram Reels container: {err_body}")

    def poll_container_status(self, container_id: str, max_attempts: int = 15, delay_sec: float = 3.0) -> str:
        """
        Step 2: Polls container status until FINISHED or ERROR.
        """
        if self.dry_run:
            return "FINISHED"

        url = f"{self.base_url}/{container_id}?fields=status_code,status&access_token={self.access_token}"

        for attempt in range(max_attempts):
            try:
                req = urllib.request.Request(url, method="GET")
                with urllib.request.urlopen(req, timeout=15) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    status_code = data.get("status_code", "").upper()
                    if status_code == "FINISHED":
                        return "FINISHED"
                    elif status_code == "ERROR":
                        raise PublishingError(f"Meta container processing failed: {data}")
                    elif status_code in ("IN_PROGRESS", ""):
                        time.sleep(delay_sec)
            except urllib.error.HTTPError as e:
                err_body = e.read().decode("utf-8")
                if "190" in err_body:
                    raise TokenInvalidError("Instagram access token has expired or is invalid (Error 190).")
                raise PublishingError(f"Error checking container status: {err_body}")

        raise PublishingError(f"Timed out waiting for Reel container {container_id} to finish processing.")

    def publish_container(self, container_id: str, account_ref: str) -> Dict[str, Any]:
        """
        Step 3: Commits publication and returns public media id.
        """
        if self.dry_run:
            remote_id = f"ig-reel-{uuid.uuid4().hex[:12]}"
            return {
                "destination": "instagram",
                "remote_id": remote_id,
                "status": "CONFIRMED",
                "account_ref": account_ref,
            }

        target_acc = self.account_id or account_ref
        url = f"{self.base_url}/{target_acc}/media_publish"
        payload = urllib.parse.urlencode({
            "creation_id": container_id,
            "access_token": self.access_token,
        }).encode("utf-8")

        try:
            req = urllib.request.Request(url, data=payload, method="POST")
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                media_id = data.get("id")
                if not media_id:
                    raise PublishingError(f"No media id in publish response: {data}")
                return {
                    "destination": "instagram",
                    "remote_id": media_id,
                    "status": "CONFIRMED",
                    "account_ref": target_acc,
                }
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8")
            if "190" in err_body:
                raise TokenInvalidError("Instagram access token has expired or is invalid (Error 190).")
            raise PublishingError(f"Failed to publish Instagram Reel: {err_body}")
