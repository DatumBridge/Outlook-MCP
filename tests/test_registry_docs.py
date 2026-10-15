"""Outlook tool guides must match tools and error codes."""

from __future__ import annotations

import ast
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.capability_bind import registry_docs  # noqa: E402
from app.core.exceptions import DOCUMENTED_ERROR_CODES  # noqa: E402

DOCS = ROOT / "registry_docs"
SERVER = ROOT / "app" / "mcp_server.py"


def mcp_tool_names() -> list[str]:
    tree = ast.parse(SERVER.read_text(encoding="utf-8"))
    names = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for dec in node.decorator_list:
            target = dec.func if isinstance(dec, ast.Call) else dec
            if isinstance(target, ast.Attribute) and target.attr == "tool":
                names.append(node.name)
                break
    return names


class RegistryDocsTest(unittest.TestCase):
    def test_guides_match_mcp_tools_and_error_ssot(self):
        tools = mcp_tool_names()
        self.assertTrue(tools)
        codes = [code for code, _ in DOCUMENTED_ERROR_CODES]
        self.assertIn("GRAPH_ERROR", codes)
        for name in tools:
            path = DOCS / f"{name}.md"
            self.assertTrue(path.is_file(), f"missing {path}")
            text = path.read_text(encoding="utf-8")
            bound = registry_docs(name)
            self.assertEqual(bound, text.strip())
            self.assertIn(f"# {name}", text)
            self.assertIn("| Name | Required | Type | Sample | Meaning |", text)
            self.assertIn("## Error codes", text)
            self.assertIn("## Cases", text)
            self.assertIn("error_code", text)
            self.assertIn("When to call", text)
            self.assertIn("untrusted", text.lower())
            self.assertIn("Do not invent a token", text)
            self.assertNotIn('"credentials_json"', text.split("## Cases", 1)[1])
            self.assertLessEqual(len(text), 24000)
            for code in codes:
                self.assertIn(f"`{code}`", text, f"{name} missing {code}")

    def test_list_messages_is_feed_not_body(self):
        text = (DOCS / "list_messages.md").read_text(encoding="utf-8")
        self.assertIn("body_preview", text)
        self.assertIn("get_message", text)
        self.assertIn("do not include `body`", text.lower())


if __name__ == "__main__":
    unittest.main()
