"""Build the Physical Analyst storyboard presentation.

Updated 21 April 2026 after Session 10 introduced the summary + ask-question
function-pair-per-domain pattern. Storyboard now mirrors David's Guzman
corner-analyst framework: 3 domains × 2 functions = 6 total, plus an
explicit scope-refusal pattern baked into the ask-question prompts.
"""
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR

BG = RGBColor(0x10, 0x1F, 0x1C)
CARD = RGBColor(0x18, 0x2B, 0x27)
CARD_ALT = RGBColor(0x1C, 0x33, 0x2E)
ACCENT = RGBColor(0xEA, 0x5A, 0x1F)
ACCENT_SOFT = RGBColor(0xC2, 0x4A, 0x18)
TEXT = RGBColor(0xE8, 0xEC, 0xEB)
MUTED = RGBColor(0x8B, 0xA3, 0x9A)
RULE = RGBColor(0x2A, 0x43, 0x3D)
OK_GREEN = RGBColor(0x4A, 0x9E, 0x6B)
STOP_RED = RGBColor(0xB8, 0x4A, 0x3C)

SLIDE_W, SLIDE_H = Inches(13.333), Inches(7.5)


def set_bg(slide, color=BG):
    bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, SLIDE_W, SLIDE_H)
    bg.line.fill.background()
    bg.fill.solid()
    bg.fill.fore_color.rgb = color
    bg.shadow.inherit = False
    return bg


def add_text(slide, left, top, width, height, text, size=14, bold=False,
             color=TEXT, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP,
             italic=False):
    tb = slide.shapes.add_textbox(left, top, width, height)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = Emu(0)
    tf.margin_top = tf.margin_bottom = Emu(0)
    tf.vertical_anchor = anchor
    lines = text.split("\n") if isinstance(text, str) else text
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        run = p.add_run()
        run.text = line
        run.font.size = Pt(size)
        run.font.bold = bold
        run.font.italic = italic
        run.font.color.rgb = color
        run.font.name = "Helvetica Neue"
    return tb


def add_rect(slide, left, top, width, height, fill=CARD, line=None):
    sh = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    sh.adjustments[0] = 0.05
    sh.fill.solid()
    sh.fill.fore_color.rgb = fill
    if line is None:
        sh.line.fill.background()
    else:
        sh.line.color.rgb = line
        sh.line.width = Pt(0.75)
    sh.shadow.inherit = False
    return sh


def add_accent_bar(slide, left, top, width=Inches(0.08), height=Inches(0.45),
                   color=ACCENT):
    bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
    bar.line.fill.background()
    bar.fill.solid()
    bar.fill.fore_color.rgb = color
    bar.shadow.inherit = False


def footer(slide, label):
    add_text(slide, Inches(0.5), Inches(7.05), Inches(10), Inches(0.3),
             "TWELVE · CONTEXT ENGINEERING 2026 · PHYSICAL ANALYST STORYBOARD",
             size=9, color=MUTED)
    add_text(slide, Inches(11.5), Inches(7.05), Inches(1.5), Inches(0.3),
             label, size=9, color=ACCENT, align=PP_ALIGN.RIGHT, bold=True)


def header(slide, tag, title, subtitle=None):
    add_accent_bar(slide, Inches(0.5), Inches(0.5))
    add_text(slide, Inches(0.75), Inches(0.45), Inches(8), Inches(0.4),
             tag, size=14, bold=True, color=ACCENT)
    add_text(slide, Inches(0.5), Inches(0.95), Inches(12.3), Inches(0.7),
             title, size=32, bold=True, color=TEXT)
    if subtitle:
        add_text(slide, Inches(0.5), Inches(1.6), Inches(12.3), Inches(0.4),
                 subtitle, size=14, color=MUTED)


# ------------------------------------------------------------------ slides

