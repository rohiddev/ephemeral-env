"""
Rebuild: agentic-ai-overview.pptx
Style: exactly matches IDP_August_Catalog_Capstone_v2.pptx
  - 10 x 5.62 inch slides
  - Black slide background (set via XML background fill)
  - #5BA872  bright green  — top bar, accent numbers, section labels
  - #155030  deep green    — card backgrounds (dark)
  - #1B5E37  forest green  — left sidebar panels
  - #2D7D4F  mid green     — dividers, secondary text
  - #0F3D23  dark forest   — footer bar
  - #F4F9F6  near white    — card backgrounds (light)
  - #A8D5B5  mint          — muted body text on dark
  - #4A7A5A  medium green  — sub-text on light cards
  - #FFFFFF  white         — headlines on dark
"""

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from lxml import etree

# ── Palette (exact from source deck) ─────────────────────────────────────────
G_BRIGHT   = RGBColor(0x5B, 0xA8, 0x72)   # bright green — bars, numbers, accent
G_DEEP     = RGBColor(0x15, 0x50, 0x30)   # deep green — dark cards
G_FOREST   = RGBColor(0x1B, 0x5E, 0x37)   # forest green — left panels, titles on light
G_MID      = RGBColor(0x2D, 0x7D, 0x4F)   # mid green — dividers
G_FOOTER   = RGBColor(0x0F, 0x3D, 0x23)   # footer bar
G_LIGHT    = RGBColor(0xF4, 0xF9, 0xF6)   # near-white cards
G_MINT     = RGBColor(0xA8, 0xD5, 0xB5)   # mint — muted text on dark
G_MED      = RGBColor(0x4A, 0x7A, 0x5A)   # medium green — sub on light
WHITE      = RGBColor(0xFF, 0xFF, 0xFF)
BLACK      = RGBColor(0x00, 0x00, 0x00)

W  = 10.0   # slide width inches
H  = 5.62  # slide height inches

prs = Presentation()
prs.slide_width  = Inches(W)
prs.slide_height = Inches(H)
BLANK = prs.slide_layouts[6]


# ── Set black background on a slide via XML ───────────────────────────────────
def set_black_bg(slide):
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = RGBColor(0x0A, 0x0A, 0x0A)


# ── Helpers ───────────────────────────────────────────────────────────────────
def rect(slide, l, t, w, h, color, line=False):
    s = slide.shapes.add_shape(1, Inches(l), Inches(t), Inches(w), Inches(h))
    s.fill.solid()
    s.fill.fore_color.rgb = color
    if line:
        s.line.color.rgb = color
    else:
        s.line.fill.background()
    return s


def tb(slide, text, l, t, w, h,
       size=11, bold=False, color=WHITE, align=PP_ALIGN.LEFT, italic=False):
    txb = slide.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h))
    txb.word_wrap = True
    tf = txb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.size   = Pt(size)
    run.font.bold   = bold
    run.font.italic = italic
    run.font.color.rgb = color
    return txb


def tb_multi(slide, lines, l, t, w, h, size=10, color=WHITE, bold_idx=None, spacing_after=3):
    txb = slide.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h))
    txb.word_wrap = True
    tf = txb.text_frame
    tf.word_wrap = True
    for i, line in enumerate(lines):
        p = tf.add_paragraph() if i > 0 else tf.paragraphs[0]
        p.space_after = Pt(spacing_after)
        run = p.add_run()
        run.text = line
        run.font.size = Pt(size)
        run.font.color.rgb = color
        run.font.bold = (bold_idx is not None and i == bold_idx)


def top_bar(slide):
    """Bright green bar across the top — matches source deck exactly."""
    rect(slide, 0, 0, W, 0.07, G_BRIGHT)


def footer_bar(slide, label="Agentic AI  ·  Executive Overview"):
    rect(slide, 0, H - 0.14, W, 0.14, G_FOOTER)
    tb(slide, label, 0.40, H - 0.135, 9.0, 0.12,
       size=8, color=G_BRIGHT)


def section_label(slide, text):
    """Small all-caps green label below the top bar — matches source style."""
    tb(slide, text, 0.40, 0.13, 9.0, 0.20,
       size=9, bold=True, color=G_BRIGHT)


def slide_title(slide, text, color=G_FOREST):
    tb(slide, text, 0.40, 0.36, 9.20, 0.62,
       size=28, bold=True, color=color)


def divider_line(slide, top, l=0.40, w=9.20, color=G_MID):
    rect(slide, l, top, w, 0.02, color)


