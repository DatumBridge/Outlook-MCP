# API — Outlook MCP

HTTP: `GET /health` → `{"status":"ok","service":"outlook-mcp"}`.

MCP tools: `list_folders`, `list_messages`, `get_message`, `mark_message_read`, `send_message`, `create_draft`, `list_drafts`, `get_draft`, `send_draft`, `reply_message`.

Auth: `credentials_json` (vault inject) or `credentials_path`.

Graph: `https://graph.microsoft.com/v1.0/me/mailFolders`, `/me/messages`, `/me/sendMail`.
