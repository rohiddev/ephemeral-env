# Director-Level System Design: Gaps, Corrections, and Quick Answers

This is a **supplement** to your existing preparation. Your current list has a strong foundation in infrastructure, distributed systems, cloud, data, leadership, and agentic AI. This document fills the most important gaps for a Director-level system-design interview.

---

## 1. The Director-Level Answer Pattern

Do not begin with technologies. Start every architecture answer with this sequence:

```text
1. Outcome: What customer or business problem are we solving?
2. Constraints: Scale, latency, availability, consistency, compliance, cost, and delivery date.
3. Decision: What architecture do we choose and why?
4. Tradeoff: What do we give up or defer?
5. Controls: Security, reliability, observability, and rollout plan.
6. Measures: How will we know it works?
```

### 45-second opening template

> “Before selecting technology, I would clarify the business outcome, the users, expected volume, reliability target, data sensitivity, and delivery constraints. I would start with the simplest architecture that satisfies those constraints, make the important tradeoffs explicit, and design for safe evolution rather than premature scale. I would define ownership, SLOs, security controls, and adoption measures before calling the design complete.”

### Strong Director close

> “The architecture is not complete until the operating model is clear: who owns it, how it is deployed safely, how we detect failure, how we recover, and how we measure business value.”

---

## 2. Most Important Gaps to Add

| Gap | Why interviewers ask it | Director-level answer theme |
|---|---|---|
| Capacity planning | Tests whether you can turn vague scale into a design. | Estimate traffic, storage, peak patterns, headroom, and cost. |
| SLOs and error budgets | Tests operational maturity. | Define user-centric reliability targets and use error budget to balance speed with safety. |
| Data integrity in async systems | Tests real distributed-systems experience. | Idempotency, outbox, retries, DLQs, reconciliation, and compensating actions. |
| Multi-tenancy and data isolation | Common in enterprise/SaaS designs. | Tenant identity, authorization, encryption, noisy-neighbor controls, and auditability. |
| Disaster recovery | Tests business-continuity thinking. | Define RTO/RPO, choose topology accordingly, and rehearse restoration. |
| API and schema evolution | Tests ability to run systems over time. | Contract-first, additive changes, deprecation, consumer communication, and compatibility tests. |
| Backpressure and overload | Tests whether your platform fails safely. | Admission control, queues, rate limits, load shedding, and graceful degradation. |
| Data governance | Especially important in regulated organizations. | Classification, retention, lineage, access policy, quality, and audit evidence. |
| Agentic AI governance | Tests whether AI is an enterprise capability rather than a demo. | Least privilege, grounded retrieval, tool controls, evaluation, human approval, and traceability. |
| Organization design | Director-level design includes teams and ownership. | Conway's Law, platform/product boundaries, decision rights, and service ownership. |

---

# Part I - Core System Design Questions You Need

## Q1. How do you begin any system design problem?

### Quick answer

> “I start by clarifying the business workflow and success metric, then establish non-functional requirements: users, peak and average traffic, latency, availability, consistency, data sensitivity, retention, geographic scope, and budget. I sketch the simplest viable design, identify the highest-risk assumptions, then deep dive into data, failure modes, security, and operational ownership.”

### Follow-up points

- Clarify read/write ratio, peak versus average load, payload size, and growth horizon.
- Ask whether data loss is acceptable and identify the consequence of stale data.
- Separate must-have requirements from future scale requirements.
- State what you will deliberately not build in version one.

### Common pitfall

Jumping directly to Kubernetes, Kafka, microservices, or a specific cloud vendor.

---

## Q2. How do you estimate scale and capacity?

### Quick answer

> “I use rough order-of-magnitude estimates first. I calculate average and peak requests per second, read/write ratio, request size, storage growth, and data-retention needs. I size for peak traffic with explicit headroom, validate the estimate with load testing, and revisit it as adoption changes.”

### Quick example

