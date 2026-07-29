# IDP Scorecard — Common Sense Minimum Rules

> Starting point for any team onboarding to Harness IDP.
> These are the minimum checks every service should pass before it can be considered "known."
> Add domain-specific checks on top of these later.

---

## Why a Scorecard

A scorecard turns the catalog from a static registry into an enforced standard.
Without it, teams register services and never fill in the important fields.
With it, incomplete entries block production and create a self-service incentive to fix.

---

## The Minimum Viable Scorecard — 8 Checks

These 8 checks answer the single most important question about any service:
**"If this breaks at 2am, can we figure out who owns it, what it does, and what it affects?"**

### Group 1 — Identity (Who owns this?)

| # | Check Name | What It Checks | Why It Matters |
|---|---|---|---|
| 1 | Has Owner | `spec.owner` is populated | Without an owner, nobody is responsible |
| 2 | Has SYSID | Annotation `bank.com/sysid` exists | Links the service to the application record in ServiceNow |
| 3 | Has Email DL | Annotation `bank.com/email-dl` exists | Where alerts and pipeline notifications go |

### Group 2 — What Is It (What does this do?)

| # | Check Name | What It Checks | Why It Matters |
|---|---|---|---|
| 4 | Has Description | `metadata.description` is populated | A one-line answer to "what does this service do" |
| 5 | Has Lifecycle | `spec.lifecycle` is set | Tells the portal if this is production, experimental, or deprecated |
| 6 | Has TechDocs | Annotation `backstage.io/techdocs-ref` exists | Links to runbook/architecture docs |

### Group 3 — Risk (What breaks if this breaks?)

| # | Check Name | What It Checks | Why It Matters |
|---|---|---|---|
| 7 | Has GitHub Slug | Annotation `github.com/project-slug` exists | Links to the source code — required for drift detection and SBOM |
| 8 | Has Tier | Annotation `bank.com/tier` exists | Tier 1/2/3 drives incident severity and on-call escalation |

---

## Scorecard Setup in Harness IDP

```
IDP → Configure → Scorecards → + New Scorecard

Name:        Common Sense Minimum
Description: 8 baseline checks — identity, description, risk tier
Kind:        Component
Type:        service
Threshold:   80%  (allows 1 check to fail without blocking)
```

Add each check using the **Advanced** tab — not Basic.

### Check expressions

```
Check 1 — Has Owner
  catalog.annotationExists."spec.owner" == true
  (or use the built-in Owner check if available)

Check 2 — Has SYSID
  catalog.annotationExists."bank.com/sysid" == true

Check 3 — Has Email DL
  catalog.annotationExists."bank.com/email-dl" == true

Check 4 — Has Description
  catalog.annotationExists."metadata.description" == true

Check 5 — Has Lifecycle
  catalog.annotationExists."spec.lifecycle" == true

Check 6 — Has TechDocs
  catalog.annotationExists."backstage.io/techdocs-ref" == true

Check 7 — Has GitHub Slug
  catalog.annotationExists."github.com/project-slug" == true

Check 8 — Has Tier
  catalog.annotationExists."bank.com/tier" == true
```

---

## Minimum catalog-info.yaml That Passes All 8 Checks

```yaml
apiVersion: harness.io/v1
kind: Component
identifier: payments_service
name: payments-service
type: service
owner: group:account/team-payments
metadata:
  title: Payments Service
  description: Processes card payment authorizations for retail banking.
  annotations:
    bank.com/sysid: SYSID-06534
    bank.com/email-dl: payments-team@company.com
    bank.com/tier: "1"
    github.com/project-slug: bank-org/payments-service
    backstage.io/techdocs-ref: dir:.
spec:
  lifecycle: production
  system:
    - system:account/payments_platform
```

---

## Threshold Guidance

| Phase | Threshold | Rationale |
|---|---|---|
| **Wave 1 — onboarding** | 60% | Gets teams in the door without blocking |
| **Wave 2 — enforcement** | 80% | Allows 1-2 gaps, not structural ones |
| **Wave 3 — production gate** | 100% | Full compliance required before prod deploy |

Start at 60% for the first 30 days. Move to 80% after teams have had time to complete their entries. Only gate production deployments at 100% once the process is established.

---

## What Comes After the Minimum

