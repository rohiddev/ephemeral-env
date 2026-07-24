# Enterprise RAG Agent — AWS Architecture
### Internal Employee Q&A Platform

---

## 1. Overview

This document describes the architecture for an enterprise-grade Retrieval-Augmented Generation (RAG) 
agent deployed on AWS. The system enables employees to query internal knowledge bases — HR policies, IT runbooks, compliance docs, engineering wikis, SOPs — using natural language, and receive grounded, cited answers backed by authoritative internal sources.

---

## 2. Design Principles

| Principle | Rationale |
|---|---|
| **Grounded answers only** | LLM responses anchored to retrieved documents; reduces hallucination |
| **Source-cited responses** | Every answer references the document chunk it was derived from |
| **Zero trust on data access** | IAM + attribute-based access control; employees only see docs they're authorized for |
| **Serverless-first** | Minimize ops overhead; scale to zero when idle |
| **Audit trail** | Every query/response logged for compliance and continuous improvement |
| **Federated ingestion** | Documents ingested from multiple enterprise sources (SharePoint, Confluence, S3, ServiceNow) |

---

## 3. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Employee Layer                           │
│  Web App / Slack Bot / MS Teams Bot / Internal Portal           │
└───────────────────────────┬─────────────────────────────────────┘
                            │ HTTPS
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    API Gateway + Cognito                         │
│   (Auth, throttling, WAF, route to Lambda or ECS)              │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Orchestration Layer                           │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │             RAG Orchestrator (Lambda / ECS Fargate)      │  │
│  │                                                          │  │
│  │  1. Query rewriting / intent classification              │  │
│  │  2. Hybrid retrieval (semantic + keyword)                │  │
│  │  3. Context assembly + prompt construction               │  │
│  │  4. LLM call (Bedrock)                                   │  │
│  │  5. Citation injection + response formatting             │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────┬────────────────────────────────┬────────────────────────┘
         │                                │
         ▼                                ▼
┌─────────────────┐            ┌──────────────────────┐
│  Knowledge      │            │   Amazon Bedrock      │
│  Store Layer    │            │                       │
│                 │            │  - Claude 3.x (Q&A)   │
│  OpenSearch     │            │  - Titan Embeddings   │
│  Serverless     │            │  - (optional) Guardr. │
│  (vector +      │            └──────────────────────┘
│   BM25 hybrid)  │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Ingestion Pipeline                         │
│                                                                 │
│  Sources → S3 Raw Bucket → Lambda/Glue ETL → Chunker →         │
│  Bedrock Titan Embeddings → OpenSearch Index + S3 Processed     │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. Component Breakdown

### 4.1 Frontend / Entry Points

Employees interact via one or more of:

- **React Web App** — hosted on S3 + CloudFront; connects via API Gateway
- **Slack Bot** — AWS Lambda handles Slack Events API; posts answers as threaded replies with source links
- **MS Teams Bot** — Azure Bot Framework connector calling the same API Gateway endpoint
- **Internal Portal Widget** — embeddable JS widget for existing intranet

All entry points are stateless — session context managed in DynamoDB (conversation history per user/session).

---

### 4.2 Authentication & Authorization

| Component | Role |
|---|---|
| **Amazon Cognito** | Employee SSO via SAML/OIDC federation with corporate IdP (Okta, Azure AD) |
| **JWT Claims** | User's department, role, clearance level encoded in token |
| **API Gateway Authorizer** | Lambda validates JWT; passes user context downstream |
| **OpenSearch Document ACLs** | Each document chunk tagged with `allowed_groups[]`; retrieval query filtered by user's group memberships at runtime |

This ensures a Finance employee cannot retrieve IT infrastructure runbooks marked for the SRE group only.

---

### 4.3 Orchestration Layer (RAG Orchestrator)

The core orchestration runs in **Lambda** for light queries or **ECS Fargate** for longer-running agentic flows.

**Step-by-step flow:**

```
1. RECEIVE query from API Gateway
        │
2. QUERY REWRITING
   └─ LLM call (Bedrock) to decompose multi-part questions,
      resolve pronouns, expand abbreviations
        │
3. HYBRID RETRIEVAL
   ├─ Semantic search: embed query via Bedrock Titan Embeddings
   │   → kNN vector search in OpenSearch
   └─ Keyword search: BM25 on OpenSearch full-text index
   └─ RRF merge (Reciprocal Rank Fusion) to combine both result sets
        │
4. RE-RANKING (optional)
   └─ Cohere Rerank via Bedrock or cross-encoder Lambda
      to score top-k chunks by relevance to query
        │
5. CONTEXT ASSEMBLY
   └─ Top N chunks (configurable, default 5) assembled into prompt
      with metadata: source doc name, section, last updated, author
        │
6. LLM GENERATION (Bedrock - Claude 3 Sonnet/Haiku)
   └─ System prompt instructs: "Answer only from provided context.
      If answer not found, say so. Cite source for each claim."
        │
7. CITATION INJECTION
   └─ Parse LLM output, append source links to S3/Confluence/SharePoint
        │
8. RETURN response + sources + confidence signal to caller
        │
9. LOG to CloudWatch + DynamoDB audit trail
```