def green_left_bar(slide, t, h, w=0.06):
    """Thin bright-green left accent on white cards — matches source."""
    rect(slide, 0.40, t, w, h, G_BRIGHT)


# ── Card with green left accent (matches source slide 2/3 cards) ─────────────
def light_card(slide, l, t, w, h, title, subtitle):
    rect(slide, l, t, w, h, G_LIGHT)
    rect(slide, l, t, 0.06, h, G_BRIGHT)   # left accent
    tb(slide, title,    l + 0.14, t + 0.08, w - 0.18, 0.28,
       size=12, bold=True, color=G_FOREST)
    tb(slide, subtitle, l + 0.14, t + 0.38, w - 0.18, 0.44,
       size=10, color=G_MED)


# ── Dark stat card (matches source slide 1 stat boxes) ───────────────────────
def stat_card(slide, l, t, w, h, number, label, sub):
    rect(slide, l, t, w, h, G_DEEP)
    tb(slide, number, l + 0.10, t + 0.02, w - 0.20, 0.52,
       size=38, bold=True, color=G_BRIGHT)
    tb(slide, label,  l + 0.10, t + 0.54, w - 0.20, 0.20,
       size=9,  bold=True, color=WHITE)
    tb(slide, sub,    l + 0.10, t + 0.74, w - 0.20, 0.20,
       size=8,  color=G_MINT)


# ── Section card (matches source slide 1 session boxes) ──────────────────────
def section_card(slide, l, t, w, h, num, title, bullets):
    rect(slide, l, t, w, h, G_DEEP)
    tb(slide, num,   l + 0.12, t + 0.07, 0.70, 0.52,
       size=28, bold=True, color=G_BRIGHT)
    tb(slide, title, l + 0.12, t + 0.59, w - 0.24, 0.25,
       size=11, bold=True, color=WHITE)
    tb_multi(slide, bullets, l + 0.12, t + 0.85,
             w - 0.24, h - 0.95, size=9, color=G_MINT)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 1 — TITLE  (matches source slide 1 layout)
# ══════════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(BLANK)
set_black_bg(s)
top_bar(s)

section_label(s, "AGENTIC AI  ·  EXECUTIVE OVERVIEW")

# Hero headline
tb(s, "Agentic AI:", 0.40, 0.38, 9.20, 0.65,
   size=44, bold=True, color=WHITE)
tb(s, "From LLM Calls to Autonomous Agents.", 0.40, 1.00, 9.20, 0.65,
   size=44, bold=True, color=WHITE)

# Subtitle
tb(s, "Understand agents, retrieval, multi-agent systems, frameworks, safety, and observability.",
   0.40, 1.75, 9.10, 0.35, size=14, color=G_MINT)

divider_line(s, 2.22)

# Three stat cards
stat_card(s, 0.40, 2.32, 2.93, 0.98,
          "4",  "CORE PROPERTIES",     "Perceive · Reason · Act · Remember")
stat_card(s, 3.53, 2.32, 2.93, 0.98,
          "3",  "RETRIEVAL PATTERNS",  "RAG · Graph RAG · Agentic RAG")
stat_card(s, 6.66, 2.32, 2.93, 0.98,
          "3",  "MAJOR FRAMEWORKS",    "LangChain · LangGraph · ADK")

divider_line(s, 3.42)

# Three agenda section cards
tb(s, "TOPICS COVERED", 0.40, 3.50, 4.0, 0.20,
   size=9, bold=True, color=G_BRIGHT)

section_card(s, 0.40, 3.72, 2.93, 1.75,
             "01", "AGENT FUNDAMENTALS",
             ["What is an agent?", "The ReAct loop", "Memory & state"])
section_card(s, 3.53, 3.72, 2.93, 1.75,
             "02", "SYSTEMS & RETRIEVAL",
             ["Multi-agent patterns", "RAG · Graph RAG", "Agentic RAG"])
section_card(s, 6.66, 3.72, 2.93, 1.75,
             "03", "PRODUCTION",
             ["Frameworks compared", "Safety & guardrails", "Eval & observability"])

footer_bar(s)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 2 — WHAT IS AN AGENT?
# ══════════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(BLANK)
set_black_bg(s)
top_bar(s)
section_label(s, "AGENT FUNDAMENTALS  ·  THE CORE SHIFT")
slide_title(s, "Plain LLM Call vs AI Agent", color=G_FOREST)

# Left dark panel — LLM call
rect(s, 0.40, 1.08, 2.80, 4.25, G_FOREST)
tb(s, "Plain LLM Call", 0.52, 1.18, 2.56, 0.40,
   size=14, bold=True, color=WHITE)
