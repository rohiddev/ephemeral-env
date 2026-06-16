# Enterprise RAG Agent — GCP Architecture
### Internal Employee Q&A Platform
#### Powered by Gemini · Vertex AI · Document AI · Vertex AI Search

---

## 1. Overview

This document describes the architecture for an enterprise-grade Retrieval-Augmented Generation (RAG) agent deployed on Google Cloud Platform (GCP). The system enables employees to query internal knowledge bases — HR policies, IT runbooks, compliance docs, engineering wikis, SOPs — using natural language, and receive grounded, cited answers backed by authoritative internal sources.

This is the GCP-native equivalent of the AWS RAG architecture, using Gemini models and Vertex AI as the primary AI layer, Document AI for intelligent document processing, and Vertex AI Search as the managed retrieval and ranking engine.

---

## 2. AWS → GCP Service Mapping

| AWS Component | GCP Equivalent | Notes |
|---|---|---|
| Amazon Bedrock (Claude) | Vertex AI + Gemini 1.5 Pro / Flash | Managed model API, no GPU infra |
| Titan Embeddings V2 | Vertex AI text-embedding-004 | 768-dim, multilingual |
| OpenSearch Serverless | Vertex AI Search (Enterprise) | Managed RAG search + ranking |
| Textract (OCR) | Document AI (Form/OCR parsers) | Layout-aware extraction |
| Lambda | Cloud Functions (2nd gen) / Cloud Run | Event-driven compute |
| Glue (ETL bulk) | Dataflow (Apache Beam) | Serverless bulk processing |
| S3 | Cloud Storage (GCS) | Object storage |
| Cognito | Identity Platform (OIDC/SAML) | Employee SSO via Okta / Azure AD |
| API Gateway | Apigee / Cloud Endpoints | API management + auth |
| DynamoDB | Firestore | Serverless NoSQL, session + audit |
| CloudWatch | Cloud Monitoring + Cloud Logging | Observability stack |
| Step Functions | Workflows | Orchestration of multi-step agents |
| EventBridge | Cloud Scheduler + Pub/Sub | Event-driven scheduling |

---

## 3. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Employee Layer                           │
│  Web App / Slack Bot / Google Chat / Internal Portal            │
└───────────────────────────┬─────────────────────────────────────┘
                            │ HTTPS
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│              Apigee / Cloud Endpoints + Identity Platform        │
│         (Auth via SAML/OIDC, throttling, WAF, routing)          │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Orchestration Layer                           │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │         RAG Orchestrator (Cloud Run / Cloud Functions)   │  │
│  │                                                          │  │
│  │  1. Query rewriting / intent classification              │  │
│  │  2. Retrieval via Vertex AI Search                       │  │
│  │  3. Context assembly + prompt construction               │  │
│  │  4. LLM call (Vertex AI — Gemini 1.5 Pro/Flash)         │  │
│  │  5. Citation injection + response formatting             │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────┬────────────────────────────────┬────────────────────────┘
         │                                │
         ▼                                ▼
┌─────────────────┐            ┌──────────────────────┐
│  Knowledge      │            │   Vertex AI           │
│  Store Layer    │            │                       │
│                 │            │  Gemini 1.5 Pro (Q&A) │
│  Vertex AI      │            │  Gemini 1.5 Flash     │
│  Search         │            │  (fast queries)       │
│  (vector +      │            │  text-embedding-004   │
│   semantic      │            │  Gemini Guardrails    │
│   ranking)      │            └──────────────────────┘
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Ingestion Pipeline                         │
│                                                                 │
│  Sources → GCS Raw Bucket → Cloud Functions/Dataflow ETL →      │
│  Document AI → Chunker → Vertex AI Embeddings →                 │
│  Vertex AI Search Index + GCS Processed                         │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. Component Breakdown

### 4.1 Frontend / Entry Points

Employees interact via one or more of:

- **React Web App** — hosted on Firebase Hosting + Cloud CDN; connects via Apigee
- **Slack Bot** — Cloud Functions handles Slack Events API; posts threaded replies with source links
- **Google Chat Bot** — native GCP integration via Chat API and Pub/Sub event push
- **Internal Portal Widget** — embeddable JS widget for existing intranet

All entry points are stateless — session context managed in Firestore (conversation history per user/session).

---

### 4.2 Authentication & Authorization

| Component | Role |
|---|---|
| **Identity Platform** | Employee SSO via SAML/OIDC federation with Okta, Azure AD, or Google Workspace |
| **Firebase Auth / IAP** | Identity-Aware Proxy secures Cloud Run endpoints without custom auth code |
| **JWT Claims** | User's department, role, clearance level encoded in ID token |
| **Apigee Authorizer** | Validates JWT; passes user context (email, groups) downstream as headers |
| **Vertex AI Search ACLs** | Documents tagged with `allowed_groups[]`; retrieval filtered by user's group memberships at query time |

