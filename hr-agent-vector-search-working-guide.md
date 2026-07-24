# HR Agent with Vector Search — Working Guide (Updated July 2026)

> Architecture confirmed against current Google Cloud docs.
> Two previous attempts failed — every root cause is pre-fixed here.
> Expected setup time: 30 minutes.

---

## What We Are Building

```
Employee types a question
        ↓
HR Policy Assistant  (Agent Studio — gemini-2.0-flash)
        ↓
Vertex AI Search Data Store  (Discovery Engine — grounded retrieval)
        ↓
Your 3 HR policy text files in GCS
        ↓
Grounded answer with document citation
```

---

## Why Previous Attempts Failed

| Root cause | Fix |
|---|---|
| Created corpus in RAG Engine — wrong service | Use Vertex AI Search Data Store only — skip RAG Engine entirely |
| IAM not auto-wired | Create data store FIRST in Agent Builder, then create agent — same service, IAM auto-wires |
| Used Gemini 3.5 Flash — restricted on free trial | Use `gemini-2.0-flash` only |
| Location mismatch (`us` vs `global`) | Use `global` for data store — confirmed in current API docs |
| Google Search + URL Context on by default | Turn both OFF before connecting the data store |

---

## STEP 1 — Enable APIs

Go to each link, click **Enable**, wait for the green checkmark.

```
Vertex AI API:
  console.cloud.google.com/apis/library/aiplatform.googleapis.com

Discovery Engine API  ← powers data store, most important:
  console.cloud.google.com/apis/library/discoveryengine.googleapis.com

Cloud Storage API:
  console.cloud.google.com/apis/library/storage.googleapis.com
```

After enabling all three — **wait 3 minutes** before continuing.

---

## STEP 2 — Create HR Documents and Upload to GCS

### 2a. Create a GCS bucket

```
console.cloud.google.com/storage/browser
→ + Create
→ Name:    hr-docs-rohiddev
→ Region:  us-central1
→ All other settings: leave default
→ Create
```

### 2b. Create 3 text files on your computer

**File 1 — save as `pto-policy.txt`:**
```
PTO POLICY

Section 1 - Eligibility
All full-time employees are eligible for PTO from day one of employment.

Section 2 - Accrual
Year 1-2:   15 days per year (1.25 days per month)
Year 3-5:   18 days per year (1.5 days per month)
Year 6-10:  22 days per year (1.83 days per month)
Year 11+:   25 days per year (2.08 days per month)

Section 3 - Carryover
Maximum 5 days may be carried over to the next calendar year.
Unused carryover days expire on March 31 of the following year.

Section 4 - How to Request PTO
Submit all PTO requests through the HR portal.
1 to 2 days:   3 business days notice required
3 to 9 days:   2 weeks notice required
10+ days:      4 weeks notice required
All requests subject to manager approval.
```

**File 2 — save as `parental-leave.txt`:**
```
PARENTAL LEAVE POLICY

Section 1 - Eligibility
Employees must have 12 or more months of continuous service and have worked
at least 1,250 hours in the past 12 months.

Section 2 - Leave Duration
Birth parent (primary caregiver):   16 weeks fully paid
Non-birth parent or co-parent:      8 weeks fully paid
Adoption or foster placement:       8 weeks fully paid

Section 3 - How to Request
Notify your manager and HR at least 30 days before your leave start date.
Send an email to hr@company.com with subject: Parental Leave Request

Section 4 - Benefits Continuation
Health, dental, and vision insurance continues at the same employee cost
during the full leave period.
```

**File 3 — save as `benefits.txt`:**
```
EMPLOYEE BENEFITS GUIDE

Section 1 - Health Insurance
Three plan options: Basic (HMO), Standard (PPO), Premium (PPO Plus)
New hires must enroll within 30 days. Coverage begins on day one.
Monthly employee premium contributions:
  Basic:    $120/month
  Standard: $160/month
  Premium:  $220/month

Section 2 - 401k Retirement Plan
Eligible from first day of employment. No waiting period.
Company match: 100% of first 3% you contribute, 50% of next 2%.
Vesting schedule: 3 years (33% per year starting year one).

Section 3 - Employee Assistance Program (EAP)
Free and confidential counseling, financial advice, and legal consultations.
Up to 6 sessions per issue category per year.
Available 24 hours a day, 7 days a week: 1-800-555-0100

Section 4 - Tuition Reimbursement
Up to $5,250 per calendar year for pre-approved job-related courses.
Minimum grade of B required for reimbursement.
Submit receipts and transcript within 60 days of course completion.
```

### 2c. Upload to GCS

In the bucket you created, click **Upload files** and upload all 3 text files.

---

## STEP 3 — Create the Data Store in Agent Builder

> This is the step that failed in both previous attempts.
> The correct path is Agent Builder → Data Stores — NOT RAG Engine.

**Navigate directly:**
```
console.cloud.google.com/gen-app-builder/data-stores
→ + Create data store
```

**Source selection screen:**
```
Select: Cloud Storage
Click: Continue
```

**Cloud Storage configuration:**
```
GCS path:     gs://hr-docs-rohiddev/
Content type: Unstructured documents
Click: Continue
```

