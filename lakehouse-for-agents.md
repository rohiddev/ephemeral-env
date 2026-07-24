# Lakehouse for Agents — Architecture Reference

---

## 1. The Core Concept

A **data lakehouse** combines the low-cost storage of a data lake (raw files in S3/GCS/ADLS) with the query performance and ACID transactions of a data warehouse, using open table formats — Delta Lake, Apache Iceberg, or Apache Hudi.

For agentic systems, it solves a fundamental problem: agents need to query **structured data** (CMDB, metrics, SYSID records), **semi-structured data** (JSON events, logs), and **unstructured data** (documents, policies, runbooks) — from a single, consistent, auditable layer.

---

## 2. Where the Lakehouse Sits in the Stack

The lakehouse is the **source of truth**. Vector databases are derived indexes built from it — not the other way around.

```
┌─────────────────────────────────────────────┐
│              Agent / Query Layer             │
│   agents call tools to query this layer      │
└──────────────┬──────────────────────────────┘
               │
       ┌───────┴────────┐
       │  Vector DB      │   OpenSearch, Pinecone, LanceDB
       │  (index)        │   built FROM the lakehouse
       └───────┬─────────┘
               │ populated by ingestion pipeline
       ┌───────┴─────────┐
       │   Lakehouse      │   Delta Lake / Iceberg on S3
       │   (truth)        │   Bronze → Silver → Gold
       └─────────────────┘
```

**The analogy:** a relational database and a search index. The database (lakehouse) is authoritative. The search index (vector DB) is a materialized view for fast retrieval. When the lakehouse changes, the pipeline re-syncs to the vector DB.

---

## 3. Lakehouse vs Vector DB — What Each Does

| Concern | Pure Vector DB | Lakehouse |
|---|---|---|
| Vector similarity search | Yes | Yes (via LanceDB / Iceberg vector ext.) |
| SQL / structured queries | No | Yes (Athena, DuckDB, Spark) |
| Join structured + unstructured | No | Yes |
| Time travel (historical state) | No | Yes (Delta / Iceberg transaction log) |
| ACID transactions | No | Yes |
| Audit trail | No (separate) | Yes (built-in) |
| Cost at 100M chunks | ~$20K/month | ~$2,500/month |
| Source of truth | It is the store | Lakehouse feeds it |

---

## 4. The Relationship to Multiple Vector Databases

If you have multiple domain-specific vector databases (HR, Legal, Engineering) with no lakehouse underneath, you have multiple sources of truth. Document changes must be applied to each independently. Drift happens. Agents get inconsistent results across domains.

```
WITHOUT lakehouse:

HR Docs  →  HR Vector DB   ┐
Legal Docs → Legal Vector DB ├  3 separate sources of truth
Eng Docs  →  Eng Vector DB  ┘  agent queries each separately

WITH lakehouse:

All Docs
   ↓
Silver Layer (one canonical table: chunks + embeddings)
   ↓          ↓               ↓
HR Vector DB  Legal Vector DB  Eng Vector DB
(derived)     (derived)        (derived)

One source of truth. All vector DBs re-sync from Silver.
Agent always gets consistent data regardless of which index it hits.
```

**Three practical patterns for the vector DB relationship:**

| Pattern | Description | When to use |
|---|---|---|
| Lakehouse replaces vector DB | Embeddings stored as a column in Delta/Parquet. LanceDB queries them directly. No separate vector DB service. | Cost-sensitive, moderate query volume |
| Lakehouse feeds multiple vector DBs | Silver layer holds canonical chunks + embeddings. Pipeline syncs to OpenSearch (hybrid BM25+vector), Pinecone (scale), etc. Each is a derived index. | High query volume, specialized retrieval needs per domain |
| Federation | Query engine (Trino, Spark) federates across multiple vector stores. Lakehouse is still the source. | Rare — complex to operate |

---

## 5. The Bronze / Silver / Gold Data Layers

```
Bronze Layer — Raw Ingestion
  Immutable. Every source document landed exactly as received.
  Format: Parquet on S3. Partitioned by source and date.
  Sources: SharePoint, Confluence, ServiceNow, GitHub, S3, CMDB exports.
  No transformation. No cleanup. Source of truth for re-processing.

Silver Layer — Cleaned and Enriched
  Documents chunked (512 tokens, 20% overlap).
  Embeddings computed and stored as a column alongside text.
  Structured metadata joined in: SYSID, owner, classification, allowed_groups.
  Format: Delta Lake table.
  Schema per row:
    chunk_id, content, embedding[], source_system, source_url,
    section_title, last_updated, sysid, owner, allowed_groups[], data_classification

Gold Layer — Agent-Ready
  Pre-computed features: blast radius scores, service health signals,
  dependency subgraphs, CMDB relationship maps.
  Materialized aggregations agents would otherwise recompute at query time.
  Agent audit log: every query, retrieved chunk, LLM response, latency, user.
  Format: Delta Lake tables. ACID. Time-travel enabled.
```

