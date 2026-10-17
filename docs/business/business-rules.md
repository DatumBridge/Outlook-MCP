# Business rules — Outlook MCP

## BR-OUTLOOK-1 — Separate Azure app

Outlook mail Connect is not Microsoft 365 files Connect. Operators register a second Azure app. Users Connect Outlook separately.

## BR-OUTLOOK-2 — Feed vs body

`list_messages` is a feed. Full body is only on `get_message` / `get_draft`, truncated. After Weaver posts a feed item, `mark_message_read` sets Graph `isRead` so the next unread poll does not list it again. Omit folder and the feed uses Inbox.

## BR-OUTLOOK-3 — Confirm send

`send_message`, `send_draft`, and `reply_message` do nothing unless `confirm=true`.