tb(s, "Send a prompt. Get a response. Done.", 0.52, 1.62, 2.56, 0.35,
   size=11, color=G_MINT)
divider_line(s, 2.05, l=0.52, w=2.40, color=G_MID)
tb_multi(s, [
    "  Stateless — no memory",
    "  One-shot — no loop",
    "  Cannot call tools",
    "  Cannot retry or adapt",
    "  Generates text only",
], 0.52, 2.12, 2.56, 1.80, size=11, color=WHITE)

# Right section — four property cards
props = [
    ("PERCEIVE",  "Receives input — query,\ntool result, system event"),
    ("REASON",    "LLM decides what to do:\nwhich tool, which answer, stop?"),
    ("ACT",       "Calls tools — API, DB,\nretrieval, escalate to human"),
    ("REMEMBER",  "Retains context across\nsteps and conversation turns"),
]
card_w, card_h = 3.20, 0.88
start_x, start_y = 3.45, 1.08
gap = 0.04
for i, (title, desc) in enumerate(props):
    t = start_y + i * (card_h + gap)
    rect(s, start_x, t, card_w, card_h, G_LIGHT)
    rect(s, start_x, t, 0.06, card_h, G_BRIGHT)
    tb(s, title, start_x + 0.14, t + 0.10, card_w - 0.20, 0.28,
       size=12, bold=True, color=G_FOREST)
    tb(s, desc,  start_x + 0.14, t + 0.42, card_w - 0.20, 0.42,
       size=10, color=G_MED)

# Definition callout
rect(s, 0.40, H - 0.58, 9.20, 0.34, G_DEEP)
rect(s, 0.40, H - 0.58, 0.06, 0.34, G_BRIGHT)
tb(s, 'Agent = "A system that perceives, reasons, acts, and remembers — in a loop."',
   0.52, H - 0.56, 8.90, 0.30, size=11, bold=True, color=G_MINT)

footer_bar(s)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 3 — THE AGENT LOOP (ReAct)
# ══════════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(BLANK)
set_black_bg(s)
top_bar(s)
section_label(s, "THE AGENT LOOP  ·  REACT PATTERN")
slide_title(s, "Thought → Action → Observation — Repeat Until Done", color=G_FOREST)

# Four step cards
steps = [
    ("THOUGHT",      "LLM writes its reasoning\nabout what to do next",     G_DEEP),
    ("ACTION",       "LLM picks a tool and\nprovides arguments",             G_FOREST),
    ("OBSERVATION",  "Tool executes. Result\nfed back into context",         G_DEEP),
    ("FINAL ANSWER", "No tool_calls in response.\nLoop exits cleanly.",      G_MID),
]
box_w = 2.10
gap_x = 0.14
sx = 0.40
for i, (label, desc, color) in enumerate(steps):
    x = sx + i * (box_w + gap_x)
    rect(s, x, 1.08, box_w, 1.60, color)
    # number badge
    badge = s.shapes.add_shape(1, Inches(x + 0.10), Inches(1.14),
                                Inches(0.36), Inches(0.36))
    badge.fill.solid(); badge.fill.fore_color.rgb = G_BRIGHT
    badge.line.fill.background()
    tf = badge.text_frame
    tf.paragraphs[0].alignment = PP_ALIGN.CENTER
    r = tf.paragraphs[0].add_run()
    r.text = str(i + 1); r.font.size = Pt(11); r.font.bold = True
    r.font.color.rgb = WHITE
    tb(s, label, x + 0.54, 1.14, box_w - 0.60, 0.30,
       size=10, bold=True, color=G_BRIGHT)
    divider_line(s, 1.50, l=x + 0.10, w=box_w - 0.20, color=G_MID)
    tb(s, desc, x + 0.10, 1.56, box_w - 0.20, 0.90,
       size=10, color=WHITE)
    if i < 3:
        tb(s, "→", x + box_w + 0.02, 1.70, gap_x + 0.06, 0.36,
           size=16, bold=True, color=G_BRIGHT, align=PP_ALIGN.CENTER)

# Loop-back label
tb(s, "↺  Loop repeats until the LLM produces a response with no tool calls",
   0.40, 2.76, 9.20, 0.30, size=11, italic=True, color=G_MINT, align=PP_ALIGN.CENTER)

# Example box — white card with left accent
rect(s, 0.40, 3.14, 9.20, 2.20, G_LIGHT)
rect(s, 0.40, 3.14, 0.06, 2.20, G_BRIGHT)
tb(s, "Concrete Example", 0.56, 3.20, 4.0, 0.30,
   size=12, bold=True, color=G_FOREST)