---

### 4.4 Knowledge Store — Amazon OpenSearch Serverless

Two index types, queried simultaneously:

| Index | Purpose |
|---|---|
| **Vector index** | Stores 1536-dim Titan embeddings per chunk; supports kNN similarity search |
| **Text index** | Standard BM25 full-text index on raw chunk content; catches exact keyword matches |

**Document metadata stored per chunk:**

```json
{
  "chunk_id": "hr-policy-pto-v3-chunk-12",
  "source_doc_id": "hr-policy-pto-v3",
  "source_system": "confluence",
  "source_url": "https://wiki.company.com/display/HR/PTO+Policy",
  "section_title": "Carryover Rules",
  "last_updated": "2025-11-01",
  "allowed_groups": ["all-employees"],
  "content": "Employees may carry over up to 5 days of unused PTO...",
  "embedding": [0.021, -0.043, ...]
}
```

---

### 4.5 Ingestion Pipeline

Runs on a scheduled basis (EventBridge) and on-demand (S3 event triggers).

```
Source Systems                  AWS Ingestion
─────────────                   ─────────────
SharePoint Online  ──────────►  Lambda Connector (Graph API)
Confluence Cloud   ──────────►  Lambda Connector (REST API)       ┐
ServiceNow         ──────────►  Lambda Connector (Table API)      ├─► S3 Raw Bucket
Internal S3 Docs   ──────────►  Direct copy                       │   (per source prefix)
HR System PDFs     ──────────►  S3 Event trigger                  ┘
                                          │
                                          ▼
                                 AWS Glue / Lambda ETL
                                 ┌─────────────────────┐
                                 │ 1. Extract text      │
                                 │    (PDF→Textract,    │
                                 │     HTML→BeautifulS) │
                                 │ 2. Chunk (512 tokens,│
                                 │    20% overlap)      │
                                 │ 3. Add metadata      │
                                 │ 4. Embed via Bedrock │
                                 │    Titan Embeddings  │
                                 │ 5. Upsert to         │
                                 │    OpenSearch        │
                                 │ 6. Archive to S3     │
                                 │    Processed bucket  │
                                 └─────────────────────┘
```

**Chunking strategy:**

- Default: 512 tokens, 20% overlap (102 token stride)
- Hierarchical chunking for long structured docs: parent chunk (2048 tokens) stored for context, child chunks (256 tokens) used for retrieval
- Tables extracted as standalone chunks with surrounding context prepended

---

### 4.6 Amazon Bedrock

| Use | Model |
|---|---|
| **Embeddings** | Amazon Titan Embeddings V2 (1536 dims) |
| **Q&A Generation** | Anthropic Claude 3 Haiku (fast, cheap) or Claude 3 Sonnet (higher quality) |
| **Query Rewriting** | Claude 3 Haiku (low latency) |
| **Guardrails** | Bedrock Guardrails — PII redaction, topic deny list, grounding checks |

Bedrock is invoked via the AWS SDK from the orchestrator Lambda/ECS task. No model hosting required.

---

### 4.7 Data Stores

| Store | Use |
|---|---|
| **S3 (Raw)** | Original source documents, immutable |
| **S3 (Processed)** | Chunked, cleaned text + chunk metadata JSON |
| **OpenSearch Serverless** | Vector + BM25 index, real-time retrieval |
| **DynamoDB** | Conversation history (session_id → message list), query audit log |
| **Parameter Store / Secrets Manager** | API keys for source connectors, config |

---

### 4.8 Observability

| Layer | Tool |
|---|---|
| **Query logs** | CloudWatch Logs — every query, retrieved chunks, LLM response, latency |
| **Metrics** | CloudWatch custom metrics — retrieval hit rate, answer confidence, latency p50/p99 |
| **Tracing** | AWS X-Ray — end-to-end trace from API Gateway through retrieval to Bedrock |
| **Feedback loop** | Thumbs up/down in UI → DynamoDB → weekly review → prompt/chunk tuning |
| **Alarms** | SNS alerts on error rate spike, Bedrock throttling, OpenSearch latency |

---

## 5. Data Flow Diagram — Query Path

