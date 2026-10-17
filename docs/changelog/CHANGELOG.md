# Changelog

## 2026-10-18

### Fixed

- **`mark_messages_read` / `mark_message_read` accept `{id}` rows on `message_ids`.** FastMCP no longer rejects a list (Weaver Feeding Email bind). An empty page returns success and does not call Graph.

## 2026-10-17

### Changed

- **`mark_messages_read`** marks a page of Graph ids after a Weaver catalog feed (array in, not foreach).
- **Graph message URLs are encoded** so `mark_message_read` PATCH reaches ids that contain `+` or `=`.
- **PSS-restricted pod.** Image and Deployment use UID/GID `10001`, non-root, no privilege escalation, read-only root, drop ALL caps, RuntimeDefault seccomp, CPU/memory requests and limits, namespace `mcp-tools`. Rebuild the image and re-apply `outlook-mcp-main.yaml`.

### Added

- `mark_message_read` sets Graph `isRead` after a Weaver mail feed posts the message. Redeploy `outlook-mcp` and republish Outlook MCP. See BR-OUTLOOK-2.

## 2026-10-14

### Added

- Outlook MCP: list/get/send/draft/reply mail via Microsoft Graph on a dedicated Azure app and vault provider `outlook`.