This ensures a Finance employee cannot retrieve IT infrastructure runbooks marked for the SRE group only.

---

### 4.3 Orchestration Layer (RAG Orchestrator)

The core orchestration runs in **Cloud Run** (containerized, auto-scales to zero) or **Cloud Functions 2nd gen** for lightweight event-driven flows. Complex multi-step agentic flows use **Vertex AI Agent Builder** or **Google Cloud Workflows**.

**Step-by-step flow:**

```
1. RECEIVE query from Apigee
        │
2. QUERY REWRITING
   └─ Gemini 1.5 Flash call to decompose, resolve pronouns,
      expand abbreviations, classify domain (HR/IT/Legal/Engineering)
        │
3. RETRIEVAL via Vertex AI Search
   └─ Managed hybrid retrieval (semantic + keyword + reranking)
      Single API call returns top-k grounded results
        │
4. CONTEXT ASSEMBLY
   └─ Top N chunks (default 5) assembled into prompt
      Metadata: source doc, section, last updated, author
      ACL strip: remove chunks user isn't authorized for
        │
5. LLM GENERATION (Vertex AI — Gemini 1.5 Pro or Flash)
   └─ System prompt: "Answer only from provided context.
      If not found, say so. Cite source for each claim."
        │
6. CITATION INJECTION
   └─ Parse output, resolve citations to source URLs
      (Drive, Confluence, SharePoint, GCS)
        │
7. RETURN response + sources to caller
        │
8. LOG to Cloud Logging + Firestore audit trail
```

---

### 4.4 Knowledge Store — Vertex AI Search

Vertex AI Search is GCP's managed enterprise search engine with built-in RAG capabilities. It handles vector indexing, semantic ranking, and hybrid retrieval in a single managed service — no separate vector DB to operate.

**Two data store types used:**

| Data Store Type | Use |
|---|---|
| **Unstructured (documents)** | PDFs, HTML, DOCX — ingested from GCS or directly from web URLs |
| **Structured (JSONL)** | Metadata records from ServiceNow, CMDB, HR systems with schema-defined fields |

**Key Vertex AI Search capabilities used:**

- **Semantic/vector search** — embedding-based nearest-neighbor search using Google's internal embedding models
- **Keyword search** — traditional full-text matching (BM25-equivalent)
- **Semantic reranking** — built-in LLM-based reranker re-scores results before returning; no separate reranker needed
- **Grounding** — native Vertex AI grounding API checks LLM response fidelity against retrieved sources
- **Follow-up query handling** — built-in session context management for conversational search flows

**Document metadata per chunk:**

```json
{
  "id": "hr-policy-pto-v3-chunk-12",
  "structData": {
    "source_system": "confluence",
    "source_url": "https://wiki.company.com/display/HR/PTO+Policy",
    "section_title": "Carryover Rules",
    "last_updated": "2025-11-01",
    "allowed_groups": ["all-employees"],
    "domain": "hr"
  },
  "content": {
    "mimeType": "text/plain",
    "uri": "gs://processed/hr-policy-pto-v3/chunk-12.txt"
  }
}
```

---

### 4.5 Ingestion Pipeline

Runs on a scheduled basis (Cloud Scheduler) and on-demand (GCS event triggers via Pub/Sub).

```
Source Systems                   GCP Ingestion
──────────────                   ─────────────
SharePoint Online  ──────────►  Cloud Function (Graph API)
Confluence Cloud   ──────────►  Cloud Function (REST API)        ┐
ServiceNow         ──────────►  Cloud Function (Table API)       ├─► GCS Raw Bucket
Internal GCS Docs  ──────────►  Direct copy                      │   (per source prefix)
HR System PDFs     ──────────►  GCS event trigger (Pub/Sub)      ┘
                                          │
                                          ▼
                              Cloud Functions / Dataflow ETL
                              ┌──────────────────────────────┐
                              │ 1. Extract text               │
                              │    (PDF/DOCX → Document AI,   │
                              │     HTML → Cloud DLP clean)   │
                              │ 2. Chunk (512 tokens,         │
                              │    20% overlap)               │
                              │ 3. Add metadata + ACL tags    │
                              │ 4. Embed via Vertex AI        │
                              │    text-embedding-004         │
                              │ 5. Upsert to Vertex AI        │
                              │    Search data store          │
                              │ 6. Archive to GCS Processed   │
                              └──────────────────────────────┘
```

