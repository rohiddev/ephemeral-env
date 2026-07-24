# Building a Simple HR Agent in Google Gemini Agent Platform

> Platform: Google Cloud → Agent Platform (Vertex AI Agent Builder)
> Scope: HR policy Q&A agent — answers employee questions grounded in HR documents
> Approach: UI-only, no code required

---

## What We Are Building

```
Employee asks:  "How many PTO days do I get in my first year?"
        ↓
HR Agent fetches relevant chunks from HR policy corpus (RAG Engine)
        ↓
Gemini reads the chunks and generates a grounded, cited answer
        ↓
Employee gets: "Per the PTO Policy (Section 2.1), full-time employees
               accrue 15 days of PTO in their first year..."
```

The agent will:
- Answer questions about PTO, benefits, leave, onboarding, payroll schedule
- Cite which document it is drawing from
- Refuse to speculate on information not in the HR corpus
- Escalate to HR team when the question is outside its scope

---

## Prerequisites

- Google Cloud project owned by an organization (not personal)
- Billing enabled on the project
- Your account has roles: `Vertex AI User` + `Storage Object Admin`

**APIs to enable** (GCP Console → APIs & Services → Enable APIs):
```
Vertex AI API
Cloud Storage API
Discovery Engine API
Vector Search API     ← aiplatform.googleapis.com (also listed as vectorsearch.googleapis.com)
```

> **Enable Vector Search directly:**
> https://console.developers.google.com/apis/api/vectorsearch.googleapis.com/overview?project=483763792704
>
> After enabling, wait 2–3 minutes before retrying corpus creation.
> The API propagation is not instant — retry too quickly and you will see the same error.

---

## STEP 1 — Prepare the HR Document Corpus

Before creating the agent, you need documents for it to search.

### 1a. Create a GCS bucket for HR documents

```
GCP Console → Cloud Storage → Create Bucket
Name:    hr-policy-corpus-[your-project-id]    hr-policy-corpus-rohiddev
Region:  us-central1
Class:   Standard
```

### 1b. Upload HR documents

Upload any of the following (PDF, DOCX, TXT, HTML all supported):
- PTO and leave policy
- Benefits guide
- Employee handbook
- Payroll schedule
- Onboarding checklist
- Code of conduct

**If you do not have real documents yet**, use the sample policy text at the end of this document (Section 9). Save each block as a `.txt` file and upload to the bucket.

---

## STEP 2 — Create the RAG Corpus

The RAG Engine indexes your documents and makes them searchable by the agent.

```
Left nav → RAG Engine → Create Corpus
```

**Configuration:**
```
Name:           hr-policy-corpus
Description:    HR policy documents for employee Q&A
Embedding model: text-embedding-004  (Google's latest, 768-dim)
```

> **⚠ New project error — Spanner mode restricted**
> If you see: *"For new projects, using Spanner mode is restricted to only allowlisted projects"*
> Fix: On the Create Corpus screen, look for **Backend / Mode** and select **Serverless** instead of Spanner.
> Serverless mode works immediately for all projects. Spanner mode requires Google allowlisting.
>
> If the UI does not show a mode selector, use this region instead: **us-west1**
> (Serverless is available in all supported regions outside us-central1/us-east1/us-east4 without restriction)

**Serverless mode — what changes:**
- Same API, same retrieval quality
- No persistent vector index (index rebuilt on each query from stored embeddings)
- Slightly higher per-query latency (~200ms more) — acceptable for HR Q&A workloads
- No allowlisting required — works immediately

**Add data source:**
```
Source type:    Google Cloud Storage
GCS path:       gs://hr-policy-corpus-[your-project-id]/
```

Click **Create**. Indexing takes 5–15 minutes depending on document size.

**Verify:** Once complete, the corpus status shows "Active" and the chunk count appears. You can run a test query directly from the RAG Engine UI before connecting to the agent.

---

## STEP 3 — Create the HR Agent

```
Left nav → Agents → + New Agent
```

**Basic configuration:**
```
Agent name:     HR Policy Assistant
Description:    Answers employee HR policy questions grounded in official documents
Model:          gemini-2.0-flash   (fast + cost-effective for Q&A)
Region:         us-central1
```

---

## STEP 4 — Write the Agent Instructions (System Prompt)

This is the most important configuration step. Paste this into the **Instructions** field:

```
You are an HR Policy Assistant for [Company Name]. Your role is to help employees 
find accurate answers to HR policy questions based on official company documents.

BEHAVIOR RULES:
1. Answer ONLY from the information in the provided HR documents. 
   If the answer is not in the documents, say so explicitly.
2. Always cite the document name and section when you provide an answer.
   Example: "According to the PTO Policy (Section 2.1)..."
3. Never speculate, estimate, or fill in gaps with general knowledge.
   If a policy document is ambiguous, say: "The policy document is not specific 
   on this point. I recommend contacting HR directly at hr@company.com."
4. Be concise. Lead with the direct answer, then provide context.
5. For sensitive topics (termination, disciplinary action, legal rights),
   always end with: "For your specific situation, please speak with an HR Business 
   Partner directly."
6. Do not answer questions about individual employee records, salaries, 
   performance reviews, or any personal data. Redirect to HR.

TONE:
- Professional but approachable
- Clear and plain language — avoid HR jargon where possible
- Empathetic on sensitive topics (bereavement, medical leave, etc.)

ESCALATION:
If an employee's question involves a complaint, harassment claim, or legal matter,
respond: "This type of concern is best handled directly and confidentially by HR. 
Please contact your HR Business Partner or use the ethics hotline at [number]."

SCOPE OF KNOWLEDGE:
- PTO accrual, carryover, and usage
- Medical, dental, vision benefits enrollment
- Parental and family leave
- Bereavement leave
- FMLA eligibility and process
- Holiday schedule
- Payroll schedule and direct deposit
- Onboarding steps for new hires
- Employee referral program
- Code of conduct basics
```

---

## STEP 5 — Connect RAG Corpus as a Tool (Grounding)

> **UI Note:** The Tools panel shows two sections: built-in toggles (Google Search, URL Context)
> and MCP tools (Vertex AI Search Data Store, MCP Server).
> There is no separate "RAG" option — your RAG corpus connects via **Vertex AI Search Data Store**.

### 5a — Disable Google Search and URL Context

**Critical:** Both Google Search and URL Context are ON by default (blue toggles).
Turn them both OFF.

```
Tools panel → Google Search       → toggle OFF
Tools panel → URL Context         → toggle OFF
```

Why: if these are left on, the agent will search the public web and browse URLs to answer
HR questions — pulling in generic HR advice instead of your company's actual policies.
An employee asking about PTO carryover should get YOUR policy, not a general article.

### 5b — Connect your RAG corpus via Vertex AI Search Data Store

```
Tools panel → MCP section → Vertex AI Search Data Store → click +
```

You will be prompted to select or create a data store. Select the corpus created in Step 2:
```
Data store:   hr-policy-corpus
```

If the corpus does not appear in the list, it may still be indexing. Wait for the RAG Engine
corpus status to show "Active" then return to this step.

**What this does:** The agent now has a grounding tool called `Vertex AI Search Data Store`.
When an employee asks a question, the agent automatically searches this store first,
retrieves the top matching document chunks, and uses them as context before generating
a response. Answers are grounded in your HR documents only.

---

## STEP 6 — Configure Safety Settings

```
Agent configuration → Safety → Configure
```

Recommended settings for HR agent:

| Category | Setting |
|---|---|
| Harassment | Block medium and above |
| Hate speech | Block medium and above |
| Sexually explicit | Block low and above |
| Dangerous content | Block medium and above |
| PII in response | Enable PII detection |

---

## STEP 7 — Test in the Agent Simulator

The simulator is the chat panel on the right side of the agent configuration screen.

**Test these questions in order:**

```
Test 1 — Basic policy lookup:
"How many PTO days do I get per year?"

Expected: Cites PTO Policy section, gives accrual rate

Test 2 — Policy not in documents:
"What is the company car policy?"

Expected: "I don't have information on this in the HR documents. 
Please contact HR at hr@company.com."

Test 3 — Sensitive topic:
"I want to report my manager for harassment."

Expected: Escalation response — directs to HR Business Partner or ethics hotline

Test 4 — Personal data request:
"Can you tell me how much my colleague earns?"

Expected: Declines, redirects to HR

Test 5 — Multi-part question:
"I'm pregnant. What leave am I entitled to and when do I need to notify HR?"

Expected: Parental leave policy details + FMLA eligibility + notification timeline, 
          with empathetic tone and suggestion to speak with HR BP
```

**Iterate:** If any answer is wrong or cites incorrectly, refine the Instructions (Step 4) and retest. Common fixes:
- Agent speculates → add "Never speculate" rule more explicitly
- Agent answer too long → add "Be concise, lead with the direct answer"
- Agent misses a document → check RAG corpus indexing status

---

## STEP 8 — Register in Agent Registry

```
Left nav → Govern → Agent Registry → Register Agent
```

```
Agent name:    HR Policy Assistant
Owner:         hr-platform-team
Version:       1.0
Risk level:    Low  (read-only, no write actions)
Tools:         search_hr_policies (RAG)
Data access:   HR policy corpus (non-PII documents only)
```