divider_line(s, 3.56, l=0.56, w=8.90, color=G_BRIGHT)
tb_multi(s, [
    'User: "What is the weather in Tokyo and convert to Celsius?"',
    "",
    "THOUGHT      I need the Tokyo weather first.",
    "ACTION       get_weather(city='Tokyo')   →   OBSERVATION: 80°F, sunny",
    "THOUGHT      Now convert 80°F to Celsius.",
    "ACTION       calculate('(80-32)*5/9')   →   OBSERVATION: 26.67",
    "FINAL        The weather in Tokyo is 26.67°C, sunny.",
], 0.56, 3.62, 8.96, 1.60, size=11, color=G_FOREST, bold_idx=0)

footer_bar(s)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 4 — MEMORY & STATE
# ══════════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(BLANK)
set_black_bg(s)
top_bar(s)
section_label(s, "MEMORY & STATE  ·  FOUR TYPES")
slide_title(s, "How Agents Remember — Across Steps and Sessions", color=G_FOREST)

memory_types = [
    ("In-Context\n(Short-Term)",
     "Current conversation in the\ncontext window. Ephemeral.\nClears each session.",
     "Limited by model context\nwindow (e.g. 200K tokens)"),
    ("External\n(Long-Term)",
     "Vector DB, relational DB,\nkey-value store. Persists\nacross all sessions.",
     "Retrieved via RAG or\nlookup tool at query time"),
    ("Episodic\n(Session)",
     "This conversation, persisted\nby thread_id. Resumable\nafter interruption.",
     "LangGraph: MemorySaver\nADK: SessionService"),
    ("Semantic\n(Knowledge Base)",
     "Shared domain knowledge\nfor all users. HR policies,\ndocs, compliance rules.",
     "Retrieved via RAG.\nGround truth for answers"),
]
card_w = 2.14
card_h = 3.90
gap_c  = 0.14
for i, (title, desc, impl) in enumerate(memory_types):
    x = 0.40 + i * (card_w + gap_c)
    rect(s, x, 1.08, card_w, card_h, G_DEEP)
    rect(s, x, 1.08, card_w, 0.46, G_FOREST)
    tb(s, title, x + 0.10, 1.10, card_w - 0.20, 0.44,
       size=11, bold=True, color=G_BRIGHT, align=PP_ALIGN.CENTER)
    tb(s, desc, x + 0.10, 1.62, card_w - 0.20, 1.50,
       size=10, color=G_MINT)
    divider_line(s, 3.20, l=x + 0.10, w=card_w - 0.20, color=G_MID)
    tb(s, impl, x + 0.10, 3.28, card_w - 0.20, 1.52,
       size=9, color=WHITE)

# Bottom callout
rect(s, 0.40, 5.06, 9.20, 0.34, G_FOREST)
rect(s, 0.40, 5.06, 0.06, 0.34, G_BRIGHT)
tb(s, "Best practice: use ALL FOUR — in-context for coherence · episodic for continuity · semantic for accuracy · external for user data",
   0.52, 5.08, 9.0, 0.30, size=10, bold=True, color=G_MINT)

footer_bar(s)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 5 — MULTI-AGENT SYSTEMS
# ══════════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(BLANK)
set_black_bg(s)
top_bar(s)
section_label(s, "MULTI-AGENT SYSTEMS  ·  SUPERVISOR PATTERN")
slide_title(s, "Fan-Out to Specialists — Fan-In to One Answer", color=G_FOREST)

# Supervisor box
rect(s, 3.50, 1.08, 3.00, 0.76, G_FOREST)
rect(s, 3.50, 1.08, 0.06, 0.76, G_BRIGHT)
tb(s, "SUPERVISOR AGENT", 3.62, 1.12, 2.80, 0.30,
   size=12, bold=True, color=G_BRIGHT)
tb(s, "Classify intent  ·  Route  ·  Aggregate",
   3.62, 1.44, 2.80, 0.28, size=10, color=G_MINT)

# Arrows down
for x in [0.85, 2.98, 5.11, 7.24]:
    tb(s, "↓", x + 0.34, 1.90, 0.40, 0.36,
       size=18, bold=True, color=G_BRIGHT, align=PP_ALIGN.CENTER)