---

### 4.6 Document AI — The Star of the Ingestion Pipeline

Document AI is GCP's purpose-built document understanding service. It goes far beyond simple text extraction — it understands document layout, structure, tables, and forms. This is the GCP equivalent and successor to AWS Textract, but with pre-trained specialized processors for specific document types.

**Document AI processors used:**

| Processor | Use Case |
|---|---|
| **Document OCR** | Scanned PDFs, image-based docs — converts to text with layout awareness |
| **Layout Parser** | HTML, DOCX, native PDFs — extracts text, tables, headings in reading order |
| **Form Parser** | HR forms, onboarding documents — extracts field-value pairs (Name: John, Role: Engineer) |
| **Custom Extractor** | Trained on your specific document types (e.g., internal SOPs with custom fields) |

**What Document AI returns (that simple extraction doesn't):**

```
Document layout tree:
  ├── Heading: "Section 4: PTO Carryover Rules"
  ├── Paragraph: "Employees may carry over up to 5 days..."
  ├── Table:
  │     ├── Row: ["Employee Type", "Max Carryover", "Expiry"]
  │     ├── Row: ["Full-time", "5 days", "March 31"]
  │     └── Row: ["Part-time", "2.5 days", "March 31"]
  └── Paragraph: "Exceptions require VP approval..."
```

This structure lets the chunker split intelligently — keeping table rows together, keeping headings with their paragraphs, preventing mid-sentence cuts.

**Document AI in the pipeline:**

```
PDF uploaded to GCS
        │
        ▼
Pub/Sub event → Cloud Function
        │
        ▼
Document AI API call
  → Layout Parser (for native PDFs)
  → OCR Processor (for scanned images)
        │
        ▼
Structured JSON response with:
  - paragraphs + positions
  - tables as structured objects
  - headings and hierarchy
  - page numbers
        │
        ▼
Custom chunker uses layout tree
(not blind token splits)
        │
        ▼
Clean, structure-aware chunks
ready for embedding
```

---

### 4.7 Vertex AI — Models & Embeddings

| Use | Model |
|---|---|
| **Embeddings** | text-embedding-004 (768-dim, multilingual) |
| **Q&A Generation** | Gemini 1.5 Flash (fast, cheap) or Gemini 1.5 Pro (complex queries) |
| **Query Rewriting** | Gemini 1.5 Flash (low latency, ~200ms) |
| **Multimodal (future)** | Gemini 1.5 Pro vision — process images and diagrams in documents |
| **Grounding** | Vertex AI Grounding API — checks answer fidelity against retrieved chunks |

**Gemini 1.5 Flash vs Pro decision:**

| Scenario | Model | Reason |
|---|---|---|
| "What is the dress code?" | Flash | Single-fact lookup, low latency needed |
| "Compare PTO policies across all three business units" | Pro | Multi-document reasoning, quality matters |
| "Summarize the last 6 months of IT incident reports" | Pro | Long context (1M token window), synthesis |
| Query rewriting | Flash | Must be under 300ms to not hurt UX |

**Why text-embedding-004 over alternatives:**

- 768 dimensions (smaller than AWS Titan's 1536 but comparable quality)
- Multilingual by default — no separate model for non-English employees
- Optimized for retrieval tasks specifically (not generic sentence similarity)
- ~$0.000025 per 1K characters (cheaper than Titan V2)

---

### 4.8 Vertex AI Agent Builder (Optional — Agentic Upgrade)

For teams that want to go beyond basic RAG into multi-step agent flows, Vertex AI Agent Builder provides:

- **Grounded generation** — native integration between Gemini and Vertex AI Search, with built-in citation handling
- **Tool use** — Gemini can call external APIs (ServiceNow, Jira, internal systems) to augment answers with live data
- **Session management** — multi-turn conversation with memory across questions in a session
- **Evaluation** — built-in answer quality scoring (groundedness, relevance, fluency)

This replaces the custom orchestration Lambda/Cloud Run for teams that prefer a managed agentic platform over writing orchestration code.

---

### 4.9 Data Stores

| Store | Use |
|---|---|
| **GCS (Raw)** | Original source documents, immutable, versioned |
| **GCS (Processed)** | Chunked text + metadata JSON + embeddings |
| **Vertex AI Search** | Managed vector + keyword index, real-time retrieval |
| **Firestore** | Conversation history (session_id → messages), query audit log |
| **Secret Manager** | API keys for source connectors, service account credentials |
| **Cloud DLP** | Scans documents at ingest for PII before they enter the index |

---

### 4.10 Observability

| Layer | Tool |
|---|---|
| **Query logs** | Cloud Logging — every query, retrieved chunks, Gemini response, latency |
| **Metrics** | Cloud Monitoring custom metrics — retrieval hit rate, latency p50/p99, answer confidence |
| **Tracing** | Cloud Trace — end-to-end from Apigee through Vertex AI Search to Gemini |
| **Feedback loop** | Thumbs up/down in UI → Firestore → weekly review → prompt tuning |
| **Alarms** | Cloud Monitoring alerts on error rate spike, Vertex AI quota hit, Search latency |
| **Evaluation** | Vertex AI Evaluation Service — automated answer quality scoring on sample queries |

---

## 5. Data Flow — Query Path

```
Employee types: "What is the PTO carryover policy?"
        │
        ▼
Apigee  →  Identity Platform Auth  →  Cloud Run Orchestrator
                                              │
                              ┌───────────────┴──────────────┐
                              │  Query Rewrite (Gemini Flash) │
                              │  + Domain classification: HR  │
                              └───────────────┬──────────────┘
                                              │
                              ┌───────────────┴──────────────┐
                              │  Vertex AI Search             │
                              │  Hybrid semantic + keyword    │
                              │  Built-in reranking           │
                              │  ACL filter on allowed_groups │
                              │  → Top 5 grounded chunks      │
                              └───────────────┬──────────────┘
                                              │
                              ┌───────────────┴──────────────┐
                              │  Prompt Assembly              │
                              │  System + context + query     │
                              └───────────────┬──────────────┘
                                              │
                              ┌───────────────┴──────────────┐
                              │  Vertex AI: Gemini 1.5 Pro   │
                              │  Grounding API validates      │
                              │  answer against source chunks │
                              └───────────────┬──────────────┘
                                              │
                              ┌───────────────┴──────────────┐
                              │  Format + cite sources        │
                              │  Log to Firestore             │
                              └───────────────┬──────────────┘
                                              │
                                              ▼
                         "Employees can carry over up to 5 days
                          of unused PTO per year.
                          [Source: HR PTO Policy v3 — Confluence]"
```

---

## 6. Ingestion Pipeline Detail — Document AI Focus

```
Stage 0: Sources
  SharePoint ──► Cloud Function (Graph API delta sync)
  Confluence ──► Cloud Function (REST API, changed pages only)
  ServiceNow ──► Cloud Function (Table API, KB articles: Published only)
  GCS uploads ──► Pub/Sub event trigger (immediate)
        │
        ▼
Stage 1: GCS Raw Bucket
  gs://raw/sharepoint/
  gs://raw/confluence/
  gs://raw/servicenow/
  Pub/Sub notification → triggers Cloud Function per new object
        │
        ▼
Stage 2: Document AI extraction
  PDF (native) ──► Layout Parser processor
  PDF (scanned) ──► Document OCR processor
  DOCX ──────────► Layout Parser processor
  HTML ──────────► Cloud DLP clean + custom parser
  Returns: structured JSON with paragraphs, tables, headings
        │
        ▼
Stage 3: Chunker (layout-aware)
  Fixed window: 512 tokens, 20% overlap (default)
  Hierarchical: 256-token child (retrieve) + 2048-token parent (context)
  Tables: extracted as standalone chunks, heading prepended
        │
        ▼
Stage 4: Vertex AI text-embedding-004
  Batch API call (up to 250 texts per request)
  Idempotent: skip re-embed if chunk hash unchanged
  Output: 768-dim vector per chunk
        │
        ┌─────────────────────┐
        ▼                     ▼
Stage 5a:                Stage 5b:
Vertex AI Search         GCS Processed Bucket
Upsert by chunk_id       gs://processed/chunk_id.json
Vector + keyword index   Stores content + metadata + embedding
Instantly queryable      Replay buffer if index rebuilt
Stale chunk cleanup      90-day lifecycle → Coldline storage
```

---

## 7. Security Controls

| Control | Implementation |
|---|---|
| **Encryption at rest** | GCS CMEK (Customer-Managed Encryption Keys via Cloud KMS) |
| **Encryption in transit** | TLS 1.3 enforced at Apigee and all internal service calls |
| **VPC isolation** | Cloud Run and Cloud Functions in VPC with Private Google Access; no public internet egress |
| **IAM least privilege** | Each Cloud Run service has its own service account scoped to exact resources |
| **Cloud DLP** | Scans every document at ingest — PII (SSN, card numbers) redacted before indexing |
| **Gemini safety filters** | Built-in content filtering on all Gemini API responses |
| **Apigee WAF** | Rate limiting per employee, IP-based blocking |
| **Audit logging** | Cloud Audit Logs for all API calls; query audit in Firestore with 90-day retention |
| **BeyondCorp / IAP** | Identity-Aware Proxy for zero-trust access to internal web app — no VPN required |

---

## 8. GCP vs AWS — Key Differences

| Capability | AWS Approach | GCP Approach | GCP Advantage |
|---|---|---|---|
| **Document extraction** | Textract (OCR + tables) | Document AI (specialized processors) | Pre-trained domain processors (forms, invoices, ID docs) |
| **Vector retrieval** | OpenSearch Serverless (self-managed index) | Vertex AI Search (fully managed RAG) | No index tuning; built-in reranking |
| **Reranking** | Cohere Rerank via Bedrock (separate call) | Built into Vertex AI Search | One less moving part, lower latency |
| **Grounding check** | Bedrock Guardrails (approximate) | Vertex AI Grounding API (native) | Tighter integration with Gemini |
| **Agentic flows** | Step Functions + Bedrock Agents | Vertex AI Agent Builder | End-to-end managed agent platform |
| **Multimodal docs** | Textract (text/tables only) | Gemini 1.5 Pro Vision | Processes charts, diagrams, images in docs |
| **Long context** | Claude 3 (200K token context) | Gemini 1.5 Pro (1M token context) | Full document in context without chunking for long docs |
| **Google Workspace** | N/A | Native Drive / Docs connector | Zero-code ingestion from Workspace |

---

## 9. Scalability & Cost Model

| Scenario | Architecture Behavior |
|---|---|
| **Low traffic (< 100 queries/day)** | Cloud Run scales to zero; Vertex AI Search per-query pricing |
| **Medium (100–1K queries/day)** | Cloud Run auto-scales containers; Search handles concurrency automatically |
| **High traffic (1K+ queries/day)** | Cloud Run max instances config; consider Vertex AI Search dedicated tier |
| **Document volume (< 100K chunks)** | Single Vertex AI Search data store |
| **Document volume (> 1M chunks)** | Multiple data stores by domain; query routing in orchestrator |

**Approximate cost drivers (monthly):**

- Vertex AI text-embedding-004: $0.000025 per 1K characters
- Gemini 1.5 Flash generation: $0.00015 per 1K input tokens
- Gemini 1.5 Pro generation: $0.00125 per 1K input tokens
- Vertex AI Search: $2.50 per 1K queries (Enterprise edition)
- Document AI Layout Parser: $10 per 1K pages
- Cloud Run: ~$0 at < 1K requests/day (free tier covers it)

---

## 10. Phased Rollout Recommendation

| Phase | Scope | Duration |
|---|---|---|
| **Phase 1 — Foundation** | Single source (Confluence HR space), Vertex AI Search data store set up, Google Chat bot | 4 weeks |
| **Phase 2 — Document AI** | Add PDF ingestion via Document AI (HR policy PDFs, SOPs); scanned doc support | 3 weeks |
| **Phase 3 — Multi-source** | Add SharePoint + ServiceNow KB; web portal launched; all employees | 4 weeks |
| **Phase 4 — Agentic** | Vertex AI Agent Builder; tool use (live ServiceNow lookups); Gemini 1.5 Pro for complex queries | Ongoing |

---

## 11. Future Enhancements

- **Gemini multimodal**: Process architecture diagrams, org charts, and flowcharts embedded in documents — Gemini 1.5 Pro Vision understands images natively
- **Google Workspace native connector**: Vertex AI Search has a built-in Google Drive connector — zero-code ingestion of Docs, Sheets, Slides
- **NotebookLM Enterprise**: Google's document Q&A product built on the same Vertex AI stack — evaluate as a faster path to pilot before building custom
- **Personalization**: Use Google Workspace user profile signals to bias retrieval toward employee's team and role
- **Vertex AI Evaluation**: Automated weekly benchmark runs to detect retrieval quality regression as the document corpus grows

---

## 12. When to Choose GCP Over AWS for This Use Case

| Factor | Lean GCP | Lean AWS |
|---|---|---|
| **Already on Google Workspace** | ✅ Native Drive/Docs connector | — |
| **Complex PDF/form documents** | ✅ Document AI specialized processors | — |
| **Very long documents (> 100 pages)** | ✅ Gemini 1.5 Pro 1M token context | — |
| **Multimodal documents (diagrams, charts)** | ✅ Gemini vision native | — |
| **Existing AWS infrastructure** | — | ✅ Keep it in the same cloud |
| **Prefer managed RAG (less ops)** | ✅ Vertex AI Search handles it all | — |
| **Need max embedding model choice** | — | ✅ Bedrock model garden is broader |

---

*Architecture version 1.0 | Platform Engineering | June 2026*