```text
10 million monthly active users
10 actions per user per month = 100 million actions/month
100M / 30 / 24 / 3600 ≈ 39 average requests per second
Assume 10x peak = about 400 RPS

At 5 KB/request: 400 RPS x 5 KB ≈ 2 MB/sec inbound at peak
```

Use approximate numbers. The interviewer wants your assumptions and reasoning, not perfect arithmetic.

### Add

- Capacity is not only compute: estimate database connections, cache memory, queue depth, network egress, and cost.
- Include load shedding and a plan for unexpected spikes.

---

## Q3. How do you define reliability for a service?

### Quick answer

> “I define reliability in user terms with service-level indicators and objectives. For example, 99.9% of successful API requests under 300 milliseconds monthly. That gives us an error budget, which lets the organization balance delivery speed against operational risk. If we burn the budget too quickly, we slow releases and focus on reliability work.”

### Key terms

| Term | Meaning |
|---|---|
| SLI | The measured indicator, such as success rate or latency. |
| SLO | The target, such as 99.9% success or p95 under 300 ms. |
| SLA | External commitment; often includes commercial consequences. |
| Error budget | Permitted unreliability: 0.1% for a 99.9% SLO. |

### Common pitfall

Saying “five nines” without identifying the business need, dependency limits, cost, or measurement method.

---

## Q4. Design a system that processes an important request exactly once.

### Strong answer

> “In distributed systems, I avoid promising literal exactly-once end-to-end delivery unless the infrastructure truly supports it. I design for at-least-once delivery with idempotent processing. The client sends an idempotency key, the service persists the key and request result transactionally, and retries return the original outcome. For downstream events, I use the transactional outbox pattern, durable queues, consumer deduplication, dead-letter queues, and reconciliation jobs.”

### Diagram to draw

```text
Client
  │ idempotency key
  v
API Service ──transaction──> Business DB
  │                              │
  │                              └── Outbox record
  v
Original response                       │
                                        v
                                  Outbox publisher
                                        │
                                        v
                                Durable event queue
                                        │
                                        v
                           Idempotent consumer + dedupe store
```

### Important terms

- **Idempotency:** retrying the same request produces the same logical outcome.
- **Transactional outbox:** persist business data and an event in one database transaction; publish later reliably.
- **DLQ:** isolate repeatedly failing messages for investigation/replay.
- **Reconciliation:** compare source and destination state; repair exceptions.
- **Saga / compensating action:** reverse earlier completed steps when a later distributed step fails.

### Common pitfall

Claiming that Kafka, a queue, or a database alone provides exactly-once business outcomes.

---

## Q5. How do you prevent cascading failure during a traffic spike or dependency outage?

### Quick answer

> “I protect the critical path through layered overload controls: timeouts with deadlines, bounded retries with jitter, circuit breakers, bulkheads, queue limits, rate limiting, admission control, and load shedding. I degrade noncritical capabilities first, preserve core transactions, and make recovery observable through queue depth, saturation, dependency latency, and error-budget burn.”

### Draw this pattern

```text
Client → CDN/WAF → Rate Limit → API → Bounded Queue → Worker → Dependency
                       │              │                 │
                       └─ reject 429  └─ shed low-value  └─ timeout/circuit break
```

### Common pitfall

Retries without a limit or jitter. This can amplify an outage into a retry storm.

---

## Q6. How do you design for multi-region availability and disaster recovery?

### Quick answer

> “I start with the business recovery objectives. RTO defines how quickly the service must recover; RPO defines acceptable data loss. For many systems, single-region multi-zone availability plus tested backups is the right starting point. I add active-passive regional failover for stricter recovery requirements, and active-active only when latency, scale, or availability justifies its operational complexity.”

### Decision guide

| Pattern | Best use | Tradeoff |
|---|---|---|
| Single region, multi-zone | Default for many services | Regional outage remains a risk. |
| Active-passive regions | Clear DR requirements | Failover and replication lag must be tested. |
| Active-active regions | Global latency or very high availability | Conflict resolution, data consistency, and cost are much harder. |