# Specialist cards
specs = [
    ("HR POLICY",    "PTO · Leave\nParental policy"),
    ("BENEFITS",     "Health · Dental\n401k · FSA"),
    ("PAYROLL",      "Salary · Pay dates\nDeductions"),
    ("IT SUPPORT",   "VPN · Access\nHardware"),
]
sw, sh = 2.00, 1.40
sx_s = 0.40
for i, (name, detail) in enumerate(specs):
    x = sx_s + i * (sw + 0.26)
    rect(s, x, 2.32, sw, sh, G_DEEP)
    rect(s, x, 2.32, sw, 0.38, G_FOREST)
    tb(s, name, x + 0.10, 2.34, sw - 0.20, 0.34,
       size=10, bold=True, color=G_BRIGHT, align=PP_ALIGN.CENTER)
    tb(s, detail, x + 0.10, 2.76, sw - 0.20, 0.82,
       size=9, color=G_MINT, align=PP_ALIGN.CENTER)

# Parallel label banner
rect(s, 0.40, 3.78, 9.20, 0.26, G_MID)
tb(s, "All specialist agents run SIMULTANEOUSLY via Send() — results accumulate in parallel via reducer",
   0.52, 3.80, 9.0, 0.22, size=9, bold=True, color=WHITE, align=PP_ALIGN.CENTER)

# Arrows up
for x in [0.85, 2.98, 5.11, 7.24]:
    tb(s, "↑", x + 0.34, 4.10, 0.40, 0.36,
       size=18, bold=True, color=G_BRIGHT, align=PP_ALIGN.CENTER)

# Aggregator
rect(s, 3.50, 4.52, 3.00, 0.62, G_FOREST)
rect(s, 3.50, 4.52, 0.06, 0.62, G_BRIGHT)
tb(s, "AGGREGATOR", 3.62, 4.56, 2.80, 0.28,
   size=12, bold=True, color=G_BRIGHT)
tb(s, "Merge  ·  Cite sources  ·  Deliver",
   3.62, 4.84, 2.80, 0.22, size=10, color=G_MINT)

# Final answer
rect(s, 2.50, 5.20, 5.00, 0.28, G_BRIGHT)
tb(s, "Unified answer with citations from all domains",
   2.50, 5.22, 5.00, 0.24, size=10, bold=True, color=WHITE, align=PP_ALIGN.CENTER)

footer_bar(s)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 6 — RETRIEVAL PATTERNS
# ══════════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(BLANK)
set_black_bg(s)
top_bar(s)
section_label(s, "RETRIEVAL PATTERNS  ·  RAG · GRAPH RAG · AGENTIC RAG")
slide_title(s, "Ground Every Answer — Pick the Right Pattern", color=G_FOREST)

