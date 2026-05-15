This is the core architecture question. Let me break it down clearly.

  ---
  The mapping

  ┌───────────────────────────────┬────────────────────────────────────────┬───────────┐
  │            Reality            │           Harness IDP Entity           │   Count   │
  ├───────────────────────────────┼────────────────────────────────────────┼───────────┤
  │ Major business platforms      │ kind: System                           │ 20-30     │
  ├───────────────────────────────┼────────────────────────────────────────┼───────────┤
  │ CMDB application records      │ bank.com/sysid annotation on Component │ 500       │
  ├───────────────────────────────┼────────────────────────────────────────┼───────────┤
  │ Repos / microservices         │ kind: Component                        │ up to 19K │
  ├───────────────────────────────┼────────────────────────────────────────┼───────────┤
  │ Shared infra (DBs, Kafka, MQ) │ kind: Resource                         │ hundreds  │
  └───────────────────────────────┴────────────────────────────────────────┴───────────┘

  ---
  A SYSID is NOT a System.

  A SYSID is a CMDB tag on a Component. Multiple repos share one SYSID. Multiple SYSIDs belong to one major System.

  Payments Platform (System)
    ├── SYSID-00100  payments-core (Component)
    ├── SYSID-00100  payments-api-gateway (Component)
    ├── SYSID-00101  fraud-detection (Component)
    ├── SYSID-00101  fraud-ml-scoring (Component)
    └── SYSID-00102  ledger-service (Component)

  The bank.com/sysid annotation exists for CMDB linkage and scorecard enforcement — not to drive the System hierarchy.

  ---
  What you manage centrally (catalog repo)

  20-30 System entities + all shared Resources. These are stable and rarely change.

  entities/
    system-payments-platform.yaml
    system-digital-banking.yaml
    system-risk-analytics.yaml
    system-lending.yaml
    ...
    resource-payments-postgres.yaml
    resource-shared-kafka.yaml
    resource-payments-ibmmq.yaml
    ...

  ---
  What lives in each of the 19K repos

  One catalog-info.yaml per repo. The catalog automation pipeline generates and maintains it. The only system-level field the repo needs to declare is which System it belongs to:

  spec:
    system:
      - system:account/payments_platform   # set once, rarely changes

  ---
  Import scale

  You do NOT import all 19K repos manually. The catalog automation pipeline auto-registers each catalog-info.yaml via the Harness Catalog Ingestion API when a repo is onboarded or updated. The
  20-30 Systems and central Resources are imported once manually.

  ---
  Bottom line: Create 20-30 System entities. Let the 500 SYSIDs live as annotations. The 19K repos are Components that each declare which of the 20-30 Systems they belong to. That's the entire
  hierarchy.