### Must mention

- Tested restore is more important than “we have backups.”
- Runbooks, regular failover exercises, dependency mapping, and communication plans.
- Data residency and replication restrictions.

---

## Q7. How do you evolve APIs and database schemas without breaking clients?

### Quick answer

> “I treat schema evolution as a product change. Prefer additive, backward-compatible changes; version only when necessary; publish contracts; use consumer-driven contract tests; measure adoption; and deprecate with a documented timeline. For databases, use expand-contract migrations: add compatible schema first, deploy dual-read or dual-write if needed, migrate data, move consumers, then remove old fields only after evidence shows they are unused.”

### Expand-contract sequence

```text
1. Add new column / endpoint / field; old behavior still works.
2. Deploy code that writes both formats when required.
3. Backfill and migrate consumers.
4. Switch reads to the new format.
5. Observe adoption and remove old format after the deprecation period.
```

### Common pitfall

A “v2 API” without a lifecycle, migration plan, compatibility policy, or client adoption measurement.

---

## Q8. How do you design multi-tenant enterprise software safely?

### Quick answer

> “Tenant isolation starts with identity and authorization, not just database design. I carry tenant context through every request, enforce it at the policy and data-access layers, and audit sensitive access. The storage model depends on risk and scale: shared tables with tenant keys for lower-risk scale, separate schemas or databases for stronger isolation, and dedicated environments where regulatory or contractual requirements demand it.”

### Include

- Tenant-aware authorization and row-level data controls.
- Encryption, key strategy, retention, export/delete workflows, and audit logs.
- Per-tenant quotas and rate limits to prevent noisy neighbors.
- Test isolation explicitly; never depend only on UI filtering.

---

## Q9. How do you make a platform team successful instead of a ticket factory?

### Quick answer

> “I run the platform as a product. I define internal customer personas and top journeys, offer paved roads through self-service APIs and templates, publish reliability and support expectations, and measure adoption, time-to-first-success, lead-time reduction, support deflection, and developer satisfaction. The platform owns common capabilities; product teams retain domain ownership.”

### Director-level measures

- Provisioning time and time to first deployment.
- Percentage of workloads on supported paved roads.
- Ticket volume and self-service completion rate.
- Deployment frequency, lead time, change failure rate, and MTTR.
- Cost per workload or per transaction where relevant.

### Common pitfall

Measuring platform success only by the number of features delivered.

---

# Part II - AI and Agentic-System Questions You Need

## Q10. When should you use a workflow, RAG, an agent, or multi-agent design?

### Quick answer

> “I use deterministic workflows for known, repeatable steps; RAG for grounded question answering; an agent when the task requires tool selection or multi-step judgment; and multi-agent patterns only when specialization creates measurable value. I do not use an agent where a workflow is safer, cheaper, and easier to test.”

| Need | Best fit |
|---|---|
| Fixed sequence, high-risk action | Deterministic workflow |
| Answer from approved documents | RAG |
| Investigate, choose tools, iterate | Single agent with bounded tools |
| Distinct specialties or parallel analysis | Multi-agent orchestration |

### Strong line

> “Agentic is not a maturity level. It is an architectural choice justified by the uncertainty and autonomy required by the task.”

---

## Q11. Design an enterprise agentic AI platform.

### Quick answer

> “I would design it as a governed platform, not a collection of chatbots. Users authenticate through enterprise identity; an AI gateway enforces model, rate, and data policies; an orchestrator runs narrowly scoped agents; RAG retrieves only approved knowledge; a controlled tool gateway authorizes every external action; high-impact actions require human approval; and every prompt, retrieval, tool call, decision, and approval is traceable.”

### Whiteboard architecture