rag_cols = [
    ("Standard RAG",
     "Query → Vector search\n→ Top-K chunks → Generate",
     ["Single retrieval per query",
      "Flat document chunks",
      "Fast, low cost",
      "Weak on multi-hop"],
     "Simple Q&A on flat docs\n(FAQs, runbooks, policies)"),
    ("Graph RAG",
     "Query → Entity match\n→ Graph traversal → Generate",
     ["Entities + relationships",
      "Multi-hop traversal",
      "Community summaries",
      "Higher build cost"],
     "Relationship queries\nacross connected domains"),
    ("Agentic RAG",
     "Query → Agent decides\n→ Retrieve N times → Generate",
     ["Retrieval is a tool in loop",
      "Agent retries if result bad",
      "Combines web + KB + DB",
      "Highest latency & cost"],
     "Complex multi-step queries\nthat require iteration"),
]
col_w = 2.80
col_h = 4.10
col_gap = 0.20
for i, (title, flow, bullets, use) in enumerate(rag_cols):
    x = 0.40 + i * (col_w + col_gap)
    rect(s, x, 1.08, col_w, col_h, G_DEEP)
    rect(s, x, 1.08, col_w, 0.38, G_BRIGHT)
    tb(s, title, x + 0.10, 1.10, col_w - 0.20, 0.34,
       size=12, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    tb(s, flow, x + 0.10, 1.54, col_w - 0.20, 0.68,
       size=10, color=G_BRIGHT, align=PP_ALIGN.CENTER)
    divider_line(s, 2.28, l=x + 0.10, w=col_w - 0.20, color=G_MID)
    bullet_text = "\n".join(f"  ·  {b}" for b in bullets)
    tb(s, bullet_text, x + 0.10, 2.36, col_w - 0.20, 1.68,
       size=10, color=G_MINT)
    divider_line(s, 4.10, l=x + 0.10, w=col_w - 0.20, color=G_MID)
    tb(s, "Use when:", x + 0.10, 4.16, col_w - 0.20, 0.22,
       size=9, bold=True, color=G_BRIGHT)
    tb(s, use, x + 0.10, 4.40, col_w - 0.20, 0.62,
       size=10, color=WHITE)

footer_bar(s)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 7 — FRAMEWORK LANDSCAPE
# ══════════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(BLANK)
set_black_bg(s)
top_bar(s)
section_label(s, "FRAMEWORK LANDSCAPE  ·  LANGCHAIN · LANGGRAPH · GOOGLE ADK")
slide_title(s, "Choose Based on Your Cloud and Control Needs", color=G_FOREST)

frameworks = [
    ("LangChain",
     "Component Library",
     "Raw materials: LLMs, prompts,\ntools, retrievers, output parsers.",
     ["Uniform LLM interface — swap providers",
      "LCEL pipe: prompt | llm | parser",
      "Rich retriever ecosystem (Bedrock KB, Pinecone)",
      "No agent loop — chains only"],
     "RAG pipelines, prompt\nengineering, LLM chains"),
    ("LangGraph",
     "Graph Orchestration",
     "Explicit state machine: nodes,\nedges, reducers, checkpointing.",
     ["Visible, testable agent loop",
      "Send() for parallel dispatch",
      "Checkpointing + human-in-the-loop",
      "Time travel debugging"],
     "Enterprise agents on\nAWS / Azure / multi-cloud"),
    ("Google ADK",
     "Agent Platform",
     "Opinionated kit: built-in agent\ntypes, session mgmt, eval CLI.",
     ["LlmAgent, ParallelAgent, SequentialAgent",
      "Built-in adk eval harness",
      "A2A + MCP protocol support",
      "Native Vertex AI deployment"],
     "GCP-native agents,\nVertex AI rapid delivery"),
]
fw_w = 2.80
fw_h = 4.10
fw_gap = 0.20
for i, (name, cat, tag, bullets, use) in enumerate(frameworks):
    x = 0.40 + i * (fw_w + fw_gap)
    rect(s, x, 1.08, fw_w, fw_h, G_LIGHT)
    rect(s, x, 1.08, fw_w, 0.38, G_FOREST)
    tb(s, name, x + 0.10, 1.10, fw_w - 0.20, 0.30,
       size=13, bold=True, color=G_BRIGHT, align=PP_ALIGN.CENTER)
    rect(s, x, 1.46, fw_w, 0.24, G_MID)
    tb(s, cat, x + 0.10, 1.48, fw_w - 0.20, 0.20,
       size=9, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    tb(s, tag, x + 0.10, 1.78, fw_w - 0.20, 0.58,
       size=10, color=G_FOREST)
    divider_line(s, 2.42, l=x + 0.10, w=fw_w - 0.20, color=G_BRIGHT)
    bullet_text = "\n".join(f"  ·  {b}" for b in bullets)
    tb(s, bullet_text, x + 0.10, 2.50, fw_w - 0.20, 1.62,
       size=10, color=G_FOREST)
    divider_line(s, 4.18, l=x + 0.10, w=fw_w - 0.20, color=G_MID)
    tb(s, "Best for:", x + 0.10, 4.24, fw_w - 0.20, 0.20,
       size=9, bold=True, color=G_FOREST)
    tb(s, use, x + 0.10, 4.46, fw_w - 0.20, 0.58,
       size=10, color=G_MED)

# Relationship note
rect(s, 0.40, H - 0.56, 9.20, 0.30, G_DEEP)
rect(s, 0.40, H - 0.56, 0.06, 0.30, G_BRIGHT)
tb(s, "LangGraph builds ON TOP of LangChain  ·  ADK is standalone  ·  All three are open source",
   0.52, H - 0.54, 9.0, 0.26, size=10, color=G_MINT, align=PP_ALIGN.CENTER)

footer_bar(s)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 8 — SAFETY & GUARDRAILS
# ══════════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(BLANK)
set_black_bg(s)
top_bar(s)
section_label(s, "SAFETY & GUARDRAILS  ·  PRODUCTION REQUIREMENTS")
slide_title(s, "Safety Is Not Optional — Build It In from Day One", color=G_FOREST)

safety = [
    ("Input\nGuardrails",
     "BEFORE LLM sees the query",
     ["PHI redaction (SSN, DOB, MRN)",
      "Topic filter — block clinical",
      "Content policy check"],
     G_FOREST),
    ("Output\nGuardrails",
     "BEFORE user sees the response",
     ["Grounding check (in the docs?)",
      "PII scan — no data leaked",
      "Tone & policy compliance"],
     G_DEEP),
    ("Prompt\nInjection",
     "Agent-specific attack vector",
     ["Malicious content in tool results",
      "Hijacks agent instructions",
      "Mitigate: separate instruction\nfrom data, restrict tools"],
     G_FOREST),
    ("Least\nPrivilege",
     "Each agent gets only what it needs",
     ["HR agent: read HR KB only",
      "No write tools unless required",
      "Separate IAM roles per agent",
      "Limits blast radius"],
     G_DEEP),
]
sw2, sh2 = 2.14, 3.70
sg = 0.13
for i, (title, sub, bullets, color) in enumerate(safety):
    x = 0.40 + i * (sw2 + sg)
    rect(s, x, 1.08, sw2, sh2, color)
    rect(s, x, 1.08, sw2, 0.44, G_BRIGHT)
    tb(s, title, x + 0.10, 1.10, sw2 - 0.20, 0.42,
       size=12, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    tb(s, sub, x + 0.10, 1.58, sw2 - 0.20, 0.28,
       size=9, color=G_BRIGHT)
    divider_line(s, 1.92, l=x + 0.10, w=sw2 - 0.20, color=G_MID)
    bullet_text = "\n".join(f"  ·  {b}" for b in bullets)
    tb(s, bullet_text, x + 0.10, 2.00, sw2 - 0.20, 2.60,
       size=10, color=G_MINT)

# Hard / soft stop row
rect(s, 0.40, 4.86, 4.40, 0.46, G_DEEP)
rect(s, 0.40, 4.86, 0.06, 0.46, G_BRIGHT)
tb(s, "Hard Stop: immediate refusal — no tools called, query terminated",
   0.52, 4.90, 4.20, 0.38, size=10, bold=True, color=WHITE)

rect(s, 5.20, 4.86, 4.40, 0.46, G_MID)
rect(s, 5.20, 4.86, 0.06, 0.46, G_BRIGHT)
tb(s, "Soft Stop: partial answer or redirect within policy constraints",
   5.32, 4.90, 4.20, 0.38, size=10, color=WHITE)

footer_bar(s)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 9 — EVALUATION & OBSERVABILITY
# ══════════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(BLANK)
set_black_bg(s)
top_bar(s)
section_label(s, "EVALUATION & OBSERVABILITY  ·  IF YOU CAN'T TRACE IT, YOU CAN'T TRUST IT")
slide_title(s, "Measure Everything — Agents Fail in Subtle Ways", color=G_FOREST)

# Left panel — evaluation metrics
rect(s, 0.40, 1.08, 4.20, 4.24, G_FOREST)
tb(s, "How Do You Know It Works?", 0.52, 1.14, 3.96, 0.36,
   size=13, bold=True, color=WHITE)
divider_line(s, 1.56, l=0.52, w=4.0, color=G_BRIGHT)

metrics = [
    ("Task Success Rate",       "Did the agent answer correctly?"),
    ("Tool Selection Accuracy", "Did it call the RIGHT tools?"),
    ("Hallucination Rate",      "Did it invent facts not in the docs?"),
    ("Latency",                 "How many LLM calls? Total time?"),
    ("Cost per Query",          "Calls × tokens × price"),
    ("Escalation Accuracy",     "Did it escalate when it should?"),
]
for i, (metric, desc) in enumerate(metrics):
    t = 1.64 + i * 0.60
    rect(s, 0.52, t, 3.96, 0.52, G_DEEP)
    rect(s, 0.52, t, 0.06, 0.52, G_BRIGHT)
    tb(s, metric, 0.64, t + 0.06, 1.90, 0.22, size=10, bold=True, color=G_BRIGHT)
    tb(s, desc,   0.64, t + 0.28, 3.76, 0.20, size=9,  color=G_MINT)

# Right panel — what to trace
rect(s, 4.90, 1.08, 4.70, 4.24, G_LIGHT)
rect(s, 4.90, 1.08, 4.70, 0.06, G_BRIGHT)
tb(s, "What to Trace in Every Call", 5.02, 1.14, 4.46, 0.36,
   size=13, bold=True, color=G_FOREST)
divider_line(s, 1.56, l=5.02, w=4.46, color=G_BRIGHT)

trace_items = [
    "Every node: entry, exit, timestamp, input, output",
    "Every LLM call: tokens in/out, model, latency",
    "Every tool call: name, args, result, latency",
    "Every routing decision: which branch and why",
    "Errors and retries: what failed, how recovered",
    "thread_id — correlate all steps of one conversation",
]
for i, item in enumerate(trace_items):
    t = 1.64 + i * 0.60
    rect(s, 5.02, t, 4.46, 0.52, G_LIGHT)
    rect(s, 5.02, t, 0.06, 0.52, G_FOREST)
    tb(s, item, 5.14, t + 0.12, 4.26, 0.34, size=10, color=G_FOREST)

footer_bar(s)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 10 — KEY TAKEAWAYS
# ══════════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(BLANK)
set_black_bg(s)
top_bar(s)
section_label(s, "KEY TAKEAWAYS  ·  WHAT TO REMEMBER")
slide_title(s, "Seven Things You Cannot Forget About Agentic AI", color=G_FOREST)

takeaways = [
    ("01", "Agent = LLM + loop + tools + memory. Not a prompt. Not a chain.",
           "The loop and the ability to act are the defining difference."),
    ("02", "ReAct is the universal loop — every framework uses it.",
           "Thought → Action → Observation, repeat until done."),
    ("03", "Multi-agent is the enterprise scaling path.",
           "Past 3–4 domains or 6–8 tools — use supervisor + specialists."),
    ("04", "RAG grounds answers. Agentic RAG adapts iteratively.",
           "Standard RAG for lookup. Agentic RAG for multi-step queries."),
    ("05", "Framework choice follows your cloud.",
           "LangChain + LangGraph for AWS/Azure. ADK for GCP / Vertex AI."),
    ("06", "Safety is not optional — build guardrails from day one.",
           "PHI, prompt injection, least privilege — non-negotiable in enterprise."),
    ("07", "If you can't trace it, you can't trust it.",
           "Trace every LLM call, tool call, and routing decision."),
]
row_h = 0.60
for i, (num, headline, detail) in enumerate(takeaways):
    t = 1.08 + i * (row_h + 0.04)
    bg = G_DEEP if i % 2 == 0 else G_FOREST
    rect(s, 0.40, t, 9.20, row_h, bg)
    # badge
    badge = s.shapes.add_shape(1, Inches(0.50), Inches(t + 0.12),
                                Inches(0.36), Inches(0.36))
    badge.fill.solid(); badge.fill.fore_color.rgb = G_BRIGHT
    badge.line.fill.background()
    tf2 = badge.text_frame
    tf2.paragraphs[0].alignment = PP_ALIGN.CENTER
    r2 = tf2.paragraphs[0].add_run()
    r2.text = num; r2.font.size = Pt(10); r2.font.bold = True
    r2.font.color.rgb = WHITE
    tb(s, headline, 0.96, t + 0.06, 4.60, 0.28, size=11, bold=True, color=G_BRIGHT)
    tb(s, detail,   5.70, t + 0.10, 3.76, 0.44, size=10, color=G_MINT)

footer_bar(s)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 11 — CLOSING
# ══════════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(BLANK)
set_black_bg(s)
top_bar(s)

section_label(s, "AGENTIC AI  ·  EXECUTIVE OVERVIEW")

tb(s, "Questions &", 0.40, 1.60, 9.20, 0.82,
   size=54, bold=True, color=WHITE)
tb(s, "Discussion.", 0.40, 2.40, 9.20, 0.82,
   size=54, bold=True, color=G_BRIGHT)

divider_line(s, 3.38, l=0.40, w=4.0, color=G_MID)

tb(s, "Rohid Dev  ·  github.com/rohiddev",
   0.40, 3.52, 6.0, 0.30, size=12, color=G_MINT)

# Reference strip
rect(s, 0.40, 4.10, 9.20, 0.06, G_MID)
refs = [
    ("Fundamentals", "agent-concepts-fundamentals-qa.txt"),
    ("LangGraph",    "langgraph-langchain-interview-prep.txt"),
    ("RAG",          "rag-graphrag-agentic-rag.txt"),
    ("Frameworks",   "langgraph-vs-langchain-vs-adk.txt"),
    ("Checklist",    "interviewchecklist.txt"),
]
rw = 9.20 / len(refs)
for i, (label, fname) in enumerate(refs):
    x = 0.40 + i * rw
    bg = G_DEEP if i % 2 == 0 else G_FOREST
    rect(s, x, 4.22, rw - 0.04, 1.0, bg)
    tb(s, label, x + 0.10, 4.30, rw - 0.20, 0.28,
       size=10, bold=True, color=G_BRIGHT)
    tb(s, fname,  x + 0.10, 4.62, rw - 0.20, 0.52,
       size=8, color=G_MINT)

footer_bar(s)


# ── Save ──────────────────────────────────────────────────────────────────────
out = "/Users/chandinidev/Documents/rohid-code/TCOE-Usecase/agentic-ai-overview.pptx"
prs.save(out)
print(f"Saved: {out}")
print(f"Slides: {len(prs.slides)}")
