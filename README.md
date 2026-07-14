# Azure Docs RAG Assistant

A retrieval-augmented generation (RAG) assistant that answers architecture and configuration questions grounded in official Microsoft Azure documentation — built as an elevated iteration of an earlier Langflow-based RAG prototype, now implemented in Flowise with a curated knowledge base, retrieval evaluation, and responsible-AI guardrails.

## Why this project

This is a follow-up to an earlier RAG prototype ("RAG-Based Product Insight Assistant," built in Langflow) that converted raw customer/PM inputs into structured PRDs. That version proved the core RAG pattern but had a thin, single-purpose knowledge base and no formal retrieval evaluation.

This version is deliberately scoped differently: instead of a generic "chat with your docs" demo, it's grounded in the same Azure services used in a separate cloud architecture project (Cloud9 streaming platform migration) — App Service, Blob Storage, Azure Front Door, Virtual Network, RBAC, and Security. The goal is a coherent, defensible artifact: a RAG assistant that can answer real architecture questions about the exact services already designed and documented elsewhere in this portfolio.

## What's "elevated" vs. the v1 prototype

| Area | v1 (Langflow) | v2 (this repo) |
|---|---|---|
| Knowledge base | Ad hoc customer input snippets | 127 curated documents from Microsoft's official open-source Azure documentation (CC BY 4.0), spanning 6 services |
| Retrieval | Default chunking, no evaluation | Deliberate chunking strategy + retrieval quality evaluation (see `eval/`) |
| Guardrails | Basic prompt-injection mitigation | Documented hallucination checks, source-citation requirements, and human-in-the-loop review checkpoints |
| Interface | None (pipeline only) | Embeddable chat widget via Flowise |
| Tooling | Langflow (deprecated in this project) | Flowise |

## Planned v3

A from-scratch Python/LangChain implementation of the same pipeline, to demonstrate the underlying mechanics that Flowise abstracts away (custom chunking logic, retrieval evaluation harness, prompt engineering without a visual builder).

## Data

See [`data/SOURCES.md`](data/SOURCES.md) for the full manifest and license attribution. In short: all source documents are pulled from [`MicrosoftDocs/azure-docs`](https://github.com/MicrosoftDocs/azure-docs), Microsoft's official open-source Azure documentation repository, licensed CC BY 4.0. No modifications were made to source text.

## Architecture

See [`docs/architecture.md`](docs/architecture.md) for the full pipeline design, chunking strategy, and retrieval configuration.

## Evaluation

See [`eval/eval-notes.md`](eval/eval-notes.md) for retrieval quality testing methodology, known limitations, and guardrail design.

## Status

🚧 In progress — knowledge base curated, architecture designed. Flowise flow build and evaluation in progress.
