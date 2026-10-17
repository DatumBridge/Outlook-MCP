# Changelog

## 2026-10-17

### Changed

- **PSS-restricted pod.** Image and Deployment use UID/GID `10001`, non-root, no privilege escalation, read-only root, drop ALL caps, RuntimeDefault seccomp, CPU/memory requests and limits, namespace `mcp-tools`. Rebuild the image and re-apply `outlook-mcp-main.yaml`.

### Added

- `mark_message_read` sets Graph `isRead` after a Weaver mail feed posts the message. Redeploy `outlook-mcp` and republish Outlook MCP / grant the tool. See BR-OUTLOOK-2.

## 2026-10-14

### Added

- Outlook MCP: list/get/send/draft/reply mail via Microsoft Graph on a dedicated Azure app and vault provider `outlook`.