---

## 6. Six Advantages for Agents Specifically

### 6.1 Structured + Unstructured in One Query

Agents today must choose: vector search OR SQL. With a lakehouse, a single agent tool can retrieve the top-5 policy chunks for parental leave AND join with an employee's HR record to check eligibility — one query, one layer. The join happens at the data layer, not in the agent's reasoning loop.

### 6.2 Time Travel — Agents Can Reason About Historical State

Delta Lake and Iceberg track every version of every table. An agent can query:
- What was the scorecard for `payments-service` on the day it was promoted to production?
- What did the blast radius graph look like before the outage?
- What policies were in effect when this decision was made six months ago?

This is impossible with OpenSearch or a pure vector database.

### 6.3 Agent Writes Back — ACID Transactions

When an agent makes a decision or updates a record (CMDB, catalog, audit log), S3 alone has no transactional guarantees — concurrent writes can corrupt state. Delta Lake provides full ACID on S3. Every agent action is committed atomically with a tamper-proof transaction log. Required for SOX compliance in regulated industries.

### 6.4 Cost at Scale

| Store | 10M chunks | 100M chunks |
|---|---|---|
| OpenSearch (managed) | ~$3,000/month | ~$30,000/month |
| Pinecone | ~$2,000/month | ~$20,000/month |
| S3 Parquet + LanceDB | ~$250/month | ~$2,500/month |

LanceDB stores vectors natively in Parquet/Lance format on S3. No separate vector DB service to manage. Agents query it directly. The cost difference becomes the business case.

### 6.5 Pre-Computed Feature Layer

Instead of agents recomputing the same aggregations on every query — blast radius scores, service health signals, CMDB relationship subgraphs — these are pre-computed nightly into Gold layer Delta tables. Agents read fast, structured facts rather than doing expensive inference work at query time. Latency drops. Cost drops.

### 6.6 Unified Audit Trail

Every agent query, retrieved chunk, LLM response, tool call, and latency measurement written as a Delta table row. Immutable. Queryable via Athena or Spark. Ready for compliance reports, model evaluation, and retrieval quality analysis — without building a separate logging system.

---

## 7. What Needs to Happen Architecturally

```
Phase 1 — Foundation (Weeks 1-4)
  Adopt open table format: Delta Lake (OSS) or Apache Iceberg
  Land all raw sources in Bronze as Parquet on S3
  AWS Glue Data Catalog or Hive Metastore as the unified metadata layer
  Athena or DuckDB for serverless SQL agent tools
  Outcome: agents can run SQL queries against structured data

Phase 2 — Silver Layer (Weeks 5-8)
  ETL pipeline: clean, chunk, embed documents → Silver Delta table
    columns: chunk_id, content, embedding[], source, last_updated, allowed_groups[]
  Join structured enrichment: CMDB / SYSID / ServiceNow metadata added per chunk
  LanceDB configured to read Silver Parquet for vector queries
  Outcome: agents can run vector search against lakehouse-backed embeddings

Phase 3 — Gold Layer (Weeks 9-12)
  Pre-compute blast radius scores, dependency graphs, service health signals
  Materialize common agent query patterns as Gold tables
  Agent audit log Delta table live — captures all interactions
  Outcome: agent query latency drops; compliance audit trail exists

Phase 4 — Agent Integration (Weeks 13-16)
  Two agent tools replace standalone vector DB:
    sql_query(table, filters)    →  Athena / DuckDB over Gold layer
    vector_search(query, top_k)  →  LanceDB over Silver embeddings
  Agents can JOIN across both in a single reasoning step
  All agent writes go through Delta transactions
  Outcome: unified agent data layer — structured, vector, audit in one place
```

---

## 8. AWS Stack

| Layer | Service |
|---|---|
| Object storage | S3 (Bronze, Silver, Gold prefixes) |
| Table format | Delta Lake OSS or Apache Iceberg via AWS Glue |
| Metadata catalog | AWS Glue Data Catalog |
| Batch ETL | AWS Glue (Spark) or EMR Serverless |
| Serverless SQL | Amazon Athena |
| In-process SQL | DuckDB (agent tool, zero infra) |
| Vector store | LanceDB on S3 (reads Parquet natively) |
| Streaming ingestion | Kinesis → S3 → Delta merge |
| Observability | CloudWatch + custom Delta audit table |

---

## 9. The CIO Pitch

> A lakehouse gives agents a single, governed, auditable data layer that is 80% cheaper than operating separate vector and structured stores, supports time travel for compliance, and enables agents to reason across structured facts and unstructured documents in the same query — capabilities that are architecturally impossible with a pure vector database.

The vector database is not replaced — it is promoted from a source of truth to a derived index, built from and governed by the lakehouse. One change to a document propagates to all downstream indexes from a single source. Consistency is structural, not operational.
