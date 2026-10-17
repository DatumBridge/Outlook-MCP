# Deployment — Outlook MCP

Image `outlook-mcp:local` (or Harbor tag). Runs as UID/GID `10001`. Service `outlook-mcp-main` in namespace `mcp-tools`.

Apply `k8s/mcp-channel-tools/outlook-mcp-main.yaml` via `publish.sh`. Repo `mcp/outlook-mcp/k8s/deployment.yaml` must stay PSS-restricted so scanners do not see a default-namespace root stub.

Integrations must have `OUTLOOK_CLIENT_ID` and `OUTLOOK_CLIENT_SECRET`. Optional `OUTLOOK_TENANT_ID` (falls back to `OFFICE365_TENANT_ID` then `common`).
