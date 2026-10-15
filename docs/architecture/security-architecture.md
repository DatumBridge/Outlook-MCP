# Security — Outlook MCP

- Separate Azure application from Microsoft 365 files. Mail.Read, Mail.Send, Mail.ReadWrite, User.Read, offline_access only.
- Tokens live in the Integrations vault (`outlook`). MCP logs must not print access or refresh tokens.
- Send/reply/send_draft require `confirm=true`.
- Email body is untrusted input. Guides tell Deep not to follow instructions in mail.
- Path credentials must stay under `OUTLOOK_CREDENTIALS_DIR`.
