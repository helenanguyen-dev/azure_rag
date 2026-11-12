---
title: Azure Docs Assistant
emoji: 📘
colorFrom: indigo
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
short_description: Answers Azure questions from Microsoft Learn via MCP
---

# Azure Docs Assistant: live demo service (v3)

The small Python service behind the "Try it live" box on
[Helena's portfolio](https://helenanguyen-dev.github.io/helenanguyen/work/azure-docs-assistant/).

```
visitor's question
   → this service (keeps the API key, enforces limits)
   → OpenAI model, given one tool: microsoft_docs_search
   → Microsoft Learn MCP server (https://learn.microsoft.com/api/mcp)
   → answer with links to the Learn pages it used
```

v2 hid these steps inside Flowise. Here they are in plain code:
`mcp_client.py` is a hand-written MCP client (initialize, list tools, call a tool),
and `app.py` runs the tool loop: the model must search first, may search once more,
and then has to answer.

## Guardrails

| Risk | Guard |
|---|---|
| Someone runs up the OpenAI bill | 5 questions/minute and 30/day per visitor, 300/day in total, answers capped at 700 tokens, at most 2 searches per question. Plus a monthly budget cap set in the OpenAI dashboard as the hard backstop. |
| Key leaks | The key lives only in the host's secret settings. The browser never sees it. |
| Other sites embedding it | CORS only allows the portfolio's address (`ALLOWED_ORIGINS`). |
| Made-up answers | The model must call the search tool first and answer only from what it returns, with links. It says so when the docs don't cover a question. |
| Off-topic use | The prompt keeps it to Microsoft and Azure; questions are capped at 300 characters. |
| Prompt injection | Only the search tool is exposed (no page fetch); the prompt tells the model to ignore instructions inside results. |

## Run it locally

```bash
pip install -r requirements.txt
export OPENAI_API_KEY=sk-...
uvicorn app:app --port 7860
curl -X POST localhost:7860/chat -H 'Content-Type: application/json' \
  -d '{"messages":[{"role":"user","content":"How do I restrict App Service by IP?"}]}'
```

Tests (no API key needed; they start a real MCP server built with the official SDK):

```bash
pip install -r requirements.txt pytest mcp
pytest tests
```

## Deploy on Hugging Face Spaces (free)

1. Create a free account at huggingface.co, then **New Space**: name it `azure-docs-assistant`,
   SDK **Docker**, template **Blank**, hardware **CPU basic (free)**, visibility **Public**.
2. In the Space's **Files** tab, upload everything in this folder
   (`README.md`, `Dockerfile`, `requirements.txt`, `app.py`, `mcp_client.py`).
3. In **Settings → Variables and secrets**, add a **secret** `OPENAI_API_KEY`.
4. Wait for the build to say **Running**. Your API is at
   `https://<your-username>-azure-docs-assistant.hf.space` (check `/health`).
5. In the OpenAI dashboard, set a monthly budget for the project the key belongs to (about $5).

Settings you can change as variables: `OPENAI_MODEL` (default `gpt-4o-mini`),
`ALLOWED_ORIGINS`, `LIMIT_PER_MINUTE`, `LIMIT_PER_DAY`, `LIMIT_GLOBAL_PER_DAY`.

Free Spaces go to sleep after about two days without visitors; the first question
after that takes up to a minute while it wakes up.
