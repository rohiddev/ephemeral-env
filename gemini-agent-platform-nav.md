# Google Gemini Enterprise Agent Platform — Navigation Reference

> Source: Google Cloud Agent Platform UI (Vertex AI Agent Builder)
> Purpose: Interview preparation — what each section does and why it matters

---

## Top Level — Agent Platform

The left nav is divided into two sections: **Build** and **Scale**.
This reflects the full agent lifecycle: build and test your agent, 
then deploy and operate it at scale.

---

## BUILD Section

### Agent Garden
A library of pre-built agent templates and reference implementations provided by Google.
Think of it as a marketplace of starting points — HR agents, customer service agents, code assistants, data analysis agents.

**Interview point:** "Rather than building from scratch, 
teams can clone a Garden template and customize it. 
Reduces time-to-first-agent from weeks to hours."

---

### ADK — Agent Development Kit
Google's open-source Python framework for building agents. ADK is the code layer — it defines how agents are structured, how tools are registered, how the agent loop (think → act → observe) executes, and how multi-agent systems are composed.

ADK provides:
- `Agent` class with tool definitions
- Built-in ReAct loop
- Streaming support
- Multi-agent orchestration (supervisor → specialist pattern)
- Integration with Gemini models via the Gemini API

**Interview point:** "ADK is Google's answer to LangGraph and LangChain. It gives you a structured agent loop without having to wire it yourself. The key differentiator is native Gemini integration and built-in multi-agent support."

---

### MCP Servers
Model Context Protocol — an open standard (originally from Anthropic, now cross-vendor) 
that defines how agents connect to external tools and data sources.
MCP Servers are the tool providers: file systems, databases, APIs, internal services.

In the Agent Platform, you register MCP Servers here. 
Your agents discover and call them at runtime without hardcoding API calls.

**Interview point:** "MCP decouples tool implementation from agent logic. 
You can swap out an MCP server (e.g. point to a different database) 
without changing the agent. It is to agents what REST is to web services — 
a standard interface."

---

### RAG Engine
Google's managed RAG (Retrieval-Augmented Generation) service. 
You point it at a corpus (documents in GCS, Drive, or BigQuery), i
t handles chunking, embedding, indexing, and retrieval. 
Agents call it as a tool: `retrieve(query)` → chunks returned → injected into context.

Under the hood it uses Vertex AI Vector Search + Gemini embeddings.

**Interview point:** "RAG Engine is the managed alternative to building your own
chunking pipeline. The trade-off: less control over chunking strategy and 
retrieval tuning, but zero infrastructure to operate. 
For most enterprise use cases it's the right starting point."

---

### Vector Search
Vertex AI Vector Search (formerly Matching Engine) — Google's managed ANN (approximate nearest neighbour) vector database. Used when you need more control than RAG Engine provides, or when you are storing your own embeddings from a custom pipeline.

Supports billions of vectors, low-latency retrieval, filtering by metadata.

**Interview point:** "RAG Engine sits on top of Vector Search. If RAG Engine is too opinionated, you drop down to Vector Search directly and build your own retrieval pipeline. Vector Search is the infrastructure layer; RAG Engine is the managed service layer above it."

---

### Search
Enterprise Search / Agent Builder Search — connects agents to
Google-quality search across your internal data sources: 
SharePoint, Confluence, GCS, BigQuery, websites. Returns ranked results with snippets.

Different from Vector Search: this is keyword + semantic hybrid search with a pre-built crawler and indexing pipeline. No embeddings to manage.

**Interview point:** "Search is for when you want Google's search quality applied to your internal corpus without building a RAG pipeline at all. Faster to stand up than RAG Engine, but less customizable. Good for document discovery; less good for precise factual retrieval."

---

## SCALE Section

### Deployments
Where you deploy agents to production endpoints. 
Each deployment is a versioned, hosted instance of an agent with a stable API endpoint.

Handles: model versioning, traffic splitting (A/B test agent versions), 
scaling (auto-scale on request volume), regional deployment.

**Interview point:** "Deployments is where an agent becomes a service. 
You get a REST endpoint, request logging, latency metrics, and version control.
A new agent version can receive 10% of traffic while the old version handles 90% 
— standard blue/green pattern applied to agents."

---

### Memory Bank
Persistent memory store for agents across sessions. Agents can write facts,
user preferences, prior decisions, and conversation summaries here and retrieve them 
in future sessions.

Without Memory Bank every conversation starts cold — the agent has no recollection 
of prior interactions. With Memory Bank the agent can recall: "Last time this user asked about parental leave, they were 6 months into their role."

**Interview point:** "Memory Bank is what separates a stateless chatbot from a 
stateful agent. It is the agent's long-term memory. Architecturally it is a k
ey-value or vector store scoped per user/session. 
The agent retrieves relevant memories at session start and writes new ones at session end."

---

### Sessions
Manages active agent sessions — conversation threads with state (message history, tool call history, intermediate outputs). Sessions are the short-term memory layer.

Memory Bank = long-term (persists across sessions)
Sessions = short-term (persists within a session)

**Interview point:** "The distinction between Sessions and Memory Bank maps directly to human memory: working memory (Sessions) vs long-term memory (Memory Bank). An enterprise agent needs both: Sessions to track what happened in this conversation, Memory Bank to remember what it learned about this user or process across all conversations."

---

---

## GOVERN Section

### Agent Registry
A central catalog of every agent deployed in the organization — name, version,
owner, description, tools it has access to, and which deployments are running it. 
The source of truth for "what agents exist and who is responsible for them."