**Data store details:**
```
Data store name:  hr-policy-store
Location:         global    ← use global, not us
Click: Create
```

**Wait for indexing to complete:**

Refresh the Data Stores list every 2–3 minutes.
The Status column must show **Active** before moving to Step 4.
This takes 5–15 minutes.

**Copy the Data Store ID:**
```
Click on hr-policy-store
→ Details or Overview tab
→ Copy the Data Store ID (looks like: hr-policy-store_1234567890)
→ Save it — you need this in Step 5
→ Collection ID is always: default_collection
```

---

## STEP 4 — Create the Agent in Agent Studio

```
GCP Console search bar → type "Agent Platform" or stay in Agent Builder
→ Left nav → Agent Studio  (or Studio → Agents)
→ + Create new agent
```

**Configure the agent:**
```
Display name:  HR Policy Assistant
Region:        global    ← must match data store location
Model:         gemini-2.0-flash    ← do NOT use 3.5 Flash (restricted on free trial)
```

**Paste this into the System Instruction (or Instructions) field:**

```
You are an HR Policy Assistant for Company employees.
Your job is to answer HR policy questions using only the official
policy documents that are provided to you as context.

Guidelines:
1. Answer ONLY from the retrieved documents. If a topic is not covered,
   respond: "I don't have information on that topic. Please contact HR
   directly at hr@company.com."
2. Always cite your source: for example, "Per the PTO Policy, Section 2..."
3. Never speculate, estimate, or guess beyond what the documents say.
4. For sensitive topics (harassment, discrimination, complaints, termination,
   individual salary), always say: "Please speak directly with your HR
   Business Partner for this matter."
5. Never reference, reveal, or discuss individual employee records,
   salaries, performance reviews, or personal data.

Tone: professional, clear, and empathetic on sensitive topics.
```

Click **Save**.

---

## STEP 5 — Connect the Data Store and Disable Web Tools

After saving, look at the agent configuration panel on the right.

**Turn off web tools first:**
```
Under Tools:
  Google Search  → toggle to OFF (must be grey/off)
  URL Context    → toggle to OFF (must be grey/off)
```

> If you leave these on, the agent uses the web instead of your HR docs.

**Add the data store:**
```
Under Tools → click + or "Add tool"
→ Select: Vertex AI Search Data Store
→ Fill in the fields:
    Project:         rohiddev         (or your project ID)
    Location:        global
    Collection:      default_collection
    Data store ID:   hr-policy-store_1234567890   (from Step 3)
→ Confirm / Add
```

Click **Save**.

> IAM is auto-wired because both the data store and the agent were created
> inside Agent Builder. No manual IAM grant is needed.

---

## STEP 6 — Test in the Preview Panel

Click **Preview** or **Test** at the top of the Agent Studio canvas.

**Test 1 — Basic policy lookup:**
```
You: How many PTO days do I get in my first year?

Expected: Per the PTO Policy (Section 2), employees in years 1-2
          receive 15 days per year, which is 1.25 days per month.
```

**Test 2 — Not in documents:**
```
You: What is the company car policy?

Expected: I don't have information on that topic.
          Please contact HR directly at hr@company.com.
```

**Test 3 — Sensitive escalation:**
```
You: How do I report my manager for harassment?

Expected: Please speak directly with your HR Business Partner
          for this matter.
```

**Test 4 — 401k:**
```
You: What is the 401k match?

Expected: Per the Benefits Guide (Section 2), the company matches
          100% of your first 3% and 50% of the next 2% you contribute.
          Vesting takes 3 years.
```

**Test 5 — Parental leave:**
```
You: I am expecting a baby. How long is my parental leave?

Expected: Per the Parental Leave Policy (Section 2), birth parents
          (primary caregiver) receive 16 weeks fully paid.
          You need to notify HR at least 30 days before your leave date.
```

---

## Troubleshooting — InternalError Checklist

Work through this in order. Stop at the first item that is wrong.

```
☐ 1. Model is gemini-2.0-flash? (not 3.5 Flash, not 1.5)
☐ 2. Agent is saved? (click Save top right)
☐ 3. Data store Status is Active? (Agent Builder → Data Stores)
☐ 4. Data store location is global? (not us, not us-central1)
☐ 5. Agent region is global? (matches data store)
☐ 6. Google Search is OFF?
☐ 7. URL Context is OFF?
☐ 8. Data Store ID copied from Agent Builder (not RAG Engine)?
```

**Isolation test:** Remove the data store tool, click Save, type "hello".
- If "hello" works → problem is the data store connection (check items 3-8)
- If "hello" fails → problem is model or agent config (check items 1-2)

---

## Clean Up After Testing

To avoid charges:

```
Agent Builder → Data Stores → hr-policy-store → Delete
Agent Builder → Agent Studio → HR Policy Assistant → Delete
Cloud Storage → hr-docs-rohiddev bucket → Delete bucket
```

Or shut down the entire project (removes everything):
```
GCP Console → IAM & Admin → Settings → Shut down project
```
hr-policy-store_1784029261487