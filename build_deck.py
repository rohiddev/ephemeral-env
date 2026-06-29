"""
Build: Agentic AI — Executive Overview deck
Output: agentic-ai-overview.pptx
"""

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt
import copy

# ── Brand palette ─────────────────────────────────────────────────────────────
NAVY       = RGBColor(0x0D, 0x1B, 0x2A)   # slide backgrounds / headers
TEAL       = RGBColor(0x00, 0xA8, 0x9C)   # accent / highlights
WHITE      = RGBColor(0xFF, 0xFF, 0xFF)
LIGHT_GRAY = RGBColor(0xF2, 0xF4, 0xF6)
MID_GRAY   = RGBColor(0x6C, 0x75, 0x7D)
DARK_GRAY  = RGBColor(0x2C, 0x3E, 0x50)
AMBER      = RGBColor(0xFF, 0xB7, 0x00)   # call-out boxes

prs = Presentation()
prs.slide_width  = Inches(13.33)
prs.slide_height = Inches(7.5)

BLANK = prs.slide_layouts[6]   # truly blank layout


# ── Helper: solid fill on shape ───────────────────────────────────────────────
def solid(shape, color):
    shape.fill.solid()
    shape.fill.fore_color.rgb = color


# ── Helper: add rectangle ─────────────────────────────────────────────────────
def rect(slide, l, t, w, h, color):
    s = slide.shapes.add_shape(1, Inches(l), Inches(t), Inches(w), Inches(h))
    solid(s, color)
    s.line.fill.background()
    return s


# ── Helper: text box ──────────────────────────────────────────────────────────
def tb(slide, text, l, t, w, h,
       size=18, bold=False, color=WHITE, align=PP_ALIGN.LEFT, wrap=True):
    txb = slide.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h))
    txb.word_wrap = wrap
    tf  = txb.text_frame
    tf.word_wrap = wrap
    p   = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.size  = Pt(size)
    run.font.bold  = bold
    run.font.color.rgb = color
    return txb


def tb_lines(slide, lines, l, t, w, h,
             size=16, color=WHITE, bold_first=False, spacing=1.2):
    """Multiple lines with optional bold first line."""
    txb = slide.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h))
    txb.word_wrap = True
    tf = txb.text_frame
    tf.word_wrap = True
    for i, line in enumerate(lines):
        p = tf.add_paragraph() if i > 0 else tf.paragraphs[0]
        p.space_after = Pt(4)
        run = p.add_run()
        run.text = line
        run.font.size  = Pt(size)
        run.font.color.rgb = color
        run.font.bold  = (i == 0 and bold_first)
    return txb


def divider(slide, t, color=TEAL, l=0.4, w=12.5, h=0.05):
    rect(slide, l, t, w, h, color)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 1 — TITLE
# ══════════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(BLANK)
rect(s, 0, 0, 13.33, 7.5, NAVY)           # full background
rect(s, 0, 0, 13.33, 0.08, TEAL)          # top accent bar
rect(s, 0, 7.42, 13.33, 0.08, TEAL)       # bottom accent bar

# Left teal column
rect(s, 0, 0, 0.5, 7.5, TEAL)

tb(s, "Agentic AI", 1.0, 1.6, 11.0, 1.1,
   size=52, bold=True, color=WHITE)
tb(s, "From LLM Calls to Autonomous Enterprise Agents",
   1.0, 2.8, 10.5, 0.7, size=24, color=TEAL)
divider(s, 3.7, LIGHT_GRAY, l=1.0, w=10.0, h=0.04)
tb(s, "Executive Overview  |  LangChain · LangGraph · Google ADK",
   1.0, 3.9, 11.0, 0.5, size=16, color=MID_GRAY)
tb(s, "Rohid Dev  ·  github.com/rohiddev",
   1.0, 6.7, 8.0, 0.4, size=13, color=MID_GRAY)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 2 — AGENDA