Once the common sense baseline is passing, layer in:

| Next Check | Annotation | Adds |
|---|---|---|
| On-call schedule | `bank.com/oncall-schedule` | PagerDuty routing |
| Data classification | `bank.com/data-classification` | Compliance visibility |
| SOX scope | `bank.com/sox-in-scope` | Audit readiness |
| now.yaml exists | GitHub file check | ServiceNow CMDB sync |
| Dependency graph | `spec.dependsOn` populated | Blast radius visibility |
| Security scan passing | Harness STO check | SDLC compliance |

These form the **Production Readiness Scorecard** — the next level up from this common sense baseline.

---

## How to Communicate This to Teams

Keep the ask simple:

> "Fill in 8 fields in your catalog-info.yaml.
> If you don't know the answer to any of them, that's the problem we're trying to surface.
> The scorecard tells you exactly which fields are missing."

The 8 checks map to 8 questions every team should be able to answer about their service without looking anything up. If they can't, the catalog is doing its job by making that visible.

---

## Scoping Scorecards — By System or SYSID

### What Harness IDP Supports Natively

Scorecards in the Harness IDP UI are scoped by **Kind + Type only**:

| Scope | Example |
|---|---|
| All services | `Kind: Component, Type: service` |
| All websites | `Kind: Component, Type: website` |

There is no native filter by System or SYSID in the scorecard UI. A scorecard applies to every entity of that kind/type across the entire account.

---

### How to Scope by System or SYSID — Two Approaches

#### Option 1 — Separate Scorecard per System (recommended for high-value systems)

Create a dedicated scorecard with a stricter check set for a specific system. Name it clearly:

```
Common Sense Minimum    → all services (80% threshold)
Payments Platform       → payments system only (100% threshold)
Tier 1 Services         → all tier:1 services (100% threshold)
```

Apply the stricter scorecard in the pipeline gate only when `entity_ref` belongs to that system. The IDP dashboard will show both scorecards for entities in scope of both.

#### Option 2 — Single Scorecard + OPA Filter by SYSID or Tier (recommended for enforcement)

Use one scorecard for all services. In the governance pipeline, pass the entity's SYSID and tier to OPA. OPA applies different enforcement rules based on those values — stricter for Tier 1, lighter for Tier 3.

```rego
package idp_scorecard_gate

# Tier 1 — all checks must pass
deny[msg] {
  input.tier == "1"
  check := input.scorecard.checks[_]
  check.status == "failed"
  msg := sprintf("BLOCKED (Tier 1): check '%v' is failing for %v.", [check.name, input.entity_ref])
}

# Tier 2 — only high-weight checks block
deny[msg] {
  input.tier == "2"
  check := input.scorecard.checks[_]
  check.status == "failed"
  check.weight >= 15
  msg := sprintf("BLOCKED (Tier 2): high-priority check '%v' is failing for %v.", [check.name, input.entity_ref])
}

# Tier 3 — score threshold only, no check-level blocking
deny[msg] {
  input.tier == "3"
  to_number(input.overall_score) < 60
  msg := sprintf("BLOCKED (Tier 3): score %v%% is below 60%% minimum for %v.", [input.overall_score, input.entity_ref])
}
```

Pass tier and SYSID from the catalog entity into OPA via the pipeline:

```yaml
payload: |
  {
    "scorecard":     <+steps.Fetch_Scorecard.output.outputVariables.scorecard_json>,
    "overall_score": "<+steps.Fetch_Scorecard.output.outputVariables.overall_score>",
    "entity_ref":    "<+pipeline.variables.entity_ref>",
    "environment":   "<+pipeline.variables.environment>",
    "sysid":         "<+steps.Fetch_Entity.output.outputVariables.sysid>",
    "tier":          "<+steps.Fetch_Entity.output.outputVariables.tier>"
  }
```

---

### Which Approach to Use

| Situation | Approach |
|---|---|
| Different check sets per system | Option 1 — separate scorecards |
| Same checks, different thresholds per tier | Option 2 — OPA filter |
| SYSID-specific override (one app is special) | Option 2 — OPA with SYSID condition |
| Starting out, one standard for everyone | Single scorecard, no scoping needed yet |

Start with no scoping. Add tier-based OPA rules once you have enough services registered to see which ones need stricter enforcement.
