# Architecture

## Pipeline overview

```
Markdown docs (data/sources/)
        │
        ▼
Document Loader (Flowise: "Text File" / "Markdown" loader, one per service folder)
        │
        ▼
Text Splitter — Markdown-aware recursive splitter
   (chunk_size ≈ 800 tokens, overlap ≈ 100 tokens)
        │
        ▼
Embeddings model (e.g., OpenAI text-embedding-3-small, or a local
sentence-transformers model if avoiding API cost)
        │
        ▼
Vector Store (Chroma — self-hosted, no external service dependency)
   metadata tagged per chunk: {service, filename, title}
        │
        ▼
Retriever (top-k = 5, similarity threshold filtering)
        │
        ▼
Conversational Retrieval Chain
   — system prompt enforces: answer only from retrieved context,
     cite the source filename/title, say "not covered in the
     knowledge base" if retrieval doesn't support an answer
        │
        ▼
Chat model (e.g., GPT-4o-mini or Claude Haiku via API)
        │
        ▼
Embeddable chat widget (Flowise built-in)
```

## Why a markdown-aware splitter (not naive fixed-length)

Azure docs are structured with headers (`##`, `###`) that mark logical sections — e.g., "Overview," "Networking considerations," "Security recommendations" within a single App Service doc. A naive fixed-length splitter would cut mid-section and lose that structure, degrading retrieval precision (a chunk that's half of "Networking" and half of "Security" answers neither question well). A markdown-aware splitter that respects header boundaries keeps each chunk topically coherent, which matters more here than in v1's unstructured customer-input use case.

## Why metadata tagging by service

Tagging each chunk with its source service (`app-service`, `blob-storage`, `front-door`, `virtual-network`, `rbac`, `security`) enables filtered retrieval — e.g., a question specifically about "App Service networking" can be scoped to the `app-service` + `virtual-network` chunks rather than searching the full 127-document corpus indiscriminately. This is one of the concrete "retrieval quality" improvements over v1, which had no metadata filtering (a limitation explicitly called out in the v1 presentation).

## Known limitations (carried forward transparently from v1)

- **Retrieval quality** still depends on chunking and embedding choices; some cross-service questions (e.g., "how does App Service networking interact with a VNet") may retrieve relevant chunks from both folders but the chain has to synthesize across them, which is harder than single-topic retrieval.
- **Knowledge base is a curated subset**, not the full Azure documentation — questions about AKS, Azure SQL, Cosmos DB, or Entra ID are out of scope for this version (documented in README as a planned v2 expansion).
- **No agentic routing** — this is a single retrieval chain, not a multi-agent system that could decide which sub-index to query.

## Flowise-specific implementation notes

- Use separate Document Loader nodes per service subfolder (or one loader over `data/sources/` recursively, with a Function node to tag metadata by parent folder name).
- Chroma is chosen over a hosted vector DB (Pinecone/Weaviate) to keep this fully self-hostable and free to run, consistent with the "portfolio project, not production system" scope.
- The embeddable chat widget is exported as part of the Flowise flow JSON in `flows/`.
