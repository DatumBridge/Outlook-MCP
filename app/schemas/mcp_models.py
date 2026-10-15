"""Pydantic models for Outlook MCP tools."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class BaseToolResponse(BaseModel):
    success: bool
    error: Optional[dict] = None


class FolderInfo(BaseModel):
    id: Optional[str] = None
    display_name: Optional[str] = None
    parent_folder_id: Optional[str] = None
    total_item_count: Optional[int] = None
    unread_item_count: Optional[int] = None


class FolderListResponse(BaseToolResponse):
    folders: List[FolderInfo] = Field(default_factory=list)
    next_skip_token: Optional[str] = None


class MessageSummary(BaseModel):
    id: Optional[str] = None
    subject: Optional[str] = None
    from_address: Optional[str] = None
    received_datetime: Optional[str] = None
    is_read: Optional[bool] = None
    body_preview: Optional[str] = None
    conversation_id: Optional[str] = None
    has_attachments: Optional[bool] = None


class MessageListResponse(BaseToolResponse):
    messages: List[MessageSummary] = Field(default_factory=list)
    next_skip_token: Optional[str] = None


class MessageResponse(BaseToolResponse):
    message: Optional[Dict[str, Any]] = None


class SendMessageResponse(BaseToolResponse):
    message: Optional[str] = None


class DraftInfo(BaseModel):
    id: Optional[str] = None
    subject: Optional[str] = None
    to: List[str] = Field(default_factory=list)
    body_preview: Optional[str] = None
    last_modified: Optional[str] = None


class DraftListResponse(BaseToolResponse):
    drafts: List[DraftInfo] = Field(default_factory=list)
    next_skip_token: Optional[str] = None


class DraftResponse(BaseToolResponse):
    draft: Optional[Dict[str, Any]] = None
    message: Optional[str] = None
