# System Overview — Outlook MCP

## Components

| Component | Role |
|-----------|------|
| `app/mcp_server.py` | FastMCP mail tools + HTTP `/health` |
| `app/services/graph_mail.py` | Microsoft Graph `/me/mailFolders` and `/me/messages` |
| `registry_docs/` | Per-tool Docs for Tool Registry |

Outlook mail is a **separate** MCP host and Azure app from `office365-mcp` (OneDrive/SharePoint/Teams). Vault provider is `outlook`. Matcher tokens: `outlook-mcp`, `outlook`. Tokens for `office365` must not match this host.

## Data flow

1. User Connects Outlook in Studio (Azure app **Weaver Integration Outlook**).
2. Integrations stores tokens under vault provider `outlook`.
3. MCP execute injects `credentials_json` when the tool server is Outlook MCP.
4. Tools call Graph with Mail.Read / Mail.Send / Mail.ReadWrite.

## Risks

- Combining Mail scopes into the files Azure app would expand consent blast radius. Do not merge.
- `list_messages` must not return full bodies.
