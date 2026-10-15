"""Microsoft Graph mail client. Uses a dedicated Outlook Azure app, not OFFICE365_*."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Optional
from urllib.parse import parse_qs, urlparse

import requests

from app.core.exceptions import (
    GraphError,
    GraphValidationError,
    normalize_graph_error,
)

GRAPH_BASE = "https://graph.microsoft.com/v1.0"
DEFAULT_SCOPES = (
    "openid",
    "profile",
    "offline_access",
    "User.Read",
    "Mail.Read",
    "Mail.Send",
    "Mail.ReadWrite",
)
DEFAULT_TIMEOUT_SEC = 60
MAX_BODY_CHARS = 20000
FEED_SELECT = (
    "id,subject,from,receivedDateTime,isRead,bodyPreview,conversationId,hasAttachments"
)
FULL_SELECT = (
    "id,subject,from,toRecipients,ccRecipients,bccRecipients,receivedDateTime,"
    "sentDateTime,isRead,bodyPreview,body,conversationId,hasAttachments,importance"
)


def _request_timeout() -> int:
    raw = os.environ.get("OUTLOOK_HTTP_TIMEOUT_SEC", "").strip()
    if not raw:
        return DEFAULT_TIMEOUT_SEC
    try:
        return max(1, int(raw))
    except ValueError:
        return DEFAULT_TIMEOUT_SEC


def _tenant_id() -> str:
    return (
        os.environ.get("OUTLOOK_TENANT_ID", "").strip()
        or os.environ.get("OFFICE365_TENANT_ID", "common").strip()
        or "common"
    )


def _token_url() -> str:
    return f"https://login.microsoftonline.com/{_tenant_id()}/oauth2/v2.0/token"


def _credentials_dir() -> Path:
    raw = os.environ.get("OUTLOOK_CREDENTIALS_DIR", "").strip()
    if raw:
        return Path(raw).resolve()
    return Path(__file__).resolve().parent.parent.parent


def _is_oauth_creds(creds_dict: dict) -> bool:
    has_access = bool(creds_dict.get("access_token") or creds_dict.get("token"))
    has_refresh = bool(creds_dict.get("refresh_token"))
    return creds_dict.get("type") == "oauth" or has_access or has_refresh


def _resolve_credentials_path(credentials_path: str) -> Path:
    base = _credentials_dir()
    candidate = Path(credentials_path)
    if not candidate.is_absolute():
        candidate = (base / candidate).resolve()
    else:
        candidate = candidate.resolve()
    try:
        candidate.relative_to(base)
    except ValueError as e:
        raise GraphError(
            "credentials_path must be under OUTLOOK_CREDENTIALS_DIR",
            error_code="INVALID_CREDENTIALS",
            retryable=False,
            original_error=e,
        ) from e
    return candidate


def load_credentials_dict(
    credentials_path: Optional[str] = None,
    credentials_json: Optional[str] = None,
) -> dict:
    creds_dict: Optional[dict] = None
    try:
        if credentials_json:
            creds_dict = json.loads(credentials_json)
        elif credentials_path:
            path = _resolve_credentials_path(credentials_path)
            if not path.exists():
                raise GraphError(
                    f"Credentials file not found: {credentials_path}",
                    error_code="CREDENTIALS_REQUIRED",
                    retryable=False,
                )
            with open(path) as f:
                creds_dict = json.load(f)
    except GraphError:
        raise
    except json.JSONDecodeError as e:
        raise GraphError(
            "Invalid credentials JSON",
            error_code="INVALID_CREDENTIALS",
            retryable=False,
            original_error=e,
        ) from e
    except OSError as e:
        raise GraphError(
            "Unable to read credentials file",
            error_code="INVALID_CREDENTIALS",
            retryable=False,
            original_error=e,
        ) from e

    if not creds_dict or not isinstance(creds_dict, dict):
        raise GraphError(
            "Credentials required: provide credentials_path or credentials_json",
            error_code="CREDENTIALS_REQUIRED",
            retryable=False,
        )
    if not _is_oauth_creds(creds_dict):
        raise GraphError(
            "OAuth credentials required. Use Connect Outlook in Integrations.",
            error_code="INVALID_CREDENTIALS",
            retryable=False,
        )
    access = creds_dict.get("access_token") or creds_dict.get("token")
    refresh = creds_dict.get("refresh_token")
    if not access and not refresh:
        raise GraphError(
            "OAuth credentials must include access_token or refresh_token",
            error_code="INVALID_CREDENTIALS",
            retryable=False,
        )
    return creds_dict


def _client_credentials(creds_dict: dict) -> tuple[str, str]:
    client_id = creds_dict.get("client_id") or os.environ.get("OUTLOOK_CLIENT_ID", "")
    client_secret = creds_dict.get("client_secret") or os.environ.get(
        "OUTLOOK_CLIENT_SECRET", ""
    )
    return str(client_id).strip(), str(client_secret).strip()


def scopes_for_refresh(creds_dict: dict) -> list[str]:
    raw = creds_dict.get("scopes") or list(DEFAULT_SCOPES)
    kept: list[str] = []
    seen: set[str] = set()
    for scope in raw:
        name = str(scope).strip()
        if not name or name in seen:
            continue
        seen.add(name)
        kept.append(name)
    return kept or list(DEFAULT_SCOPES)


def refresh_access_token(creds_dict: dict) -> dict:
    refresh_token = creds_dict.get("refresh_token")
    if not refresh_token:
        raise GraphError(
            "No refresh_token available; re-authenticate",
            error_code="AUTH_ERROR",
            retryable=False,
        )
    client_id, client_secret = _client_credentials(creds_dict)
    if not client_id or not client_secret:
        raise GraphError(
            "client_id and client_secret required for token refresh "
            "(in credentials or OUTLOOK_CLIENT_ID/SECRET env)",
            error_code="INVALID_CREDENTIALS",
            retryable=False,
        )
    body = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": " ".join(scopes_for_refresh(creds_dict)),
    }
    try:
        resp = requests.post(_token_url(), data=body, timeout=_request_timeout())
        if resp.status_code >= 400:
            raise normalize_graph_error(
                Exception(resp.text), status_code=resp.status_code
            )
        data = resp.json()
    except GraphError:
        raise
    except requests.RequestException as e:
        raise normalize_graph_error(e) from e

    creds_dict["access_token"] = data.get("access_token")
    creds_dict["token"] = data.get("access_token")
    if data.get("refresh_token"):
        creds_dict["refresh_token"] = data["refresh_token"]
    creds_dict["expires_in"] = data.get("expires_in")
    return creds_dict


def parse_addresses(raw: Optional[str]) -> list[str]:
    if not raw or not str(raw).strip():
        return []
    return [p.strip() for p in str(raw).split(",") if p.strip()]


def recipients_payload(addresses: list[str]) -> list[dict]:
    return [{"emailAddress": {"address": addr}} for addr in addresses]


def skip_token_from_next_link(next_link: Optional[str]) -> Optional[str]:
    if not next_link:
        return None
    parsed = urlparse(next_link)
    qs = parse_qs(parsed.query)
    for key in ("$skiptoken", "skipToken", "$skip"):
        vals = qs.get(key)
        if vals and vals[0]:
            return vals[0]
    return next_link


def _from_address(msg: dict) -> Optional[str]:
    email = ((msg.get("from") or {}).get("emailAddress") or {}).get("address")
    return email


def _recipient_addresses(msg: dict, key: str) -> list[str]:
    out: list[str] = []
    for item in msg.get(key) or []:
        addr = ((item or {}).get("emailAddress") or {}).get("address")
        if addr:
            out.append(addr)
    return out


def summary_from_graph(msg: dict) -> dict:
    return {
        "id": msg.get("id"),
        "subject": msg.get("subject"),
        "from_address": _from_address(msg),
        "received_datetime": msg.get("receivedDateTime"),
        "is_read": msg.get("isRead"),
        "body_preview": msg.get("bodyPreview"),
        "conversation_id": msg.get("conversationId"),
        "has_attachments": msg.get("hasAttachments"),
    }


def detail_from_graph(msg: dict) -> dict:
    body = msg.get("body") or {}
    content = body.get("content") or ""
    truncated = False
    if isinstance(content, str) and len(content) > MAX_BODY_CHARS:
        content = content[:MAX_BODY_CHARS]
        truncated = True
    return {
        "id": msg.get("id"),
        "subject": msg.get("subject"),
        "from_address": _from_address(msg),
        "to": _recipient_addresses(msg, "toRecipients"),
        "cc": _recipient_addresses(msg, "ccRecipients"),
        "received_datetime": msg.get("receivedDateTime"),
        "sent_datetime": msg.get("sentDateTime"),
        "is_read": msg.get("isRead"),
        "conversation_id": msg.get("conversationId"),
        "has_attachments": msg.get("hasAttachments"),
        "importance": msg.get("importance"),
        "body_preview": msg.get("bodyPreview"),
        "body_content_type": body.get("contentType"),
        "body": content,
        "body_truncated": truncated,
    }


def draft_from_graph(msg: dict) -> dict:
    return {
        "id": msg.get("id"),
        "subject": msg.get("subject"),
        "to": _recipient_addresses(msg, "toRecipients"),
        "body_preview": msg.get("bodyPreview"),
        "last_modified": msg.get("lastModifiedDateTime"),
    }


def folder_from_graph(item: dict) -> dict:
    return {
        "id": item.get("id"),
        "display_name": item.get("displayName"),
        "parent_folder_id": item.get("parentFolderId"),
        "total_item_count": item.get("totalItemCount"),
        "unread_item_count": item.get("unreadItemCount"),
    }


class GraphMailService:
    def __init__(
        self,
        credentials_path: Optional[str] = None,
        credentials_json: Optional[str] = None,
    ):
        self._creds = load_credentials_dict(credentials_path, credentials_json)

    def _access_token(self) -> str:
        token = self._creds.get("access_token") or self._creds.get("token")
        if not token:
            self._creds = refresh_access_token(self._creds)
            token = self._creds.get("access_token")
        if not token:
            raise GraphError("Missing access token", error_code="AUTH_ERROR", retryable=True)
        return token

    def _headers(self, content_type: Optional[str] = None) -> dict[str, str]:
        headers = {"Authorization": f"Bearer {self._access_token()}"}
        if content_type:
            headers["Content-Type"] = content_type
        return headers

    def _request(
        self,
        method: str,
        url: str,
        *,
        params: Optional[dict] = None,
        json_body: Optional[dict] = None,
        extra_headers: Optional[dict] = None,
    ) -> Any:
        try:
            headers = self._headers("application/json" if json_body is not None else None)
            if extra_headers:
                headers.update(extra_headers)
            resp = requests.request(
                method,
                url,
                headers=headers,
                params=params,
                json=json_body,
                timeout=_request_timeout(),
            )
            if resp.status_code == 401:
                self._creds = refresh_access_token(self._creds)
                headers = self._headers(
                    "application/json" if json_body is not None else None
                )
                if extra_headers:
                    headers.update(extra_headers)
                resp = requests.request(
                    method,
                    url,
                    headers=headers,
                    params=params,
                    json=json_body,
                    timeout=_request_timeout(),
                )
            if resp.status_code >= 400:
                detail = resp.text[:500] if resp.text else resp.reason
                raise normalize_graph_error(
                    Exception(detail), status_code=resp.status_code
                )
            if resp.status_code == 204 or not resp.content:
                return {}
            return resp.json()
        except GraphError:
            raise
        except requests.RequestException as e:
            raise normalize_graph_error(e) from e

    def list_folders(
        self, page_size: int = 50, skip_token: Optional[str] = None
    ) -> tuple[list[dict], Optional[str]]:
        params: dict[str, Any] = {"$top": max(1, min(page_size, 200))}
        if skip_token:
            params["$skiptoken"] = skip_token
        data = self._request("GET", f"{GRAPH_BASE}/me/mailFolders", params=params)
        items = [folder_from_graph(x) for x in data.get("value") or []]
        return items, skip_token_from_next_link(data.get("@odata.nextLink"))

    def list_messages(
        self,
        folder_id: Optional[str] = None,
        page_size: int = 25,
        skip_token: Optional[str] = None,
        unread_only: bool = False,
        search: Optional[str] = None,
    ) -> tuple[list[dict], Optional[str]]:
        params: dict[str, Any] = {
            "$top": max(1, min(page_size, 50)),
            "$select": FEED_SELECT,
            "$orderby": "receivedDateTime desc",
        }
        extra = None
        if unread_only:
            params["$filter"] = "isRead eq false"
        if search and search.strip():
            params["$search"] = f'"{search.strip()}"'
            extra = {"ConsistencyLevel": "eventual"}
            params.pop("$orderby", None)
        if skip_token:
            params["$skiptoken"] = skip_token
        if folder_id and folder_id.strip():
            url = f"{GRAPH_BASE}/me/mailFolders/{folder_id.strip()}/messages"
        else:
            url = f"{GRAPH_BASE}/me/messages"
        data = self._request("GET", url, params=params, extra_headers=extra)
        items = [summary_from_graph(x) for x in data.get("value") or []]
        return items, skip_token_from_next_link(data.get("@odata.nextLink"))

    def get_message(self, message_id: str) -> dict:
        mid = (message_id or "").strip()
        if not mid:
            raise GraphValidationError("message_id is required")
        data = self._request(
            "GET",
            f"{GRAPH_BASE}/me/messages/{mid}",
            params={"$select": FULL_SELECT},
        )
        return detail_from_graph(data)

    def send_message(
        self,
        to: str,
        subject: str,
        body: str,
        cc: Optional[str] = None,
        content_type: str = "Text",
    ) -> None:
        tos = parse_addresses(to)
        if not tos:
            raise GraphValidationError("to is required (comma-separated addresses)")
        if not (subject or "").strip():
            raise GraphValidationError("subject is required")
        ct = "HTML" if (content_type or "").lower() == "html" else "Text"
        payload = {
            "message": {
                "subject": subject.strip(),
                "body": {"contentType": ct, "content": body or ""},
                "toRecipients": recipients_payload(tos),
            },
            "saveToSentItems": True,
        }
        ccs = parse_addresses(cc)
        if ccs:
            payload["message"]["ccRecipients"] = recipients_payload(ccs)
        self._request("POST", f"{GRAPH_BASE}/me/sendMail", json_body=payload)

    def create_draft(
        self,
        to: str,
        subject: str,
        body: str,
        cc: Optional[str] = None,
        content_type: str = "Text",
    ) -> dict:
        tos = parse_addresses(to)
        if not tos:
            raise GraphValidationError("to is required (comma-separated addresses)")
        if not (subject or "").strip():
            raise GraphValidationError("subject is required")
        ct = "HTML" if (content_type or "").lower() == "html" else "Text"
        payload = {
            "subject": subject.strip(),
            "body": {"contentType": ct, "content": body or ""},
            "toRecipients": recipients_payload(tos),
        }
        ccs = parse_addresses(cc)
        if ccs:
            payload["ccRecipients"] = recipients_payload(ccs)
        data = self._request("POST", f"{GRAPH_BASE}/me/messages", json_body=payload)
        return draft_from_graph(data)

    def list_drafts(
        self, page_size: int = 25, skip_token: Optional[str] = None
    ) -> tuple[list[dict], Optional[str]]:
        params: dict[str, Any] = {
            "$top": max(1, min(page_size, 50)),
            "$select": "id,subject,toRecipients,bodyPreview,lastModifiedDateTime",
            "$orderby": "lastModifiedDateTime desc",
        }
        if skip_token:
            params["$skiptoken"] = skip_token
        data = self._request(
            "GET", f"{GRAPH_BASE}/me/mailFolders/drafts/messages", params=params
        )
        items = [draft_from_graph(x) for x in data.get("value") or []]
        return items, skip_token_from_next_link(data.get("@odata.nextLink"))

    def get_draft(self, draft_id: str) -> dict:
        did = (draft_id or "").strip()
        if not did:
            raise GraphValidationError("draft_id is required")
        data = self._request(
            "GET",
            f"{GRAPH_BASE}/me/messages/{did}",
            params={"$select": FULL_SELECT},
        )
        return detail_from_graph(data)

    def send_draft(self, draft_id: str) -> None:
        did = (draft_id or "").strip()
        if not did:
            raise GraphValidationError("draft_id is required")
        self._request("POST", f"{GRAPH_BASE}/me/messages/{did}/send")

    def reply_message(
        self, message_id: str, comment: str, reply_all: bool = False
    ) -> None:
        mid = (message_id or "").strip()
        if not mid:
            raise GraphValidationError("message_id is required")
        if comment is None or not str(comment).strip():
            raise GraphValidationError("comment is required")
        path = "replyAll" if reply_all else "reply"
        self._request(
            "POST",
            f"{GRAPH_BASE}/me/messages/{mid}/{path}",
            json_body={"comment": str(comment)},
        )
