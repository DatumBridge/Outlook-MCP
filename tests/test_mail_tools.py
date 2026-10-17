"""Outlook MCP mail tool guards (no Graph network)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.services.graph_mail import (  # noqa: E402
    filter_unread_feed,
    graph_message_url,
    parse_addresses,
    parse_message_id_list,
    skip_token_from_next_link,
    summary_from_graph,
)


class MailShapeTest(unittest.TestCase):
    def test_filter_unread_feed_drops_read(self):
        rows = [
            {"id": "a", "is_read": False},
            {"id": "b", "is_read": True},
            {"id": "c"},
        ]
        got = filter_unread_feed(rows, True)
        self.assertEqual([r["id"] for r in got], ["a", "c"])

    def test_parse_message_id_list(self):
        self.assertEqual(parse_message_id_list("a,b"), ["a", "b"])
        self.assertEqual(parse_message_id_list([{"id": "x"}, {"message_id": "y"}]), ["x", "y"])
        self.assertEqual(
            parse_message_id_list("id-1,id-2", None, [{"id": "id-2"}, {"id": "id-3"}]),
            ["id-1", "id-2", "id-3"],
        )

    def test_graph_message_url_encodes_id(self):
        url = graph_message_url("AAMkAGI+abc=")
        self.assertIn("/me/messages/AAMkAGI%2Babc%3D", url)

    def test_parse_addresses(self):
        self.assertEqual(parse_addresses("a@b.com, c@d.com"), ["a@b.com", "c@d.com"])
        self.assertEqual(parse_addresses(""), [])

    def test_skip_token(self):
        link = "https://graph.microsoft.com/v1.0/me/messages?$skiptoken=abc"
        self.assertEqual(skip_token_from_next_link(link), "abc")

    def test_summary_omits_body(self):
        row = summary_from_graph(
            {
                "id": "1",
                "subject": "Hi",
                "from": {"emailAddress": {"address": "user@example.com"}},
                "receivedDateTime": "2026-10-14T00:00:00Z",
                "isRead": False,
                "bodyPreview": "Please",
                "body": {"contentType": "Text", "content": "full body must not leak"},
            }
        )
        self.assertNotIn("body", row)
        self.assertEqual(row["body_preview"], "Please")
        self.assertEqual(row["from_address"], "user@example.com")


class ToolGuardTest(unittest.TestCase):
    def test_confirm_and_creds_helpers_in_source(self):
        src = (ROOT / "app" / "mcp_server.py").read_text(encoding="utf-8")
        self.assertIn('error_code": "CONFIRM_REQUIRED"', src)
        self.assertIn("if not confirm:", src)
        self.assertIn("Set confirm=true", src)
        self.assertIn("CREDENTIALS_REQUIRED", src)
        self.assertIn("parse_message_id_list(message_id, message_ids, messages)", src)

    def test_send_paths_require_confirm_in_source(self):
        src = (ROOT / "app" / "mcp_server.py").read_text(encoding="utf-8")
        for name in ("def send_message", "def send_draft", "def reply_message"):
            self.assertIn(name, src)


if __name__ == "__main__":
    unittest.main()
