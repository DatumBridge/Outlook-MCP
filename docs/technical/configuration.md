# Configuration — Outlook MCP

| Variable | Where | Meaning |
|---|---|---|
| `OUTLOOK_CLIENT_ID` | Integrations | Azure app client id |
| `OUTLOOK_CLIENT_SECRET` | Integrations | Azure app secret |
| `OUTLOOK_TENANT_ID` | Integrations / MCP | Directory; default `OFFICE365_TENANT_ID` or `common` |
| `CREDENTIAL_OAUTH_REDIRECT_URI_OUTLOOK` | Integrations | Optional callback override |
| `OUTLOOK_CREDENTIALS_DIR` | MCP | Bound for `credentials_path` |
| `OUTLOOK_HTTP_TIMEOUT_SEC` | MCP | Graph HTTP timeout (default 60) |
