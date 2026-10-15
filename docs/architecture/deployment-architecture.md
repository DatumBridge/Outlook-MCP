# Deployment — Outlook MCP

Image `outlook-mcp:local` (or Harbor tag). Service `outlook-mcp-main` in namespace `mcp-tools`.

Apply `k8s/mcp-channel-tools/outlook-mcp-main.yaml` via `publish.sh`.

Integrations must have `OUTLOOK_CLIENT_ID` and `OUTLOOK_CLIENT_SECRET`. Optional `OUTLOOK_TENANT_ID` (falls back to `OFFICE365_TENANT_ID` then `common`).