# ══════════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(BLANK)
rect(s, 0, 0, 13.33, 7.5, LIGHT_GRAY)
rect(s, 0, 0, 13.33, 1.1, NAVY)
rect(s, 0, 0, 0.5, 7.5, TEAL)
tb(s, "Agenda", 1.0, 0.2, 10.0, 0.7, size=30, bold=True, color=WHITE)

items = [
    ("01", "What Is an AI Agent?",             "LLM call vs agent — the key shift"),
    ("02", "The Agent Loop",                   "ReAct pattern, tools, stopping conditions"),
    ("03", "Memory & State",                   "In-context, external, episodic, semantic"),
    ("04", "Multi-Agent Systems",              "Supervisor, parallel dispatch, fan-out/fan-in"),
    ("05", "RAG · Graph RAG · Agentic RAG",    "Retrieval patterns and when to use each"),
    ("06", "Framework Landscape",              "LangChain vs LangGraph vs Google ADK"),
    ("07", "Safety & Guardrails",              "PHI, prompt injection, least privilege"),
    ("08", "Evaluation & Observability",       "Tracing, LLM-as-judge, production metrics"),
    ("09", "Key Takeaways",                    "Decision guide and next steps"),
]

row_h = 0.54
for i, (num, title, sub) in enumerate(items):
    top = 1.25 + i * row_h
    bg_color = WHITE if i % 2 == 0 else LIGHT_GRAY
    rect(s, 0.6, top, 12.2, row_h - 0.04, bg_color)
    # number badge
    badge = s.shapes.add_shape(1, Inches(0.7), Inches(top + 0.08),
                                Inches(0.42), Inches(0.38))
    solid(badge, TEAL)
    badge.line.fill.background()
    tf = badge.text_frame
    tf.paragraphs[0].alignment = PP_ALIGN.CENTER
    run = tf.paragraphs[0].add_run()
    run.text = num
    run.font.size = Pt(12)
    run.font.bold = True
    run.font.color.rgb = WHITE

    tb(s, title, 1.25, top + 0.05, 5.5, 0.35,
       size=14, bold=True, color=DARK_GRAY)
    tb(s, sub,   6.9,  top + 0.1,  5.8, 0.3,
       size=12, color=MID_GRAY)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 3 — WHAT IS AN AGENT?
# ══════════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(BLANK)
rect(s, 0, 0, 13.33, 7.5, NAVY)
rect(s, 0, 0, 0.5, 7.5, TEAL)
tb(s, "01  |  What Is an AI Agent?", 1.0, 0.2, 11.0, 0.6,
   size=26, bold=True, color=WHITE)
divider(s, 0.95)

# Left column — LLM call
rect(s, 0.6, 1.1, 5.5, 5.8, DARK_GRAY)
tb(s, "Plain LLM Call", 0.8, 1.2, 5.0, 0.5,
   size=17, bold=True, color=TEAL)
tb_lines(s, [
    "Send prompt  →  get response  →  done.",
    "",
    "  Stateless",
    "  One-shot — no loop",
    "  No tools — cannot act",
    "  No memory across turns",
    "  Cannot retry or adapt",
], 0.75, 1.75, 5.3, 4.5, size=14, color=LIGHT_GRAY)

# Right column — Agent
rect(s, 6.8, 1.1, 5.9, 5.8, DARK_GRAY)
tb(s, "AI Agent", 7.0, 1.2, 5.5, 0.5,
   size=17, bold=True, color=TEAL)
tb_lines(s, [
    "LLM  +  Loop  +  Tools  +  Memory",
    "",
    "  Reasons about next step",
    "  Calls tools — acts in the world",
    "  Observes results, iterates",
    "  Retains context across turns",
    "  Stops when problem is solved",
], 7.0, 1.75, 5.5, 4.5, size=14, color=LIGHT_GRAY)

# VS badge
badge = s.shapes.add_shape(1, Inches(6.0), Inches(3.6),
                             Inches(0.7), Inches(0.7))
solid(badge, TEAL)
badge.line.fill.background()
tf = badge.text_frame
tf.paragraphs[0].alignment = PP_ALIGN.CENTER
run = tf.paragraphs[0].add_run()
run.text = "VS"
run.font.size = Pt(16)
run.font.bold = True
run.font.color.rgb = WHITE