This makes the agent visible to the governance team and creates an audit trail.

---

## STEP 9 — Deploy

```
Left nav → Scale → Deployments → + New Deployment
```

```
Deployment name:   hr-agent-prod
Agent:             HR Policy Assistant
Version:           1.0
Region:            us-central1
Traffic:           100% to v1.0
```

Click **Deploy**. You get a REST endpoint:
```
https://[region]-aiplatform.googleapis.com/v1/projects/[project]/locations/[region]/agents/[agent-id]:streamQuery
```

Share this endpoint with your frontend team or embed it in your employee portal / intranet.

---

## STEP 10 — Set Up Evaluation (Optional but Recommended)

```
Left nav → Optimize → Evaluation → + New Evaluation
```

Create a golden dataset — 20 question/answer pairs you know are correct:

```json
[
  {
    "question": "How many PTO days do full-time employees get in year one?",
    "expected_answer": "15 days",
    "document_source": "PTO Policy Section 2.1"
  },
  {
    "question": "When does parental leave begin?",
    "expected_answer": "Parental leave can begin up to 4 weeks before the expected due date",
    "document_source": "Parental Leave Policy Section 1.2"
  }
]
```

Run this evaluation before every agent update. Only promote a new version if it scores ≥ the previous version on this dataset.

---

## Sample HR Policy Documents for the Corpus

Copy each block below into a separate `.txt` file and upload to your GCS bucket.

---

### File: pto-policy.txt

```
PTO POLICY — Effective January 2026

Section 1 — Eligibility
All full-time employees working 30+ hours per week are eligible for Paid Time Off (PTO)
beginning on their first day of employment.

Section 2 — Accrual Rates
2.1 Years 1–2:     15 days (120 hours) per year, accrued at 1.25 days per month
2.2 Years 3–5:     18 days (144 hours) per year, accrued at 1.5 days per month
2.3 Years 6–10:    22 days (176 hours) per year, accrued at 1.83 days per month
2.4 Years 11+:     25 days (200 hours) per year, accrued at 2.08 days per month

Part-time employees accrue PTO on a pro-rated basis proportional to their scheduled hours.

Section 3 — Carryover
Employees may carry over up to 5 days (40 hours) of unused PTO into the next calendar year.
Carryover days must be used by March 31 of the new year or they are forfeited.

Section 4 — PTO Request Process
4.1 Requests of 1–2 days: submit at least 3 business days in advance
4.2 Requests of 3–9 days: submit at least 2 weeks in advance
4.3 Requests of 10+ days: submit at least 4 weeks in advance
All requests are subject to manager approval based on business need.

Section 5 — PTO Payout on Separation
Upon separation, employees will be paid out accrued, unused PTO up to a maximum of 
10 days (80 hours) at their current base rate of pay.
```

---

### File: parental-leave-policy.txt

```
PARENTAL LEAVE POLICY — Effective January 2026

Section 1 — Eligibility
1.1 All employees who have been employed for at least 12 months and worked a minimum
    of 1,250 hours in the past 12 months are eligible for parental leave.
1.2 Leave may begin up to 4 weeks before the expected due date for birth parents,
    or on the date of adoption/foster placement for other parents.

Section 2 — Duration
2.1 Birth parent (primary caregiver):  16 weeks fully paid
2.2 Non-birth parent / secondary:      8 weeks fully paid
2.3 Adoption or foster placement:      8 weeks fully paid for all parents

Section 3 — Pay During Leave
Parental leave is fully paid at 100% of base salary.
Parental leave runs concurrently with FMLA where applicable.

Section 4 — Notification Requirements
4.1 Employees must notify HR and their manager at least 30 days before the 
    anticipated leave start date, or as soon as practicable.
4.2 Notification: email hr@company.com with subject "Parental Leave Request"
    Include: expected leave start date, expected return date, primary or secondary status

Section 5 — Benefits During Leave
Health, dental, and vision benefits continue at the same employee cost during leave.
401(k) contributions continue if payroll deductions are active.

Section 6 — Return to Work
Employees returning from parental leave are guaranteed return to the same or an
equivalent position at the same pay and benefits level.
```

---

### File: benefits-guide.txt

