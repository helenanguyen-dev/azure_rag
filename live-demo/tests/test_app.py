"""Tests run against a real MCP server (the SDK-built fake) and a scripted OpenAI.

    pip install -r requirements.txt pytest mcp
    pytest tests
"""
import json
import os
import socket
import subprocess
import sys
import time
from types import SimpleNamespace as NS

import pytest

HERE = os.path.dirname(__file__)


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="module", params=["sse", "json"])
def learn_url(request):
    port = free_port()
    proc = subprocess.Popen([sys.executable, os.path.join(HERE, "fake_learn_server.py"), str(port), request.param])
    for _ in range(50):
        try:
            socket.create_connection(("127.0.0.1", port), timeout=0.2).close()
            break
        except OSError:
            time.sleep(0.1)
    yield f"http://127.0.0.1:{port}/mcp"
    proc.terminate()


@pytest.fixture
def client(learn_url, monkeypatch):
    sys.path.insert(0, os.path.dirname(HERE))
    import app as app_module
    from fastapi.testclient import TestClient

    monkeypatch.setattr(app_module, "MCP_URL", learn_url)
    app_module.limiter.__init__()
    return TestClient(app_module.app), app_module


def tool_call(query, id_="call_1", name="microsoft_docs_search"):
    fn = NS(name=name, arguments=json.dumps({"query": query}))
    call = NS(id=id_, type="function", function=fn)
    call.model_dump = lambda: {"id": id_, "type": "function", "function": {"name": name, "arguments": fn.arguments}}
    return call


class ScriptedOpenAI:
    """Plays back model turns and records what the app sent."""

    def __init__(self, turns):
        self.turns = list(turns)
        self.requests = []
        self.chat = NS(completions=NS(create=self.create))

    async def create(self, **kw):
        self.requests.append(kw)
        msg = self.turns.pop(0)
        return NS(choices=[NS(message=msg)])


def test_question_searches_learn_and_cites(client, monkeypatch):
    c, app_module = client
    fake = ScriptedOpenAI([
        NS(content=None, tool_calls=[tool_call("App Service IP restrictions")]),
        NS(content="Use access restrictions. See [IP restrictions](https://learn.microsoft.com/en-us/azure/app-service/app-service-ip-restrictions).", tool_calls=None),
    ])
    monkeypatch.setattr(app_module, "openai_client", lambda: fake)

    r = c.post("/chat", json={"messages": [{"role": "user", "content": "How do I restrict App Service by IP?"}]})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["steps"] == [{"tool": "microsoft_docs_search", "query": "App Service IP restrictions"}]
    assert body["sources"] == [{"title": "Set up Azure App Service access restrictions", "url": "https://learn.microsoft.com/en-us/azure/app-service/app-service-ip-restrictions"}]
    # Only the search tool is offered to the model, and the first turn must search.
    first = fake.requests[0]
    assert [t["function"]["name"] for t in first["tools"]] == ["microsoft_docs_search"]
    assert first["tool_choice"] == "required"
    # The tool result reached the model.
    tool_msgs = [m for m in fake.requests[1]["messages"] if m["role"] == "tool"]
    assert "Networking > Access restriction" in tool_msgs[0]["content"]


def test_search_budget_forces_an_answer(client, monkeypatch):
    c, app_module = client
    fake = ScriptedOpenAI([
        NS(content=None, tool_calls=[tool_call("a", "c1")]),
        NS(content=None, tool_calls=[tool_call("b", "c2")]),
        NS(content="Final answer.", tool_calls=None),
    ])
    monkeypatch.setattr(app_module, "openai_client", lambda: fake)
    r = c.post("/chat", json={"messages": [{"role": "user", "content": "q"}]})
    assert r.status_code == 200
    assert [s["query"] for s in r.json()["steps"]] == ["a", "b"]
    assert fake.requests[-1]["tool_choice"] == "none"
    # No sources cited in the answer, so the top search hits are shown.
    assert len(r.json()["sources"]) == 2


def test_rejects_long_question_and_bad_shape(client):
    c, _ = client
    assert c.post("/chat", json={"messages": [{"role": "user", "content": "x" * 301}]}).status_code == 400
    assert c.post("/chat", json={"messages": [{"role": "assistant", "content": "hi"}]}).status_code == 400
    assert c.post("/chat", json={"messages": []}).status_code == 422


def test_rate_limit_per_minute(client, monkeypatch):
    c, app_module = client
    monkeypatch.setattr(app_module, "openai_client", lambda: ScriptedOpenAI(
        [NS(content=None, tool_calls=[tool_call("x")]), NS(content="ok", tool_calls=None)] * 10))
    codes = [c.post("/chat", json={"messages": [{"role": "user", "content": "q"}]}).status_code for _ in range(6)]
    assert codes == [200] * 5 + [429]


def test_limiter_windows():
    sys.path.insert(0, os.path.dirname(HERE))
    from app import Limiter, PER_DAY
    lim = Limiter()
    t = 1_000_000.0
    for i in range(PER_DAY):
        assert lim.check("v", t + i * 61) is None  # spaced out: never hits the minute limit
    assert "today" in lim.check("v", t + PER_DAY * 61)
    assert lim.check("v", t + 86400 + PER_DAY * 61) is None  # next day


def test_cors_only_allows_the_site(client):
    c, _ = client
    ok = c.options("/chat", headers={"Origin": "https://helenanguyen-dev.github.io", "Access-Control-Request-Method": "POST"})
    bad = c.options("/chat", headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "POST"})
    assert ok.headers.get("access-control-allow-origin") == "https://helenanguyen-dev.github.io"
    assert "access-control-allow-origin" not in bad.headers