# Bottom definition box
rect(s, 0.6, 7.0, 12.1, 0.38, TEAL)
tb(s, 'Agent = "A system that perceives, reasons, acts, and remembers — in a loop."',
   0.8, 7.02, 11.8, 0.35, size=13, bold=True, color=NAVY)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 4 — THE AGENT LOOP (ReAct)
# ══════════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(BLANK)
rect(s, 0, 0, 13.33, 7.5, LIGHT_GRAY)
rect(s, 0, 0, 13.33, 1.1, NAVY)
rect(s, 0, 0, 0.5, 7.5, TEAL)
tb(s, "02  |  The Agent Loop — ReAct Pattern", 1.0, 0.2, 11.0, 0.6,
   size=26, bold=True, color=WHITE)

# Loop boxes
steps = [
    ("THOUGHT",      "LLM reasons about\nwhat to do next",       NAVY),
    ("ACTION",       "LLM picks a tool\nand provides arguments", TEAL),
    ("OBSERVATION",  "Tool executes.\nResult returned to LLM",   DARK_GRAY),
    ("FINAL ANSWER", "No more tool calls.\nLoop exits.",          AMBER),
]
box_w, box_h = 2.6, 2.2
gap = 0.35
start_x = 0.65
for i, (label, desc, color) in enumerate(steps):
    x = start_x + i * (box_w + gap)
    rect(s, x, 1.3, box_w, box_h, color)
    tb(s, label, x + 0.1, 1.4, box_w - 0.2, 0.45,
       size=15, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    divider(s, 1.88, WHITE, l=x + 0.1, w=box_w - 0.2, h=0.03)
    tb(s, desc, x + 0.15, 1.95, box_w - 0.3, 1.3,
       size=13, color=WHITE, align=PP_ALIGN.CENTER)

    # Arrow between boxes
    if i < 3:
        ax = x + box_w + 0.02
        tb(s, "→", ax, 2.0, gap + 0.1, 0.5,
           size=22, bold=True, color=TEAL, align=PP_ALIGN.CENTER)

# Loop-back arrow label
tb(s, "↺  Loops back to THOUGHT until final answer is reached",
   0.65, 3.65, 12.0, 0.4, size=14, color=DARK_GRAY, align=PP_ALIGN.CENTER)

# Example box
rect(s, 0.65, 4.15, 12.0, 3.1, WHITE)
tb(s, "Concrete Example", 0.85, 4.25, 4.0, 0.4,
   size=15, bold=True, color=NAVY)
divider(s, 4.7, TEAL, l=0.75, w=11.7, h=0.04)
example_lines = [
    'User: "What is the weather in Tokyo and convert to Celsius?"',
    "",
    "THOUGHT   I need the Tokyo weather first.",
    "ACTION    get_weather(city='Tokyo')   →   OBSERVATION: 80°F, sunny",
    "THOUGHT   Now I convert 80°F to Celsius.",
    "ACTION    calculate('(80-32)*5/9')   →   OBSERVATION: 26.67",
    "FINAL     The weather in Tokyo is 26.67°C, sunny.",
]
tb_lines(s, example_lines, 0.85, 4.75, 11.8, 2.3,
         size=13, color=DARK_GRAY)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 5 — MEMORY & STATE
# ══════════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(BLANK)
rect(s, 0, 0, 13.33, 7.5, NAVY)
rect(s, 0, 0, 0.5, 7.5, TEAL)
tb(s, "03  |  Memory & State", 1.0, 0.2, 11.0, 0.6,
   size=26, bold=True, color=WHITE)
divider(s, 0.95)

memory_types = [
    ("In-Context\n(Short-Term)",
     "Current conversation in the\ncontext window.\nEphemeral — clears each session.",
     "Context window limit\n(e.g. 200K tokens for Claude)"),
    ("External\n(Long-Term)",
     "Vector DB, relational DB,\nkey-value store.\nPersists across all sessions.",
     "Retrieved via RAG or\nlookup tool at query time"),
    ("Episodic\n(Session)",
     "This conversation, persisted\nby thread_id / session_id.\nResumable after interruption.",
     "LangGraph: MemorySaver\nADK: SessionService"),
    ("Semantic\n(Knowledge Base)",
     "Shared facts and domain\nknowledge for all users.\nHR policies, product docs, etc.",
     "Retrieved via RAG.\nGround truth for the agent"),
]

box_w = 2.85
for i, (title, desc, impl) in enumerate(memory_types):
    x = 0.6 + i * (box_w + 0.22)
    rect(s, x, 1.1, box_w, 5.1, DARK_GRAY)
    rect(s, x, 1.1, box_w, 0.7, TEAL)
    tb(s, title, x + 0.1, 1.12, box_w - 0.2, 0.65,
       size=13, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    tb(s, desc, x + 0.15, 1.9, box_w - 0.3, 2.2,
       size=12, color=LIGHT_GRAY)
    divider(s, 4.2, MID_GRAY, l=x + 0.15, w=box_w - 0.3, h=0.03)
    tb(s, impl, x + 0.15, 4.3, box_w - 0.3, 1.7,
       size=11, color=AMBER)

# Bottom callout
rect(s, 0.6, 6.35, 12.1, 0.85, TEAL)
tb(s, "Production best practice: use ALL FOUR together.\n"
      "In-context for coherence  |  Episodic for continuity  |  Semantic for accuracy  |  External for user data",
   0.8, 6.42, 11.8, 0.75, size=12, bold=False, color=NAVY)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 6 — MULTI-AGENT SYSTEMS
# ══════════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(BLANK)
rect(s, 0, 0, 13.33, 7.5, LIGHT_GRAY)
rect(s, 0, 0, 13.33, 1.1, NAVY)
rect(s, 0, 0, 0.5, 7.5, TEAL)
tb(s, "04  |  Multi-Agent Systems", 1.0, 0.2, 11.0, 0.6,
   size=26, bold=True, color=WHITE)

# Supervisor box (top center)
rect(s, 4.9, 1.25, 3.4, 1.0, NAVY)
tb(s, "SUPERVISOR AGENT", 4.9, 1.3, 3.4, 0.4,
   size=13, bold=True, color=TEAL, align=PP_ALIGN.CENTER)
tb(s, "Classify intent  →  Route  →  Aggregate",
   4.9, 1.7, 3.4, 0.45, size=11, color=WHITE, align=PP_ALIGN.CENTER)

# Arrows down
for x in [1.5, 4.6, 7.7, 10.8]:
    tb(s, "↓", x + 0.4, 2.35, 0.5, 0.5,
       size=20, bold=True, color=TEAL, align=PP_ALIGN.CENTER)

# Specialist boxes
specialists = [
    ("HR Policy",      "PTO · Leave\nParental policy"),
    ("Benefits",       "Health · Dental\n401k · FSA"),
    ("Payroll",        "Salary · Pay dates\nDeductions"),
    ("IT Support",     "VPN · Access\nHardware"),
]
box_w_s = 2.7
for i, (name, detail) in enumerate(specialists):
    x = 0.55 + i * (box_w_s + 0.35)
    rect(s, x, 2.9, box_w_s, 1.7, DARK_GRAY)
    rect(s, x, 2.9, box_w_s, 0.45, TEAL)
    tb(s, name, x + 0.1, 2.93, box_w_s - 0.2, 0.4,
       size=13, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    tb(s, detail, x + 0.1, 3.4, box_w_s - 0.2, 1.1,
       size=12, color=LIGHT_GRAY, align=PP_ALIGN.CENTER)

# Arrows up to aggregator
for x in [1.5, 4.6, 7.7, 10.8]:
    tb(s, "↑", x + 0.4, 4.65, 0.5, 0.5,
       size=20, bold=True, color=TEAL, align=PP_ALIGN.CENTER)

# Aggregator
rect(s, 4.9, 5.2, 3.4, 0.85, NAVY)
tb(s, "AGGREGATOR", 4.9, 5.25, 3.4, 0.35,
   size=13, bold=True, color=TEAL, align=PP_ALIGN.CENTER)
tb(s, "Merge  →  Deduplicate  →  Cite sources",
   4.9, 5.6, 3.4, 0.4, size=11, color=WHITE, align=PP_ALIGN.CENTER)

# Arrow to final answer
tb(s, "↓", 6.3, 6.1, 0.6, 0.5, size=20, bold=True, color=TEAL)
rect(s, 3.5, 6.65, 6.3, 0.6, TEAL)
tb(s, "Unified Answer with citations", 3.5, 6.7, 6.3, 0.5,
   size=14, bold=True, color=NAVY, align=PP_ALIGN.CENTER)

# "Parallel" label
rect(s, 0.55, 4.62, 12.15, 0.32, AMBER)
tb(s, "All specialist agents run SIMULTANEOUSLY — results accumulate in parallel",
   0.75, 4.65, 12.0, 0.28, size=11, bold=True, color=NAVY, align=PP_ALIGN.CENTER)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 7 — RAG / GRAPH RAG / AGENTIC RAG
# ══════════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(BLANK)
rect(s, 0, 0, 13.33, 7.5, NAVY)
rect(s, 0, 0, 0.5, 7.5, TEAL)
tb(s, "05  |  Retrieval Patterns", 1.0, 0.2, 11.0, 0.6,
   size=26, bold=True, color=WHITE)
divider(s, 0.95)

cols = [
    ("Standard RAG",
     "Query  →  Vector search\n→  Top-K chunks  →  Generate",
     ["Single retrieval per query",
      "Flat document chunks",
      "Fast and cheap",
      "Weak on multi-hop questions"],
     "Simple Q&A on flat docs\n(FAQs, runbooks, policies)"),
    ("Graph RAG",
     "Query  →  Entity match\n→  Graph traversal  →  Generate",
     ["Entities + relationships",
      "Multi-hop traversal",
      "Community summaries",
      "Higher build cost"],
     "Relationship queries\nacross connected domains"),
    ("Agentic RAG",
     "Query  →  Agent decides\n→  Retrieve N times  →  Generate",
     ["Retrieval is a tool in the loop",
      "Agent retries if result is bad",
      "Can combine web + KB + DB",
      "Highest cost and latency"],
     "Complex multi-step queries\nthat require iteration"),
]

box_w = 3.8
for i, (title, flow, bullets, use) in enumerate(cols):
    x = 0.6 + i * (box_w + 0.26)
    rect(s, x, 1.1, box_w, 5.9, DARK_GRAY)
    rect(s, x, 1.1, box_w, 0.55, TEAL)
    tb(s, title, x + 0.1, 1.13, box_w - 0.2, 0.5,
       size=15, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    tb(s, flow, x + 0.15, 1.75, box_w - 0.3, 0.85,
       size=12, color=AMBER, align=PP_ALIGN.CENTER)
    divider(s, 2.65, MID_GRAY, l=x + 0.15, w=box_w - 0.3, h=0.03)
    bullet_text = "\n".join(f"  •  {b}" for b in bullets)
    tb(s, bullet_text, x + 0.15, 2.72, box_w - 0.3, 2.3,
       size=12, color=LIGHT_GRAY)
    divider(s, 5.1, MID_GRAY, l=x + 0.15, w=box_w - 0.3, h=0.03)
    tb(s, "Use when:", x + 0.15, 5.15, box_w - 0.3, 0.3,
       size=11, bold=True, color=TEAL)
    tb(s, use, x + 0.15, 5.5, box_w - 0.3, 1.3,
       size=12, color=LIGHT_GRAY)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 8 — FRAMEWORK LANDSCAPE
# ══════════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(BLANK)
rect(s, 0, 0, 13.33, 7.5, LIGHT_GRAY)
rect(s, 0, 0, 13.33, 1.1, NAVY)
rect(s, 0, 0, 0.5, 7.5, TEAL)
tb(s, "06  |  Framework Landscape", 1.0, 0.2, 11.0, 0.6,
   size=26, bold=True, color=WHITE)

frameworks = [
    ("LangChain",
     "Component Library",
     "Raw materials: LLMs, prompts,\ntools, retrievers, parsers.",
     ["Uniform LLM interface (swap providers)",
      "LCEL pipe syntax: prompt | llm | parser",
      "Rich retriever ecosystem",
      "No agent loop — just chains"],
     "RAG pipelines, prompt\nengineering, LLM chains"),
    ("LangGraph",
     "Graph Orchestration",
     "Blueprint: nodes, edges, state,\nloops, parallelism, persistence.",
     ["Explicit, visible agent loop",
      "Conditional edges + Send() for parallel",
      "Checkpointing + human-in-the-loop",
      "Time travel for debugging"],
     "Complex enterprise agents,\nAWS/Azure/multi-cloud"),
    ("Google ADK",
     "Agent Platform",
     "Prefab kit: built-in agent types,\nsession mgmt, eval harness.",
     ["LlmAgent, ParallelAgent, SequentialAgent",
      "Built-in adk eval CLI",
      "A2A protocol + MCP support",
      "Native Vertex AI deployment"],
     "GCP-native agents,\nrapid prototyping"),
]

box_w = 3.85
for i, (name, category, tagline, bullets, use) in enumerate(frameworks):
    x = 0.6 + i * (box_w + 0.26)
    rect(s, x, 1.15, box_w, 6.1, WHITE)
    rect(s, x, 1.15, box_w, 0.55, NAVY)
    tb(s, name, x + 0.1, 1.18, box_w - 0.2, 0.3,
       size=16, bold=True, color=TEAL, align=PP_ALIGN.CENTER)
    rect(s, x, 1.7, box_w, 0.3, TEAL)
    tb(s, category, x + 0.1, 1.72, box_w - 0.2, 0.28,
       size=11, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    tb(s, tagline, x + 0.15, 2.1, box_w - 0.3, 0.75,
       size=12, color=DARK_GRAY)
    divider(s, 2.9, TEAL, l=x + 0.15, w=box_w - 0.3, h=0.03)
    bullet_text = "\n".join(f"  •  {b}" for b in bullets)
    tb(s, bullet_text, x + 0.15, 2.98, box_w - 0.3, 2.5,
       size=12, color=DARK_GRAY)
    divider(s, 5.55, LIGHT_GRAY, l=x + 0.15, w=box_w - 0.3, h=0.03)
    tb(s, "Best for:", x + 0.15, 5.62, box_w - 0.3, 0.3,
       size=11, bold=True, color=NAVY)
    tb(s, use, x + 0.15, 5.98, box_w - 0.3, 1.0,
       size=12, color=MID_GRAY)

# Relationship note at bottom
rect(s, 0.6, 7.08, 12.1, 0.3, NAVY)
tb(s, "LangGraph builds ON TOP of LangChain  |  ADK is standalone  |  All three are open source",
   0.8, 7.1, 12.0, 0.28, size=12, color=TEAL, align=PP_ALIGN.CENTER)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 9 — SAFETY & GUARDRAILS
# ══════════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(BLANK)
rect(s, 0, 0, 13.33, 7.5, NAVY)
rect(s, 0, 0, 0.5, 7.5, TEAL)
tb(s, "07  |  Safety & Guardrails", 1.0, 0.2, 11.0, 0.6,
   size=26, bold=True, color=WHITE)
divider(s, 0.95)

safety_items = [
    ("Input Guardrails",
     "Run BEFORE the LLM sees the query",
     "PHI redaction (SSN, DOB, MRN)\nTopic filter (block clinical advice)\nContent policy check",
     TEAL),
    ("Output Guardrails",
     "Run BEFORE the user sees the response",
     "Grounding check (answer in the docs?)\nPII scan (no data leaked)\nTone / policy compliance",
     DARK_GRAY),
    ("Prompt Injection Defense",
     "Agent-specific attack vector",
     "Malicious content in tool results\nhijacks agent behavior.\nMitigation: separate instruction\nfrom data. Restrict tool permissions.",
     RGBColor(0x8B, 0x00, 0x00)),
    ("Least Privilege",
     "Each agent only gets what it needs",
     "HR agent: read HR KB only\nPayroll agent: read payroll only\nNo write tools unless required\nSeparate IAM roles per agent",
     DARK_GRAY),
]

box_w = 2.85
for i, (title, sub, detail, color) in enumerate(safety_items):
    x = 0.6 + i * (box_w + 0.24)
    rect(s, x, 1.1, box_w, 5.6, DARK_GRAY)
    rect(s, x, 1.1, box_w, 0.55, color)
    tb(s, title, x + 0.1, 1.13, box_w - 0.2, 0.35,
       size=13, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    divider(s, 1.68, MID_GRAY, l=x + 0.1, w=box_w - 0.2, h=0.03)
    tb(s, sub, x + 0.15, 1.75, box_w - 0.3, 0.55,
       size=11, color=AMBER)
    tb(s, detail, x + 0.15, 2.38, box_w - 0.3, 3.1,
       size=12, color=LIGHT_GRAY)

# Hard stop vs soft stop
rect(s, 0.6, 6.85, 5.8, 0.52, TEAL)
tb(s, "Hard Stop: immediate refusal, no tools called, query terminated",
   0.8, 6.9, 5.5, 0.42, size=12, bold=True, color=NAVY)
rect(s, 6.7, 6.85, 5.8, 0.52, DARK_GRAY)
tb(s, "Soft Stop: partial answer or redirect within policy constraints",
   6.9, 6.9, 5.5, 0.42, size=12, color=WHITE)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 10 — EVALUATION & OBSERVABILITY
# ══════════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(BLANK)
rect(s, 0, 0, 13.33, 7.5, LIGHT_GRAY)
rect(s, 0, 0, 13.33, 1.1, NAVY)
rect(s, 0, 0, 0.5, 7.5, TEAL)
tb(s, "08  |  Evaluation & Observability", 1.0, 0.2, 11.0, 0.6,
   size=26, bold=True, color=WHITE)

# Left — evaluation metrics
rect(s, 0.6, 1.2, 5.8, 6.0, WHITE)
tb(s, "How Do You Know the Agent Is Working?",
   0.8, 1.3, 5.5, 0.5, size=15, bold=True, color=NAVY)
divider(s, 1.85, TEAL, l=0.7, w=5.6, h=0.04)
metrics = [
    ("Task Success Rate",      "Did the agent answer/complete correctly?"),
    ("Tool Selection Accuracy","Did it call the RIGHT tools?"),
    ("Hallucination Rate",     "Did it invent facts not in the documents?"),
    ("Latency",                "How many LLM calls? Total time?"),
    ("Cost per Query",         "Calls × tokens × price per token"),
    ("Escalation Accuracy",    "Did it escalate when it should have?"),
]
for i, (metric, desc) in enumerate(metrics):
    top = 1.98 + i * 0.82
    rect(s, 0.7, top, 5.6, 0.7, LIGHT_GRAY)
    tb(s, metric, 0.9, top + 0.05, 2.8, 0.35,
       size=13, bold=True, color=NAVY)
    tb(s, desc, 0.9, top + 0.35, 5.2, 0.3,
       size=11, color=MID_GRAY)

# Right — what to trace
rect(s, 6.9, 1.2, 5.8, 6.0, WHITE)
tb(s, "What to Trace in Every Agent Call",
   7.1, 1.3, 5.5, 0.5, size=15, bold=True, color=NAVY)
divider(s, 1.85, TEAL, l=7.0, w=5.6, h=0.04)
trace_items = [
    "Every node entry + exit (timestamp, input, output)",
    "Every LLM call (tokens in / out, model, latency)",
    "Every tool call (name, args, result, latency)",
    "Every routing decision (which branch and why)",
    "Errors and retries (what failed, how recovered)",
    "thread_id / session_id (correlate one conversation)",
]
for i, item in enumerate(trace_items):
    top = 2.0 + i * 0.82
    rect(s, 7.0, top, 5.6, 0.7, LIGHT_GRAY)
    rect(s, 7.0, top, 0.08, 0.7, TEAL)
    tb(s, item, 7.2, top + 0.15, 5.2, 0.45,
       size=12, color=DARK_GRAY)

# Tooling footer
rect(s, 0.6, 7.25, 12.1, 0.15, TEAL)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 11 — KEY TAKEAWAYS
# ══════════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(BLANK)
rect(s, 0, 0, 13.33, 7.5, NAVY)
rect(s, 0, 0, 0.5, 7.5, TEAL)
tb(s, "09  |  Key Takeaways", 1.0, 0.2, 11.0, 0.6,
   size=26, bold=True, color=WHITE)
divider(s, 0.95)

takeaways = [
    ("01", "An agent = LLM + loop + tools + memory.",
           "The loop and the ability to act are what separate agents from plain LLM calls."),
    ("02", "ReAct is the universal loop.",
           "Thought → Action → Observation, repeat. Every major framework implements this."),
    ("03", "Multi-agent is the scaling path.",
           "Past 3-4 domains or 6-8 tools, use a supervisor + specialists. Parallel dispatch = speed."),
    ("04", "RAG grounds answers. Agentic RAG adapts.",
           "Standard RAG for simple lookup. Agentic RAG for multi-step, multi-source queries."),
    ("05", "Framework choice follows your cloud.",
           "LangChain + LangGraph for AWS/Azure/multi-cloud. Google ADK for GCP + Vertex AI."),
    ("06", "Safety is not optional.",
           "Guardrails, PHI redaction, least privilege, and prompt injection defense from day one."),
    ("07", "If you can't trace it, you can't trust it.",
           "Every LLM call, tool call, and routing decision must be logged and traceable."),
]

for i, (num, headline, detail) in enumerate(takeaways):
    top = 1.1 + i * 0.87
    rect(s, 0.6, top, 11.9, 0.78, DARK_GRAY)
    # number
    badge = s.shapes.add_shape(1, Inches(0.68), Inches(top + 0.17),
                                Inches(0.44), Inches(0.44))
    solid(badge, TEAL)
    badge.line.fill.background()
    tf = badge.text_frame
    tf.paragraphs[0].alignment = PP_ALIGN.CENTER
    run = tf.paragraphs[0].add_run()
    run.text = num
    run.font.size = Pt(12)
    run.font.bold = True
    run.font.color.rgb = WHITE

    tb(s, headline, 1.25, top + 0.07, 5.5, 0.36,
       size=14, bold=True, color=WHITE)
    tb(s, detail, 6.9, top + 0.12, 5.4, 0.55,
       size=12, color=LIGHT_GRAY)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 12 — THANK YOU / END
# ══════════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(BLANK)
rect(s, 0, 0, 13.33, 7.5, NAVY)
rect(s, 0, 0, 13.33, 0.08, TEAL)
rect(s, 0, 7.42, 13.33, 0.08, TEAL)
rect(s, 0, 0, 0.5, 7.5, TEAL)
rect(s, 12.83, 0, 0.5, 7.5, TEAL)

tb(s, "Thank You", 1.0, 2.2, 11.0, 1.0,
   size=54, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
divider(s, 3.5, TEAL, l=3.0, w=7.0, h=0.06)
tb(s, "Questions & Discussion",
   1.0, 3.7, 11.0, 0.6, size=22, color=TEAL, align=PP_ALIGN.CENTER)

tb(s, "Rohid Dev  ·  github.com/rohiddev",
   1.0, 6.6, 11.2, 0.45, size=14, color=MID_GRAY, align=PP_ALIGN.CENTER)


# ── Save ──────────────────────────────────────────────────────────────────────
out = "/Users/chandinidev/Documents/rohid-code/TCOE-Usecase/agentic-ai-overview.pptx"
prs.save(out)
print(f"Saved: {out}")
print(f"Slides: {len(prs.slides)}")
