# Ephemeral Environment Architecture

## Overview

An ephemeral environment is a full, isolated, on-demand stack provisioned for a specific version of software — including all dependent services — and torn down after the test run. The key challenge is **version compatibility mapping**: ensuring Loan App v1 always runs alongside the correct version of Person App, the right MQ schema, and the matching API Gateway contract.

---

## Version Compatibility Registry

The registry is the source of truth. It defines which versions of each service are compatible for a given test target.

| Test Target     | Person App | MQ Schema | API GW Contract | EC2 AMI       |
|-----------------|------------|-----------|-----------------|---------------|
| Loan App v1     | v2.3       | v4        | v1              | ami-loan-v1   |
| Loan App v2     | v2.5       | v4        | v2              | ami-loan-v2   |
| Loan App v3     | v3.0       | v5        | v2              | ami-loan-v3   |

> Each row is a **compatibility manifest** — a declaration of the full stack for one test scope. The orchestrator reads this manifest to know what to provision.

---

## Architecture Layers

```
┌─────────────────────────────────────────────────────────────┐
│              Version Compatibility Registry                  │
│  Loan App v1 ──► Person App v2.3 + MQ schema v4 + API GW v1│
└──────────────────────────┬──────────────────────────────────┘
                           │ reads manifest
                           ▼
              ┌────────────────────────┐
              │  Ephemeral Env         │
              │  Orchestrator          │
              │  (provisions full      │
              │   stack per manifest)  │
              └────────────┬───────────┘
                           │ provisions
                           ▼
┌─────────────────────────────────────────────────────────────┐
│         Isolated Stack  [env-loanapp-v1-abc123]             │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ K8s namespace│─►│ Message queue│─►│   API gateway    │  │
│  │ v1 + v2.3    │  │ MQ schema v4 │  │ Ephemeral stage  │  │
│  └──────┬───────┘  └──────┬───────┘  └──────────────────┘  │
│         │                 │                                 │
│  ┌──────▼───────┐  ┌──────▼───────┐  ┌──────────────────┐  │
│  │ EC2 instances│  │  Data sync   │  │ Routing isolation│  │
│  │ Non-k8s loads│  │ Seeded, iso. │  │ ≠ prod / QA      │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## Component Breakdown

### 1. Kubernetes Namespace
- One namespace per ephemeral env, named after the env tag (e.g. `env-loanapp-v1-abc123`)
- Helm values override image tags to pin exact versions
- Services within the namespace discover each other via in-cluster DNS — no cross-env traffic
- Namespace is deleted on teardown

### 2. EC2 Instances
- For workloads that cannot run in containers (legacy MQ agents, licensed software, etc.)
- Provisioned via Terraform with the env tag as a variable
- Security group rules restrict traffic to the ephemeral env's namespace/VPC only
- Instance terminated on teardown

### 3. Message Queue (MQ)
- Options: dedicated IBM MQ queue manager, RabbitMQ virtual host, or ActiveMQ broker
- Schema version pinned to the compatibility manifest (e.g. MQ schema v4)
- Queue names namespaced by env tag to prevent cross-env message bleed
- Destroyed or flushed on teardown

### 4. API Gateway
- A dedicated stage or route prefix per ephemeral env
- Maps `X-Env-Tag: loanapp-v1-abc123` header to the env's backend services
- Endpoints are isolated — no shared routes with prod or QA
- Stage deleted on teardown

### 5. Data Sync
- A schema clone or anonymised snapshot seeded to a known, reproducible state
- Must be isolated — no writes flow back to prod or QA databases
- Options: Postgres schema-per-env, RDS snapshot restore, or data subsetting tool (e.g. Faker + seed scripts)

### 6. Routing Isolation (Netflix-style)
- Every request entering the ephemeral stack carries a header: `X-Env-Tag: <env-id>`
- The API gateway reads this header and routes to the correct env's services
- Inter-service calls within the env propagate the header downstream
- Loan App v1 always calls Person App v2.3 and never leaks to prod or another env

---

## Version Mapping — How It Works

```
Test request:  POST /loan/apply
               X-Env-Tag: loanapp-v1-abc123

API Gateway    → routes to Loan App v1 pod (in k8s ns env-loanapp-v1-abc123)

Loan App v1    → calls Person App (propagates X-Env-Tag header)
               → gateway routes to Person App v2.3 pod (same namespace)

Person App v2.3 → publishes to MQ queue "payments.loanapp-v1-abc123"
               → EC2 consumer reads from same namespaced queue

All services   → read/write to isolated data store (seeded snapshot)
               → never touch prod or QA endpoints
```

---

## Orchestration Flow

```
1. Test pipeline triggers env creation
   └── passes: service=loan-app, version=v1

2. Orchestrator looks up compatibility manifest
   └── resolves: person-app=v2.3, mq-schema=v4, api-gw=v1, ami=ami-loan-v1

3. Orchestrator provisions:
   ├── K8s namespace + deploys Helm charts with pinned image tags
   ├── EC2 instance via Terraform (if required by manifest)
   ├── MQ virtual host / queue manager
   ├── API Gateway stage + route rules
   └── Data sync job (snapshot restore + seed)

4. Orchestrator registers env in routing table
   └── API GW rule: X-Env-Tag: loanapp-v1-abc123 → env endpoints

5. Tests run against ephemeral endpoints

6. Teardown:
   ├── K8s namespace deleted
   ├── EC2 terminated
   ├── MQ virtual host deleted
   ├── API GW stage removed
   └── Data snapshot dropped
```

---

## Tooling Options

| Layer              | Option A                   | Option B                  |
|--------------------|----------------------------|---------------------------|
| Orchestration      | Harness IDP + IaCM         | Crossplane + ArgoCD       |
| K8s provisioning   | Helm + namespace controller| vcluster (virtual cluster)|
| EC2 provisioning   | Terraform (IaCM)           | AWS CDK                   |
| MQ isolation       | RabbitMQ virtual hosts     | IBM MQ queue manager clone|
| Routing            | AWS API GW + Lambda@Edge   | Istio service mesh        |
| Data isolation     | pg_dump snapshot restore   | Neon DB branching         |
| Registry (manifest)| Git YAML + OPA validation  | HashiCorp Consul KV       |

---

## Key Design Principles

- **Tag everything** — every resource in an ephemeral env carries the env tag. This drives routing, cost attribution, and teardown.
- **Manifest is the contract** — the compatibility registry is the only place where version mappings are defined. No hardcoding in pipelines.
- **Isolation by default** — network policies, MQ namespacing, and data snapshots ensure zero cross-env or prod bleed.
- **Idempotent provisioning** — re-running the orchestrator for the same env tag is safe (upsert, not create).
- **TTL on every env** — environments auto-expire (e.g. 24h) even if teardown is not explicitly triggered.