```
Employee types: "What is the PTO carryover policy?"
        │
        ▼
API Gateway  →  Cognito Auth  →  Lambda Orchestrator
                                        │
                          ┌─────────────┴────────────┐
                          │   Query Rewrite (Bedrock) │
                          │   "PTO carryover rules    │
                          │    for employees"         │
                          └─────────────┬────────────┘
                                        │
                          ┌─────────────┴────────────┐
                          │   Hybrid Retrieval        │
                          │   OpenSearch kNN + BM25   │
                          │   → Top 5 chunks returned │
                          └─────────────┬────────────┘
                                        │
                          ┌─────────────┴────────────┐
                          │   Prompt Assembly         │
                          │   System + Context +      │
                          │   User Query              │
                          └─────────────┬────────────┘
                                        │
                          ┌─────────────┴────────────┐
                          │   Bedrock: Claude 3       │
                          │   Generates answer with   │
                          │   inline citations        │
                          └─────────────┬────────────┘
                                        │
                          ┌─────────────┴────────────┐
                          │   Format Response         │
                          │   Append source links     │
                          │   Log to DynamoDB         │
                          └─────────────┬────────────┘
                                        │
                                        ▼
                         "Employees can carry over up to
                          5 days of unused PTO per year.
                          [Source: HR PTO Policy v3, §4.2]"
```

---

## 6. Security Controls

| Control | Implementation |
|---|---|
| **Encryption at rest** | S3 SSE-KMS, OpenSearch encryption, DynamoDB encryption |
| **Encryption in transit** | TLS 1.2+ enforced at API Gateway and all internal calls |
| **VPC isolation** | Lambda and ECS in private subnets; OpenSearch and DynamoDB via VPC endpoints |
| **IAM least privilege** | Each Lambda has its own execution role scoped to exactly the resources it needs |
| **Bedrock Guardrails** | PII detection (SSN, credit card) stripped from prompts and responses |
| **WAF** | AWS WAF on CloudFront + API Gateway; rate limiting per employee |
| **Audit logging** | CloudTrail for all API calls; query audit in DynamoDB with 90-day retention |

---

## 7. Scalability & Cost Model

| Scenario | Architecture Behavior |
|---|---|
| **Low traffic (< 100 queries/day)** | Lambda handles all orchestration; near-zero idle cost |
| **Medium traffic (100–1000 queries/day)** | Lambda auto-scales; OpenSearch Serverless scales compute units on demand |
| **High traffic (1000+ queries/day)** | Move orchestrator to ECS Fargate with auto-scaling; pre-warm Lambda concurrency |
| **Document volume (< 100K chunks)** | Single OpenSearch index, single collection |
| **Document volume (> 1M chunks)** | Shard by domain (HR, IT, Legal, Engineering); route queries to relevant shard |

**Approximate cost drivers (monthly):**
- Bedrock embeddings: $0.0001 per 1K tokens (Titan V2)
- Bedrock Claude Haiku generation: $0.00025 per 1K input tokens
- OpenSearch Serverless: $0.24/OCU-hour (scales down when idle)
- Lambda: Negligible at < 10K queries/day

---

## 8. Phased Rollout Recommendation

| Phase | Scope | Duration |
|---|---|---|
| **Phase 1 — Foundation** | Single source (SharePoint HR docs), single user group (HR team), Slack bot only | 4 weeks |
| **Phase 2 — Expand Sources** | Add Confluence (Engineering wiki) + ServiceNow KB articles; IT team added | 3 weeks |
| **Phase 3 — Self-Service** | Web portal launched; all employees; multi-domain retrieval with routing | 4 weeks |
| **Phase 4 — Agentic** | Multi-hop reasoning (agent can follow references across docs); active feedback loop tuning | Ongoing |

---

## 9. Key Architecture Decisions & Tradeoffs

| Decision | Choice | Rationale | Tradeoff |
|---|---|---|---|
| **Vector DB** | OpenSearch Serverless | Native AWS, no separate service to manage, supports hybrid BM25+kNN | Higher cost than Pinecone at very large scale |
| **LLM** | Bedrock Claude | No data leaves AWS; enterprise privacy; no GPU infra | Slightly higher latency than self-hosted |
| **Chunking** | Fixed 512-token + overlap | Predictable, easy to tune | May split mid-table; mitigated with table extraction |
| **Orchestration** | Lambda-first | Zero idle cost; simple ops | 15-min timeout limit; complex agentic flows need Fargate/Step Functions |
| **Re-ranking** | Optional Cohere/cross-encoder | Significantly improves precision at top-5 | Adds ~100–200ms latency per query |

---

## 10. Future Enhancements

- **Agentic tool use**: Allow the agent to query ServiceNow tickets, Jira issues, or CMDB records in real time as supplementary context
- **Personalization**: Weight retrieval results by employee's team/role for more contextually relevant answers
- **Answer confidence scoring**: Surface a "confidence" indicator to employees when retrieved context is sparse
- **Auto-refresh**: Detect stale chunks when source documents are updated; re-embed and reindex automatically
- **Multilingual support**: Bedrock Titan Embeddings supports multilingual; extend to non-English employee populations

---

*Architecture version 1.0 | Platform Engineering | June 2026*
