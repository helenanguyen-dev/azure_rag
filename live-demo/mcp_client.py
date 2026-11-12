"""A small Model Context Protocol (MCP) client over Streamable HTTP.

Written by hand on purpose: v3 is about showing the mechanics that Flowise
hid. An MCP call is three JSON-RPC messages:

1. initialize            -> the server answers with its capabilities
2. notifications/initialized
3. tools/list or tools/call

Servers may answer a POST with plain JSON or with a short Server-Sent Events
stream, so both are handled.
"""

from __future__ import annotations

import itertools
import json
from typing import Any

import httpx

PROTOCOL_VERSION = "2025-03-26"


class MCPError(RuntimeError):
    pass


class MCPClient:
    def __init__(self, url: str, http: httpx.AsyncClient):
        self.url = url
        self.http = http
        self.session_id: str | None = None
        self._ids = itertools.count(1)

    def _headers(self) -> dict[str, str]:
        h = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
        if self.session_id:
            h["Mcp-Session-Id"] = self.session_id
            h["MCP-Protocol-Version"] = PROTOCOL_VERSION
        return h

    async def _post(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        r = await self.http.post(self.url, json=payload, headers=self._headers())
        if r.status_code >= 400:
            raise MCPError(f"MCP server returned HTTP {r.status_code}")
        if sid := r.headers.get("mcp-session-id"):
            self.session_id = sid
        if "id" not in payload:  # a notification: no answer expected
            return None
        ctype = r.headers.get("content-type", "")
        if "text/event-stream" in ctype:
            message = _last_matching_sse(r.text, payload["id"])
        else:
            message = r.json()
        if message is None:
            raise MCPError("MCP server sent no answer")
        if "error" in message:
            raise MCPError(message["error"].get("message", "MCP error"))
        return message["result"]

    async def request(self, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = {"jsonrpc": "2.0", "id": next(self._ids), "method": method}
        if params is not None:
            payload["params"] = params
        result = await self._post(payload)
        assert result is not None
        return result

    async def initialize(self) -> dict[str, Any]:
        result = await self.request(
            "initialize",
            {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": "azure-docs-assistant", "version": "3.0"},
            },
        )
        await self._post({"jsonrpc": "2.0", "method": "notifications/initialized"})
        return result

    async def list_tools(self) -> list[dict[str, Any]]:
        return (await self.request("tools/list")).get("tools", [])

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> str:
        result = await self.request("tools/call", {"name": name, "arguments": arguments})
        text = "\n".join(c.get("text", "") for c in result.get("content", []) if c.get("type") == "text")
        if result.get("isError"):
            raise MCPError(text or "tool failed")
        return text

    async def close(self) -> None:
        if self.session_id:
            try:
                await self.http.delete(self.url, headers=self._headers())
            except httpx.HTTPError:
                pass


def _last_matching_sse(body: str, request_id: int) -> dict[str, Any] | None:
    """Pick the JSON-RPC response with our id out of an SSE body."""
    found = None
    for event in body.replace("\r\n", "\n").split("\n\n"):
        data = "\n".join(line[5:].lstrip() for line in event.split("\n") if line.startswith("data:"))
        if not data:
            continue
        try:
            msg = json.loads(data)
        except json.JSONDecodeError:
            continue
        if isinstance(msg, dict) and msg.get("id") == request_id:
            found = msg
    return found
