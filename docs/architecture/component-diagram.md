# Component diagram — Outlook MCP

```text
Studio Connect Outlook
  → Integrations OAuth (OUTLOOK_CLIENT_ID)
  → vault provider outlook
  → MCP inject credentials_json
  → outlook-mcp Graph mail tools
```

Microsoft 365 Connect (`OFFICE365_CLIENT_*`, provider `office365`) does not inject into this host.
