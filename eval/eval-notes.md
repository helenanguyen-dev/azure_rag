# Evaluation & Guardrails

This document tracks retrieval quality testing and responsible-AI guardrails — the two things flagged as gaps in the v1 (Langflow) prototype's "Key Limitations" slide (limited training knowledge base, retrieval quality, limited guardrail/routing components).

## Retrieval evaluation methodology

For each of the 6 service areas, a small set of test questions with known-correct source documents will be run against the retriever, and precision/recall assessed manually:

1. Write 3-5 test questions per service (18-30 total) where the correct answer is verifiably contained in a specific source document (e.g., "What's the difference between App Service Environment v3 and the multitenant offering?" → should retrieve `app-service/environment/overview.md`).
2. For each question, log: which chunks were retrieved (top-5), whether the correct source document appeared in the top-5, and whether the generated answer actually used that source correctly (vs. hallucinating from general knowledge).
3. Track a simple retrieval hit-rate metric: (# questions where correct source was retrieved) / (total questions).

*Status: methodology defined, test questions and results to be filled in after the Flowise flow is built.*

## Guardrails

Carried forward and made more explicit than in v1:

- **Grounding constraint**: system prompt instructs the model to answer only from retrieved context and explicitly say when a question falls outside the knowledge base (e.g., an AKS question, which isn't in this corpus) rather than answering from general training knowledge. This directly addresses the "risk of outdated or incomplete knowledge sources" limitation named in the v1 presentation.
- **Source citation**: every answer should reference which document(s) it drew from, so a user can verify against the original Microsoft doc rather than trusting the generated summary blindly.
- **Human-in-the-loop framing**: consistent with the v1 recommendation, this tool is positioned as a decision-support / drafting aid, not an authoritative source — same "Go, phased implementation, not full automation" conclusion as the original project.
- **Bias/staleness awareness**: because the corpus is a snapshot pulled in July 2026, answers may not reflect Azure feature changes after that date. This is a known limitation, not something the guardrails can fully solve — documented here rather than hidden.

## What's intentionally out of scope for this version

- No automated eval framework (e.g., RAGAS) — manual evaluation only, given portfolio-project scope and timeline.
- No red-teaming for prompt injection beyond the basic mitigation carried from v1.