```text
Users / Apps
     │
     v
Identity + RBAC/ABAC + consent + PHI/PII controls
     │
     v
AI Gateway: model routing, quotas, safety, policy enforcement
     │
     v
Agent Orchestrator / Supervisor
     ├───────────────┬────────────────┐
     v               v                v
Specialist agents    RAG              Tool Gateway
                     │                │
              Curated knowledge       Approved enterprise APIs
                     │                │
                     └───────┬────────┘
                             v
                    Human approval for high-impact actions

Governance across all layers: audit, evaluation, observability, cost, lifecycle
```

### Key design principles

- Agents must not receive broad database credentials or unrestricted tool access.
- Tool services independently enforce authentication and authorization; never trust the model to do so.
- Use least privilege and risk tiers for agents, tools, data sources, and actions.
- Separate read, draft, recommend, and execute privileges.
- Start with low-risk, read-only use cases and measurable business outcomes.

---

## Q12. How do you secure an agent against prompt injection and unsafe tool use?

### Quick answer

> “I assume untrusted content may contain malicious instructions. I separate system instructions, user input, retrieved content, and tool results; treat retrieved text as data rather than authority; minimize tool permissions; validate tool arguments against schemas and business policy; require confirmation or approval for consequential actions; and log decisions for investigation. Prompt filters help, but the security boundary is authorization at the tool and data layers.”

### Controls to mention

| Threat | Primary control |
|---|---|
| Prompt injection in documents | Treat retrieval as untrusted data; isolate instructions; content filtering. |
| Unauthorized data retrieval | User/tenant-aware retrieval and data access controls. |
| Unsafe agent action | Tool-level authorization, schemas, policy engine, approval. |
| Data exfiltration | Egress controls, redaction, DLP, restricted tools, audit. |
| Runaway cost / loops | Max steps, deadlines, quotas, circuit breakers, token budgets. |

### Common pitfall

Saying “the system prompt will prevent the agent from doing it.” Prompts are behavior guidance, not an authorization boundary.

---

## Q13. How do you evaluate and release an agent safely?

### Quick answer

> “I use an evaluation lifecycle before broad release: define intended use and prohibited behavior, create a representative test set including adversarial and failure cases, evaluate answer quality and tool behavior, run human review for high-risk outputs, deploy behind feature flags, monitor production quality and escalation rates, then continuously regression-test changes to prompts, models, tools, and retrieval.”

### Metrics

- Task completion and correctness.
- Citation / grounding quality.
- Unsafe-action prevention rate.
- Tool success, policy-denial, and human-override rates.
- Latency and cost per completed task.
- Escalation / containment rate.
- User satisfaction, but never as the only quality metric.

### Common pitfall

Using an LLM judge alone for critical correctness or safety decisions. Use a mix of deterministic checks, reference answers, human review, and production monitoring.

---

## Q14. How do you handle memory in an enterprise agent?

### Quick answer

> “I default to minimal, scoped memory. Session memory supports the active task and expires. Long-term memory must have an explicit business purpose, user visibility where appropriate, retention policy, access controls, correction/deletion workflow, and tenant isolation. I do not let an agent silently accumulate sensitive personal or regulated data.”

### Decision points

- Is memory necessary, or can the agent retrieve authoritative data each time?
- Is it a user preference, task state, enterprise record, or sensitive information?
- Who can read it, correct it, delete it, and audit it?
- What is the retention period and legal basis?

---

# Part III - Technical Corrections to Your Existing Notes

Use these refinements in interviews so your answers are accurate and senior-level.