```
EMPLOYEE BENEFITS GUIDE — 2026

Section 1 — Health Insurance
The company offers three health plan tiers: Basic (HMO), Standard (PPO), Premium (PPO+)
Open enrollment: November 1–15 each year. Changes effective January 1.
New hires enroll within 30 days of start date. Coverage begins day 1 of employment.
Employee premium contributions (monthly):
  Basic:    Employee $120 | Employee + Spouse $280 | Family $380
  Standard: Employee $160 | Employee + Spouse $370 | Family $490
  Premium:  Employee $220 | Employee + Spouse $480 | Family $640

Section 2 — Dental and Vision
Dental: Two plans available — Basic (preventive only) and Comprehensive.
Vision: One plan — covers annual eye exam, $200 frame allowance, contact lens allowance.

Section 3 — 401(k) Retirement Plan
Employees are eligible to enroll from day 1.
Company match: 100% of first 3% contributed, 50% of next 2% contributed.
Vesting: Company match vests over 3 years (33% per year).
Enrollment: Fidelity NetBenefits portal or contact benefits@company.com

Section 4 — Employee Assistance Program (EAP)
Free and confidential counseling, financial advice, and legal consultation.
Up to 6 sessions per issue per year at no cost to the employee.
Available 24/7: 1-800-XXX-XXXX or eap.company.com

Section 5 — Tuition Reimbursement
Up to $5,250 per calendar year for approved courses.
Courses must be relevant to current or future role.
Grade of B or better required for reimbursement.
Submit receipts and transcript to hr@company.com within 60 days of course completion.
```

---

### File: leave-policy.txt

```
LEAVE OF ABSENCE POLICY — 2026

Section 1 — FMLA (Family and Medical Leave Act)
Eligibility: 12 months of employment + 1,250 hours worked in past 12 months
Duration: Up to 12 weeks unpaid, job-protected leave per year
Qualifying reasons:
  - Serious health condition of employee
  - Care for spouse, child, or parent with serious health condition
  - Birth, adoption, or foster placement of a child
  - Qualifying military exigency

Section 2 — Medical Leave (non-FMLA)
For employees not yet FMLA-eligible or who have exhausted FMLA:
Short-term disability (STD): 60% of base salary for up to 12 weeks
Long-term disability (LTD): 60% of base salary after 12 weeks, up to age 65

Section 3 — Bereavement Leave
Immediate family (spouse, child, parent, sibling): 5 paid days
Extended family (grandparent, in-law, aunt/uncle): 3 paid days
Close friend or colleague: 1 paid day (manager discretion)
Additional unpaid time may be granted at manager discretion.

Section 4 — Jury Duty
Full pay maintained during jury service for up to 10 business days.
Beyond 10 days: employee receives jury compensation, company pays the difference 
up to full base salary.
Provide jury summons to HR within 5 days of receipt.

Section 5 — Military Leave
Unpaid military leave granted in accordance with USERRA.
Benefits continuation available at employee's cost during deployment.
Position guaranteed upon return per USERRA requirements.
```

---

### File: holiday-payroll-schedule.txt

```
HOLIDAY SCHEDULE AND PAYROLL — 2026

Section 1 — Company Holidays 2026
New Year's Day:          January 1 (Thursday)
Martin Luther King Day:  January 19 (Monday)
Presidents' Day:         February 16 (Monday)
Memorial Day:            May 25 (Monday)
Juneteenth:              June 19 (Friday)
Independence Day:        July 4 (Saturday) — observed July 3 (Friday)
Labor Day:               September 7 (Monday)
Thanksgiving:            November 26 (Thursday)
Day after Thanksgiving:  November 27 (Friday)
Christmas Eve:           December 24 (Thursday)
Christmas Day:           December 25 (Friday)

If a holiday falls on Saturday, it is observed on Friday.
If a holiday falls on Sunday, it is observed on Monday.

Section 2 — Payroll Schedule
Pay frequency: Bi-weekly (every other Friday)
Pay period: Monday through Sunday, paid 5 business days after period close
Direct deposit: Available — enroll via payroll portal or submit voided check to payroll@company.com
Paper checks: Available upon request, mailed to address on file

Section 3 — Time Reporting
Non-exempt employees must submit timesheets by Sunday 11:59 PM of each pay period.
Late timesheet submission may delay payment by one pay cycle.
Overtime (hours over 40/week) must be pre-approved by manager.
```

---

## Architecture Summary

```
Employee (browser / intranet / Slack)
        ↓ question
Gemini Agent Platform — HR Policy Assistant
        ↓ search_hr_policies tool call
RAG Engine — hr-policy-corpus
        ↓ top-5 relevant chunks from HR documents
Agent assembles context + system prompt + employee question
        ↓
Gemini 2.0 Flash generates grounded answer with citation
        ↓ response
Employee receives answer with document source reference
```

**Total setup time:** ~2 hours (mostly waiting for RAG corpus indexing)
**Ongoing cost:** Gemini Flash API calls (~$0.0001 per query) + Vector Search OCU (~$0.10/hr)

==
Data store ID
hr-search-store_1783992014984
==