**Interview point:** "At scale, organizations will have dozens or hundreds of agents. 
Without a registry, you have shadow AI — agents running in production that nobody knows 
about, with no ownership or audit trail. Agent Registry is governance layer zero: 
you cannot govern what you cannot see."

---

### Policies
Rules enforced at runtime on agent behavior — 
what topics an agent can and cannot discuss, what tools it is allowed to call, 
what data it can access, output filtering (PII redaction, content safety),
rate limits per user or group.

Policies are evaluated before the agent responds or takes an action. 
A policy violation blocks the action and logs it.

**Interview point:** "Policies are the guardrails layer. They enforce organizational 
rules without embedding them in agent code — a compliance team can update a policy 
without a code deployment. This separation of concerns is critical in regulated 
industries: the agent team owns the logic, the risk/compliance team owns the policies."

---

### Gateways
An API gateway layer specifically for agent traffic. 
Handles: authentication (who is calling the agent), authorization 
(which agents can this caller access), rate limiting, request/response logging, 
routing (which deployment version receives this request), and protocol translation.

**Interview point:** "Gateways are where multi-agent systems get controlled. 
Agent A calls Agent B through a Gateway — the Gateway enforces that A 
is allowed to call B, logs the interaction, and applies rate limits. 
Without Gateways, agent-to-agent calls are unaudited and uncontrolled. I
n a bank, every inter-agent call is a potential audit event."

---

### Security
Centralized security controls for the Agent Platform: 
IAM bindings (who can deploy agents, who can modify policies), 
secret management (API keys agents use to call external systems), 
VPC Service Controls (network isolation), and vulnerability scanning of 
agent configurations.

**Interview point:** "Security here is about the platform perimeter —
not what the agent says, but what the agent can reach. A rogue or compromised agent should not be able to exfiltrate data or call unauthorized APIs. VPC controls and IAM least-privilege on the agent's service account are the primary controls."

---

## OPTIMIZE Section

### Topology
A visual graph of your multi-agent system — which agents exist, which agents call 
\which other agents, which tools each agent uses, which deployments are active,
and how traffic flows across the system.

Think of it as a live architecture diagram generated from actual runtime data, 
not from documentation.

**Interview point:** "Topology is observability for agent architecture. 
When something fails in a multi-agent system, the first question is 
'which agent in the chain broke?' Topology gives you the graph to trace 
the call path. It also reveals unintended agent connections — an agent calling a 
tool it shouldn't — before it becomes a security incident."

---

### Evaluation
Framework for measuring agent quality — accuracy, groundedness
(is the answer supported by retrieved documents?), relevance,
safety (did it violate any policies?), latency, and cost per query.
Run evaluations against a golden dataset to compare agent versions 
before promoting to production.

**Interview point:** "Evaluation is what makes agent deployment safe. You cannot A/B test an agent in production if you don't know what 'better' means. Evaluation defines the metrics, runs the agent against test cases, and gives you a score. A new agent version only goes to Deployments if it scores equal or better on the evaluation set. This is the quality gate."

---

## Bottom Links

### Get API Key
Generates a Gemini API key for calling the Agent Platform programmatically —
for CI/CD pipelines, local development, testing agents before deploying to the platform.

### Tutorials
Guided walkthroughs for each section. The ADK tutorial walks through building a 
multi-agent system step by step.

---

## How It All Connects — The Full Lifecycle

```
BUILD
  Agent Garden    →  start from a template
  ADK             →  write agent logic in Python
  MCP Servers     →  register tools the agent can call
  RAG Engine      →  connect agent to internal knowledge base
  Vector Search   →  underlying vector DB if custom pipeline needed
  Search          →  Google-quality search over internal docs

         ↓  agent is built and tested locally

SCALE
  Deployments     →  deploy to a production endpoint, version it
  Sessions        →  short-term memory per conversation
  Memory Bank     →  long-term memory across conversations

         ↓  agent is live in production

GOVERN
  Agent Registry  →  catalog of all agents — who owns what
  Policies        →  runtime guardrails — what agents can/cannot do
  Gateways        →  API gateway for agent traffic — auth, rate limit, audit
  Security        →  platform perimeter — IAM, VPC, secrets

         ↓  agents are controlled and auditable

OPTIMIZE
  Topology        →  live graph of agent architecture and call flows
  Evaluation      →  quality gate before promoting a new agent version
```

---

## One-Line Answers for Each Menu Item

| Section | Item | One-line answer |
|---|---|---|
| Build | Agent Garden | Pre-built agent templates — clone and customize |
| Build | ADK | Python SDK for building the agent loop and multi-agent systems |
| Build | MCP Servers | Registered tool providers — agents call these at runtime |
| Build | RAG Engine | Managed RAG — point at a corpus, get retrieval for free |
| Build | Vector Search | Managed vector DB — for custom embedding pipelines at scale |
| Build | Search | Enterprise search over internal docs — no embeddings needed |
| Scale | Deployments | Production endpoints — versioned, auto-scaled, monitored |
| Scale | Memory Bank | Long-term memory — persists facts across sessions |
| Scale | Sessions | Short-term memory — conversation history within a session |
| Govern | Agent Registry | Central catalog of all agents — ownership and audit trail |
| Govern | Policies | Runtime guardrails — what agents can and cannot do |
| Govern | Gateways | API gateway for agent traffic — auth, routing, logging |
| Govern | Security | Platform perimeter — IAM, VPC controls, secrets |
| Optimize | Topology | Live graph of multi-agent call flows and dependencies |
| Optimize | Evaluation | Quality gate — score agent versions before promoting to prod |
