# Enterprise Agentic AI Architecture - Whiteboard Preparation

**Audience:** Healthcare enterprise leadership and technical stakeholders  
**Purpose:** Illustrative target architecture for an enterprise agentic AI platform  
**Important:** This is a vendor-neutral target-state diagram. It does not represent any organization's current architecture.

---

## Whiteboard Title

```text
Illustrative Target Architecture:
Enterprise Agentic AI Platform for Healthcare
```

---

## Diagram to Draw

Draw seven boxes from left to right. Use arrows in the order shown.

```text
 ┌──────────────────┐
 │  USERS           │
 │ Members          │
 │ Providers        │
 │ Employees        │
 │ Operations / IT  │
 └────────┬─────────┘
          │
          v
 ┌──────────────────┐
 │ EXPERIENCE       │
 │ Web / Mobile     │
 │ Contact Center   │
 │ Teams / Apps     │
 └────────┬─────────┘
          │
          v
 ┌──────────────────┐
 │ SECURITY GATE    │
 │ SSO / MFA        │
 │ Roles & Consent  │
 │ PHI / PII Check  │
 └────────┬─────────┘
          │
          v
 ┌─────────────────────────────────────┐
 │ AGENTIC AI PLATFORM                 │
 │                                     │
 │  Supervisor Agent                   │
 │       │                             │
 │       ├── Care Navigation Agent     │
 │       ├── Claims Agent              │
 │       ├── Member Service Agent      │
 │       ├── Provider Agent            │
 │       └── IT Operations Agent       │
 └──────────────┬──────────────────────┘
                │
        ┌───────┴────────┐
        v                v
┌─────────────────┐  ┌─────────────────────┐
│ KNOWLEDGE / RAG │  │ CONTROLLED TOOLS    │
│ Policies        │  │ Claims systems      │
│ Clinical guides │  │ CRM / case system   │
│ Benefits        │  │ Provider directory  │
│ SOPs / Runbooks │  │ Clinical APIs       │
│ Vector database │  │ ITSM / ServiceNow   │
└─────────────────┘  └──────────┬──────────┘
                                 │
                                 v
                     ┌─────────────────────┐
                     │ HUMAN APPROVAL      │
                     │ High-risk actions   │
                     │ Claim / clinical /  │
                     │ payment decisions   │
                     └─────────────────────┘
```

Draw one large boundary around every box and label it:

```text
ENTERPRISE GOVERNANCE, SAFETY & OPERATIONS

• Policy-as-code
• PHI / PII protection
• Audit trail
• Human approval
• Model monitoring
• Cost / token controls
• Agent testing and evaluation
```

---

## How to Draw It

### Color guide

| Color | Use it for |
|---|---|
| Blue | Users, Experience, Agentic AI Platform, Knowledge/RAG, Controlled Tools |
| Red | Security Gate, PHI/PII controls, Human Approval |
| Green | Business-impact callouts: speed, consistency, reduced manual work, traceability |

### Layout guidance

1. Start with **Users** on the far left.
2. Draw **Experience** and **Security Gate** as narrow boxes in the middle-left.
3. Make **Agentic AI Platform** the largest box in the center.
4. Split the next area into two boxes: **Knowledge/RAG** below-left and **Controlled Tools** below-right.
5. Put **Human Approval** below Controlled Tools with an arrow down from it.
6. Draw the large governance boundary last, surrounding the full diagram.

---

## 30-Second Talk Track

> Users interact through familiar channels such as web, mobile, Teams, or the contact center. Every request first passes through identity, role, consent, and PHI/PII controls. A supervisor agent routes the request to the correct specialized agent. The agent uses approved knowledge through RAG and calls enterprise systems only through controlled tools. Any high-impact decision or action requires human approval. Governance, auditability, safety, and monitoring apply across the entire platform.

---

## Feature and Impact Callouts

| Diagram component | What it does | Enterprise impact |
|---|---|---|
| Security Gate | Enforces SSO/MFA, roles, consent, purpose-of-use, and PHI/PII controls. | Protects sensitive health information before an agent can retrieve data or act. |
| Supervisor Agent | Routes work to specialized agents rather than using one generic chatbot. | Improves consistency, control, and accuracy for claims, service, care, provider, and IT workflows. |
| Specialized Agents | Provides focused agents for care navigation, claims, member service, provider support, and IT operations. | Allows incremental rollout by business use case and risk tier. |
| Knowledge / RAG | Retrieves approved policies, benefits information, clinical guidance, SOPs, and runbooks. | Grounds outputs in enterprise knowledge and reduces unsupported answers. |
| Controlled Tools | Connects agents to approved enterprise APIs and systems through a governed layer. | Ensures authentication, authorization, schema validation, rate limits, and audit logging. |
| Human Approval | Requires accountable human review for high-impact actions. | Keeps clinical, claims, payment, and sensitive data actions under appropriate oversight. |
| Governance Boundary | Centralizes policy, safety, observability, cost controls, and evaluations. | Makes agent systems safe, auditable, testable, and scalable across the enterprise. |

---

## Core Design Principle

```text
Agents may reason and recommend autonomously, but access to sensitive data
and execution of consequential actions must remain governed, auditable,
policy-controlled, and human-approved where appropriate.
```

---

## Recommended Initial Use Cases

| Priority | Use case | Risk level | Initial capability |
|---|---|---|---|
| 1 | Employee and provider policy assistant | Low | RAG-only answers from approved documents |
| 2 | IT and platform operations assistant | Low to medium | Runbook search, incident triage, ticket drafting |
| 3 | Claims operations copilot | Medium | Case summarization and missing-information identification; no autonomous decisions |
| 4 | Member service agent assist | Medium | Grounded response drafting and benefit-policy retrieval |
| 5 | Care navigation support | Medium to high | Approved pathway/resource discovery; no autonomous clinical decisions |
| 6 | Developer platform agent | Medium | Policy-controlled infrastructure and access-request workflows |

---

## Discussion Questions to Prepare For

1. **How is PHI protected?**  
   Identity, roles, consent, purpose-of-use checks, data classification, controlled retrieval, tool authorization, and immutable audit logs operate before and throughout the agent workflow.

2. **Can the agent make a clinical or claims decision?**  
   The target design supports recommendations and workflow assistance. High-impact clinical, claims, payment, and record-changing actions require human approval.

3. **How do we prevent hallucinations?**  
   Use curated knowledge and RAG, require citations where appropriate, evaluate agents before release, restrict tool access, and provide a clear escalation path when knowledge is unavailable.

4. **Why use multiple agents?**  
   Specialized agents have smaller scopes, clearer ownership, tailored guardrails, and more measurable quality than one broad agent.

5. **How do we scale safely?**  
   Treat agents as production software: catalog them, assign owners and risk tiers, test and evaluate them, monitor behavior and cost, and promote changes through controlled CI/CD.