| Existing topic | Refined answer |
|---|---|
| CAP theorem | During a network partition, a distributed system must choose whether to prioritize consistency or availability for the affected operation. CAP is not “choose any two at all times.” |
| TCP vs UDP | Modern HTTP/3 uses QUIC over UDP, adding reliability and encryption at higher layers. DNS can use UDP, TCP, DoH, or DoT depending on the scenario. |
| TLS handshake | In modern TLS, client and server typically use asymmetric cryptography for authentication and key agreement, then derive symmetric session keys for application data. |
| Kubernetes pod failure | A failed process may be restarted by the kubelet; a pod may be replaced by its controller if it is terminated/evicted. Readiness removes it from service endpoints; liveness can trigger restarts but is not the only failure detector. |
| SQL vs NoSQL | SQL and NoSQL are not synonymous with strong versus eventual consistency or vertical versus horizontal scaling. Many relational systems scale horizontally and many NoSQL systems support transactions. Select based on data model, access patterns, consistency, operations, and team skill. |
| Eventual consistency | It is not automatically unacceptable for inventory or payments; it can be used if the business process includes reservations, idempotency, reconciliation, and compensating actions. The key question is the cost of stale/conflicting state. |
| RAG | RAG can improve factual grounding, but it does not guarantee correctness. Retrieval quality, authorization, chunking, citation, and refusal behavior are part of the design. |
| LLMs | “Autocomplete at scale” is a useful simplification, but say that LLMs generate tokens from learned probability distributions and can perform useful reasoning-like tasks without being a deterministic source of truth. |
| Exactly once | Prefer “at-least-once delivery plus idempotent business processing” unless you can precisely state the scope of an exactly-once guarantee. |
| Retry strategy | Retry only transient, idempotent operations; use bounded exponential backoff with jitter and a total deadline. Avoid retrying non-idempotent requests without an idempotency key. |

---

# Part IV - Director-Level Architecture Pitfalls

## The answers that sound junior

| Avoid saying | Better Director-level framing |
|---|---|
| “We should use microservices.” | “I would start with the team and domain boundaries, then decide whether independent deployment and scaling justify distributed-system complexity.” |
| “We need active-active multi-region.” | “I would establish RTO/RPO, user latency, and data-residency needs first; active-active is justified only when those needs outweigh its consistency and cost complexity.” |
| “Kafka guarantees exactly once.” | “Kafka can support processing guarantees, but I still design business operations to be idempotent and reconciled.” |
| “We will use AI to automate it.” | “I would separate assist, recommend, and execute capabilities, define risk tiers, and start with a measurable low-risk workflow.” |
| “We need five nines.” | “I would define an SLO aligned to the business impact and cost of failure, then establish the dependencies and operational investment needed to meet it.” |
| “Security will review it later.” | “Security, privacy, auditability, and data classification are architecture inputs from the beginning.” |
| “The platform team will build it.” | “The platform team provides a self-service paved road with published service levels; product teams own domain behavior and adoption.” |

## Do not forget in any design

```text
Business outcome
Scale and growth
Data classification and security
Failure modes and recovery
Observability and SLOs
Cost and operational burden
Ownership and team boundaries
Migration and rollout strategy
Success measures
```

---

# Part V - Practice Prompts

Practice answering each in 10 minutes on a whiteboard, then in 2 minutes verbally.

1. Design a secure internal developer platform for 5,000 engineers.
2. Design a claims-document processing system with human review and auditability.
3. Design a multi-region customer-notification platform.
4. Design an API platform for external partners with tenant isolation and quotas.
5. Design a payment workflow that resists duplicate requests and downstream failure.
6. Design a healthcare knowledge assistant that protects sensitive information.
7. Design an agent that can create IT tickets and execute approved runbooks.
8. Migrate a 20-year-old monolith while continuing feature delivery.
9. Reduce cloud spend by 25% without reducing reliability.
10. Design a data-retention and deletion platform for regulated customer data.

## Checklist for each practice answer

- [ ] State the user and business outcome.
- [ ] Ask or declare scale, latency, availability, consistency, and compliance assumptions.
- [ ] Draw a high-level component diagram.
- [ ] Describe the data model and data ownership.
- [ ] Explain the two hardest tradeoffs.
- [ ] Cover overload, failure, and disaster recovery.
- [ ] Cover security, audit, and access control.
- [ ] State metrics, ownership, rollout, and evolution plan.

---

## Final Memory Hook

```text
At Director level, architecture = technology + operating model + risk model + business outcome.
```