def title_slide(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_bg(slide)
    add_accent_bar(slide, Inches(0.5), Inches(0.5))
    add_text(slide, Inches(0.75), Inches(0.45), Inches(6), Inches(0.4),
             "TWELVE · CONTEXT ENGINEERING 2026", size=14, bold=True, color=ACCENT)

    add_text(slide, Inches(0.5), Inches(2.3), Inches(12), Inches(1.2),
             "Physical Analyst", size=54, bold=True, color=TEXT)
    add_text(slide, Inches(0.5), Inches(3.3), Inches(12), Inches(0.8),
             "Storyboard for the AI analyst", size=28, color=MUTED)
    add_text(slide, Inches(0.5), Inches(4.0), Inches(12), Inches(0.5),
             "Three domains. Two depths per domain. Six functions.",
             size=18, color=ACCENT, italic=True)

    add_text(slide, Inches(0.5), Inches(5.3), Inches(12), Inches(0.4),
             "Liam Henshaw  ·  Pedro Carvalho", size=16, color=TEXT)
    add_text(slide, Inches(0.5), Inches(5.75), Inches(12), Inches(0.4),
             "Storyboard review  ·  23 April 2026", size=13, color=MUTED)
    add_text(slide, Inches(0.5), Inches(6.15), Inches(12), Inches(0.4),
             "Final presentation  ·  5 May 2026", size=13, color=MUTED)


def framework_slide(prs):
    """How the receptionist + 3x2 pattern works."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_bg(slide)
    header(slide, "HOW IT WORKS", "The receptionist routes to six functions",
           "Three domains · Two depths each · Pattern from Session 10 (Guzman corner-analyst example)")

    # 3x2 grid of functions
    col_w, col_h = Inches(4.0), Inches(1.7)
    start_x = Inches(0.5)
    start_y = Inches(2.4)
    gap_x, gap_y = Inches(0.15), Inches(0.2)

    domains = [
        ("PROFILE", "Who is this player physically",
         "getPhysicalProfile(player)",
         "askAboutProfile(player, q)"),
        ("SIMILARITY / COMPARE", "Player ↔ others",
         "findSimilarOrCompare(mode, A, B?)",
         "askAboutSimilarity(q)"),
        ("SHORTLIST", "Brief → candidates",
         "shortlistByAttribute(metric, pos, league, n)",
         "askShortlistQuestion(brief)"),
    ]

    # Domain column labels
    for i, (dom, tag, _, _) in enumerate(domains):
        x = start_x + (col_w + gap_x) * i
        add_text(slide, x, Inches(2.15), col_w, Inches(0.3),
                 f"DOMAIN {i+1} · {dom}", size=10, bold=True, color=ACCENT)
        add_text(slide, x, Inches(2.45), col_w, Inches(0.3),
                 tag, size=10, color=MUTED, italic=True)

    # Two rows — summary and ask
    row_labels = [("SUMMARY", "Deterministic. Fixed shape."),
                  ("ASK", "Intent-driven. Refusal baked in.")]

    y_base = Inches(2.85)
    for r, (row_tag, row_sub) in enumerate(row_labels):
        y = y_base + (col_h + gap_y) * r
        for i, (_, _, summary, ask) in enumerate(domains):
            x = start_x + (col_w + gap_x) * i
            func = summary if r == 0 else ask
            fill = CARD if r == 0 else CARD_ALT
            add_rect(slide, x, y, col_w, col_h, fill=fill)
            add_text(slide, x + Inches(0.2), y + Inches(0.15),
                     col_w - Inches(0.4), Inches(0.3),
                     row_tag, size=10, bold=True, color=ACCENT)
            add_text(slide, x + Inches(0.2), y + Inches(0.5),
                     col_w - Inches(0.4), Inches(0.4),
                     func, size=12, bold=True, color=TEXT)
            add_text(slide, x + Inches(0.2), y + Inches(1.05),
                     col_w - Inches(0.4), Inches(0.55),
                     row_sub, size=10, color=MUTED)

    # Bottom note
    add_text(slide, Inches(0.5), Inches(6.55), Inches(12.3), Inches(0.35),
             "Ask-question functions reuse each domain's knowledge base — three wordalisations + three ask-templates, not six separate builds.",
             size=11, color=MUTED, italic=True)

    footer(slide, "FRAMEWORK")


def workflow_slide(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_bg(slide)
    header(slide, "THE SPORTING DIRECTOR'S WORKFLOW",
           "One loop, three entry points",
           "Start from a brief · profile a target · find alternatives or compare")

    y = Inches(2.4)
    box_w, box_h = Inches(3.9), Inches(2.0)
    gap = Inches(0.25)
    start_x = Inches(0.5)

    steps = [
        ("SHORTLIST", "Start from a brief",
         "\"Top 5 quickest CBs in the PL\"\n\"Quick LB under 24 with endurance\""),
        ("PROFILE", "Describe a known player",
         "\"What's Gvardiol's profile?\"\n\"Is Kane still fit enough?\""),
        ("SIMILAR / COMPARE", "Pivot to alternatives",
         "\"Who could replace him in the Bundesliga?\"\n\"Compare Saliba vs Konaté\""),
    ]
    for i, (title, sub, examples) in enumerate(steps):
        x = start_x + (box_w + gap) * i
        add_rect(slide, x, y, box_w, box_h)
        add_text(slide, x + Inches(0.25), y + Inches(0.2),
                 box_w - Inches(0.5), Inches(0.35),
                 f"STEP {i+1}", size=10, bold=True, color=ACCENT)
        add_text(slide, x + Inches(0.25), y + Inches(0.55),
                 box_w - Inches(0.5), Inches(0.45),
                 title, size=18, bold=True, color=TEXT)
        add_text(slide, x + Inches(0.25), y + Inches(1.0),
                 box_w - Inches(0.5), Inches(0.35),
                 sub, size=12, color=MUTED)
        add_text(slide, x + Inches(0.25), y + Inches(1.35),
                 box_w - Inches(0.5), Inches(0.65),
                 examples, size=10, color=TEXT, italic=True)

        if i < len(steps) - 1:
            arrow_x = x + box_w - Inches(0.05)
            arrow = slide.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW,
                                            arrow_x, y + Inches(0.85),
                                            Inches(0.3), Inches(0.3))
            arrow.line.fill.background()
            arrow.fill.solid()
            arrow.fill.fore_color.rgb = ACCENT
            arrow.shadow.inherit = False

    # Bottom note
    add_rect(slide, Inches(0.5), Inches(4.8), Inches(12.3), Inches(1.9))
    add_text(slide, Inches(0.8), Inches(5.0), Inches(11.7), Inches(0.35),
             "WHY THIS SHAPE", size=11, bold=True, color=ACCENT)
    add_text(slide, Inches(0.8), Inches(5.4), Inches(11.7), Inches(1.3),
             [
                "Three domains cover a sporting director's real-world loop: brief → target → alternatives.",
                "Each domain answers at two depths — a fixed summary for the obvious question, an ask-question",
                "function for the nuanced one. Same knowledge base underneath, different prompt on top.",
                "",
                "Scope rules: same position group only for similarity and compare. Rule-based — no ML.",
             ],
             size=13, color=TEXT)

    footer(slide, "WORKFLOW")


def domain_slide(prs, tag, domain_name, subtitle, summary, ask):
    """summary and ask are dicts with: sig, examples, output, notes."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_bg(slide)
    header(slide, tag, domain_name, subtitle)

    col_w = Inches(6.0)
    col_h = Inches(4.95)
    y = Inches(2.15)

    # Left column — SUMMARY
    add_rect(slide, Inches(0.5), y, col_w, col_h)
    add_accent_bar(slide, Inches(0.5), y + Inches(0.0), width=col_w,
                   height=Inches(0.04))
    add_text(slide, Inches(0.8), y + Inches(0.2), col_w - Inches(0.6),
             Inches(0.35), "SUMMARY · deterministic", size=10, bold=True,
             color=ACCENT)
    add_text(slide, Inches(0.8), y + Inches(0.55), col_w - Inches(0.6),
             Inches(0.45), summary["sig"], size=13, bold=True, color=TEXT)

    add_text(slide, Inches(0.8), y + Inches(1.1), col_w - Inches(0.6),
             Inches(0.3), "EXAMPLE QUESTIONS", size=9, bold=True, color=MUTED)
    ex_text = "\n".join(f"•  {e}" for e in summary["examples"])
    add_text(slide, Inches(0.8), y + Inches(1.4), col_w - Inches(0.6),
             Inches(1.6), ex_text, size=11, color=TEXT)

    add_text(slide, Inches(0.8), y + Inches(3.15), col_w - Inches(0.6),
             Inches(0.3), "OUTPUT", size=9, bold=True, color=MUTED)
    add_text(slide, Inches(0.8), y + Inches(3.45), col_w - Inches(0.6),
             Inches(0.7), summary["output"], size=11, color=TEXT)

    add_text(slide, Inches(0.8), y + Inches(4.15), col_w - Inches(0.6),
             Inches(0.3), "NOTES", size=9, bold=True, color=MUTED)
    add_text(slide, Inches(0.8), y + Inches(4.4), col_w - Inches(0.6),
             Inches(0.55), summary["notes"], size=10, color=MUTED)

    # Right column — ASK
    x2 = Inches(6.8)
    add_rect(slide, x2, y, col_w, col_h, fill=CARD_ALT)
    add_text(slide, x2 + Inches(0.3), y + Inches(0.2), col_w - Inches(0.6),
             Inches(0.35), "ASK-QUESTION · intent-driven", size=10, bold=True,
             color=ACCENT)
    add_text(slide, x2 + Inches(0.3), y + Inches(0.55), col_w - Inches(0.6),
             Inches(0.45), ask["sig"], size=13, bold=True, color=TEXT)

    add_text(slide, x2 + Inches(0.3), y + Inches(1.1), col_w - Inches(0.6),
             Inches(0.3), "EXAMPLE QUESTIONS", size=9, bold=True, color=MUTED)
    ex_text = "\n".join(f"•  {e}" for e in ask["examples"])
    add_text(slide, x2 + Inches(0.3), y + Inches(1.4), col_w - Inches(0.6),
             Inches(1.6), ex_text, size=11, color=TEXT)

    add_text(slide, x2 + Inches(0.3), y + Inches(3.15), col_w - Inches(0.6),
             Inches(0.3), "OUTPUT", size=9, bold=True, color=MUTED)
    add_text(slide, x2 + Inches(0.3), y + Inches(3.45), col_w - Inches(0.6),
             Inches(0.7), ask["output"], size=11, color=TEXT)

    add_text(slide, x2 + Inches(0.3), y + Inches(4.15), col_w - Inches(0.6),
             Inches(0.3), "NOTES", size=9, bold=True, color=MUTED)
    add_text(slide, x2 + Inches(0.3), y + Inches(4.4), col_w - Inches(0.6),
             Inches(0.55), ask["notes"], size=10, color=MUTED)

    footer(slide, tag)


def scope_pattern_slide(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_bg(slide)
    header(slide, "SCOPE REFUSAL", "Staying in the physical-data lane",
           "Baked into every ask-question function. No separate guard function.")

    # In / Out table
    y = Inches(2.15)
    col_w = Inches(6.0)
    col_h = Inches(3.0)

    # IN scope
    add_rect(slide, Inches(0.5), y, col_w, col_h)
    add_text(slide, Inches(0.8), y + Inches(0.2), col_w - Inches(0.6),
             Inches(0.35), "IN SCOPE · tracking data", size=11, bold=True,
             color=OK_GREEN)
    in_items = [
        "Speed · acceleration · deceleration · top speed",
        "Volume — distance, sprints, high-speed runs",
        "Intensity — high-intensity distance, repeated sprint ability",
        "The four physical pillars",
    ]
    add_text(slide, Inches(0.8), y + Inches(0.7), col_w - Inches(0.6),
             Inches(2.2),
             "\n".join(f"•  {i}" for i in in_items),
             size=12, color=TEXT)

    # OUT of scope
    x2 = Inches(6.8)
    add_rect(slide, x2, y, col_w, col_h)
    add_text(slide, x2 + Inches(0.3), y + Inches(0.2), col_w - Inches(0.6),
             Inches(0.35), "OUT OF SCOPE · refuse + redirect", size=11,
             bold=True, color=STOP_RED)
    out_items = [
        "Tactical — positioning, marking, pressing, system fit",
        "Technical — first touch, shooting, passing, finishing",
        "Mental — composure, leadership, decision-making",
        "Team context — manager fit, teammates, style",
    ]
    add_text(slide, x2 + Inches(0.3), y + Inches(0.7), col_w - Inches(0.6),
             Inches(2.2),
             "\n".join(f"•  {i}" for i in out_items),
             size=12, color=TEXT)

    # Three-part pattern across the bottom
    y2 = Inches(5.35)
    step_w = Inches(4.0)
    gap = Inches(0.15)

    steps = [
        ("1 · ACKNOWLEDGE", "Name the question briefly."),
        ("2 · STATE THE LIMIT", "\"That's a tactical/technical read I can't speak to.\""),
        ("3 · REDIRECT", "Pivot to the nearest physical-data angle, or say plainly there isn't one."),
    ]
    for i, (t, body) in enumerate(steps):
        x = Inches(0.5) + (step_w + gap) * i
        add_rect(slide, x, y2, step_w, Inches(1.35), fill=CARD_ALT)
        add_text(slide, x + Inches(0.2), y2 + Inches(0.2), step_w - Inches(0.4),
                 Inches(0.35), t, size=11, bold=True, color=ACCENT)
        add_text(slide, x + Inches(0.2), y2 + Inches(0.55), step_w - Inches(0.4),
                 Inches(0.75), body, size=12, color=TEXT)

    footer(slide, "SCOPE")


def scope_examples_slide(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_bg(slide)
    header(slide, "SCOPE REFUSAL · EXAMPLES",
           "Questions the analyst will refuse",
           "Out-of-scope asks the bot won't answer directly — it refuses and redirects to the physical angle instead.")

    examples = [
        ("PROFILE · askAboutProfile",
         "Is Kane a good finisher?",
         "tactical · refuse + redirect",
         "Finishing is a technical read I can't speak to — I only have physical data. Kane still shows top-quartile explosive acceleration in the box for a forward his age, and his repeated sprint profile means he's not fading in the 80th minute. Whether he puts the chances away is outside what tracking shows."),
        ("SIMILARITY · askAboutSimilarity",
         "Find me a leader type like Van Dijk.",
         "mental · refuse + redirect",
         "Leadership isn't something tracking data captures. I can give you the physical archetype — CBs with his combination of aerial physicality, recovery speed, and endurance at age 32+. Closest physical matches are [X, Y, Z]. Whether they carry a back line the way he does is a separate judgement."),
        ("SHORTLIST · askShortlistQuestion",
         "Find me a CB who can play out from the back.",
         "technical · refuse + redirect",
         "Ball-playing ability is technical, outside my scope. I can shortlist CBs whose physical profile matches players known for that role as a proxy — similar endurance, high-intensity running, age band. Caveat: the passing itself you'll need to evaluate separately."),
    ]

    y = Inches(2.15)
    for label, question, flag, answer in examples:
        add_rect(slide, Inches(0.5), y, Inches(12.3), Inches(1.55))
        add_text(slide, Inches(0.8), y + Inches(0.15), Inches(8),
                 Inches(0.3), label, size=10, bold=True, color=ACCENT)
        add_text(slide, Inches(8.8), y + Inches(0.15), Inches(4),
                 Inches(0.3), flag.upper(), size=9, bold=True, color=STOP_RED,
                 align=PP_ALIGN.RIGHT)

        # User question
        add_text(slide, Inches(0.8), y + Inches(0.5), Inches(1.2),
                 Inches(0.3), "USER ASKS", size=9, bold=True, color=MUTED)
        add_text(slide, Inches(2.1), y + Inches(0.48), Inches(10.4),
                 Inches(0.35), f"“{question}”", size=13, bold=True,
                 color=TEXT, italic=True)

        # Bot response
        add_text(slide, Inches(0.8), y + Inches(0.9), Inches(1.2),
                 Inches(0.3), "ANALYST", size=9, bold=True, color=MUTED)
        add_text(slide, Inches(2.1), y + Inches(0.88), Inches(10.4),
                 Inches(0.65), answer, size=11, color=TEXT)
        y += Inches(1.7)

    footer(slide, "SCOPE")


def open_questions_slide(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_bg(slide)
    header(slide, "FEEDBACK NEEDED", "Open for Thursday",
           "Four questions we'd like David's steer on")

    items = [
        ("Knowledge-base sizing",
         "Session 3 guidance was 50–60 Q&A pairs per wordalisation. For three domains that's 150–180 pairs total. Aim for ~30 per domain and lean on few-shot examples for the gaps?"),
        ("Embedding retrieval inside function calling",
         "David flagged this as an unbuilt extension in Session 10. For now we stuff the full Q&A base into each call. Add embedding retrieval only if token budget bites?"),
        ("Shortlist summary output richness",
         "Ranked list only, or list with a mini-radar per candidate? Full radar reserved for Domain 2 compare-mode to keep the visuals distinct."),
        ("Multi-intent dispatch",
         "Session 10's Arsenal example fired TWO functions in one turn (summary + ask). Wire that for Domain 1 (\"profile and is he PL-ready?\") or keep one-function-per-turn for demo simplicity?"),
    ]

    y = Inches(2.15)
    for label, body in items:
        add_rect(slide, Inches(0.5), y, Inches(12.3), Inches(1.1))
        add_text(slide, Inches(0.8), y + Inches(0.15), Inches(11.7),
                 Inches(0.35), label, size=13, bold=True, color=ACCENT)
        add_text(slide, Inches(0.8), y + Inches(0.5), Inches(11.7),
                 Inches(0.55), body, size=11, color=TEXT)
        y += Inches(1.22)

    footer(slide, "OPEN ITEMS")


# ------------------------------------------------------------------ build

def build():
    prs = Presentation()
    prs.slide_width = SLIDE_W
    prs.slide_height = SLIDE_H

    title_slide(prs)
    framework_slide(prs)
    workflow_slide(prs)

    # Domain 1 — Profile
    domain_slide(
        prs, "DOMAIN 1 · PROFILE", "Profile",
        "Who is this player physically — at two depths",
        summary={
            "sig": "getPhysicalProfile(player)",
            "examples": [
                "What's this player's physical profile?",
                "Describe [player]'s physical strengths and weaknesses",
                "Tell me about [player]'s physical game",
            ],
            "output": "Narrative in analyst's voice. Four pillars in contribution order, peer-group context, trade-offs flagged.",
            "notes": "Wordalisation 1 (already written). Player-only data. Peer group = same position, same season.",
        },
        ask={
            "sig": "askAboutProfile(player, question)",
            "examples": [
                "Is Gvardiol fast enough for a PL high line?",
                "Does Kane still have the engine to play 90?",
                "Can Salah still press the way he did three years ago?",
            ],
            "output": "Focused narrative answer to the specific question. Pulls only the relevant pillars. Refuses out-of-scope questions.",
            "notes": "Same knowledge base as summary. Refusal + redirect pattern built into prompt.",
        },
    )

    # Domain 2 — Similarity / Compare
    domain_slide(
        prs, "DOMAIN 2 · SIMILARITY / COMPARE", "Similarity · Compare",
        "Player ↔ others — one summary function with two modes",
        summary={
            "sig": "findSimilarOrCompare(mode, playerA, playerB?)",
            "examples": [
                "Who else has a similar physical profile to Gvardiol?",
                "Compare Saliba and Konaté physically",
                "Closest physical match to peak Van Dijk?",
            ],
            "output": "mode=similar → top 5 nearest neighbours by cosine similarity.\nmode=compare → Twelve-platform radar + narrative summary.",
            "notes": "Wordalisation 2 (new). Same-position peer group only. Rule-based similarity, no ML.",
        },
        ask={
            "sig": "askAboutSimilarity(question)",
            "examples": [
                "If we lose Gvardiol, who in the Bundesliga fits?",
                "Who's physically closer to Rodri — Zubimendi or Caicedo?",
                "Find a centre back under 25 with a similar profile to Saliba",
            ],
            "output": "Narrative answer that narrows the candidate pool by league, age, or intent before ranking.",
            "notes": "Position-group bound inherited from summary. Tactical 'plays like X' questions refused and redirected to physical archetype.",
        },
    )

    # Domain 3 — Shortlist
    domain_slide(
        prs, "DOMAIN 3 · SHORTLIST", "Shortlist",
        "Brief → candidates — structured and free-text entry points",
        summary={
            "sig": "shortlistByAttribute(metric, position, league, n)",
            "examples": [
                "Top 5 quickest centre backs in the Premier League",
                "Fastest wingers in Serie A",
                "Which midfielders cover the most high-intensity distance?",
            ],
            "output": "Ranked table — Player | Club | Rank — with a one-line wordalisation flagging the metric each leads on.",
            "notes": "Wordalisation 3 (new). Rule-based filter + rank. Refuses if metric isn't in the data.",
        },
        ask={
            "sig": "askShortlistQuestion(brief)",
            "examples": [
                "Find me a quick LB under 24 with good high-intensity endurance",
                "Who's a physical match for a ball-winning 6 with recovery pace?",
                "Shortlist forwards with elite sprint volume across a full 90",
            ],
            "output": "Parses multi-constraint briefs. Ranks candidates, wordalises the shortlist with the metric hook per player.",
            "notes": "Parameter extraction via LLM (Session 10 annotation pattern). Refuses tactical briefs; answers physical proxies only.",
        },
    )

    scope_pattern_slide(prs)
    scope_examples_slide(prs)

    out = "Physical_Analyst_Storyboard.pptx"
    prs.save(out)
    print(f"Saved {out}")


if __name__ == "__main__":
    build()
