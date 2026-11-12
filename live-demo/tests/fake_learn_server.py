"""A stand-in for the Microsoft Learn MCP server, built with the official MCP SDK.

Used to check that our hand-written client speaks real MCP. Run:
    python tests/fake_learn_server.py 8765
"""
import json
import sys

import uvicorn
from mcp.server.mcpserver import MCPServer

server = MCPServer("fake-learn")


@server.tool()
def microsoft_docs_search(query: str) -> str:
    """Search official Microsoft/Azure documentation."""
    return json.dumps([
        {
            "title": "Set up Azure App Service access restrictions",
            "content": f"Excerpt about {query}: add allow rules by IP address range in Networking > Access restriction.",
            "contentUrl": "https://learn.microsoft.com/en-us/azure/app-service/app-service-ip-restrictions",
        },
        {
            "title": "Azure App Service overview",
            "content": "App Service is an HTTP-based service for hosting web applications.",
            "contentUrl": "https://learn.microsoft.com/en-us/azure/app-service/overview",
        },
    ])


@server.tool()
def microsoft_docs_fetch(url: str) -> str:
    """Fetch a whole page (the demo must not expose this one)."""
    return "full page"


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
    json_mode = len(sys.argv) > 2 and sys.argv[2] == "json"
    uvicorn.run(server.streamable_http_app(json_response=json_mode), host="127.0.0.1", port=port, log_level="warning")
