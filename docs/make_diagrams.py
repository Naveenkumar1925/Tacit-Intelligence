"""Render the Plant Brain architecture diagrams as plain black-on-white PNGs.

Run:  py docs/make_diagrams.py     -> docs/img/fig1..fig5.png

Deliberately monochrome: white ground, black text, black rules. Prints
cleanly, embeds cleanly in Word, and reproduces on a projector.
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

OUT = Path(__file__).parent / "img"
OUT.mkdir(exist_ok=True)

FONT = {"family": "DejaVu Sans"}
DPI = 200


def canvas(w, h):
    fig, ax = plt.subplots(figsize=(w, h))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")
    return fig, ax


def box(ax, x, y, w, h, text, size=7.4, bold=False, dashed=False, fill="white",
        round_=False):
    style = "round,pad=0.4,rounding_size=1.6" if round_ else "square,pad=0"
    ax.add_patch(FancyBboxPatch(
        (x, y), w, h, boxstyle=style, linewidth=1.0, edgecolor="black",
        facecolor=fill, linestyle="--" if dashed else "-", zorder=2))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=size,
            color="black", zorder=3, linespacing=1.45,
            fontweight="bold" if bold else "normal", **FONT)


def group(ax, x, y, w, h, label):
    ax.add_patch(FancyBboxPatch(
        (x, y), w, h, boxstyle="square,pad=0", linewidth=1.0, edgecolor="black",
        facecolor="#F2F2F2", zorder=1))
    ax.text(x + 1.6, y + h - 2.4, label, ha="left", va="center", fontsize=7.2,
            color="black", fontweight="bold", zorder=3, **FONT)


def arrow(ax, p1, p2, dashed=False, label=None, size=6.4, rad=0.0):
    ax.add_patch(FancyArrowPatch(
        p1, p2, arrowstyle="-|>", mutation_scale=9, linewidth=0.9,
        color="black", zorder=4, linestyle="--" if dashed else "-",
        connectionstyle=f"arc3,rad={rad}", shrinkA=1, shrinkB=1))
    if label:
        ax.text((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2 + 1.2, label,
                ha="center", va="bottom", fontsize=size, color="black",
                zorder=5, **FONT)


def save(fig, name):
    fig.savefig(OUT / f"{name}.png", dpi=DPI, facecolor="white",
                bbox_inches="tight", pad_inches=0.12)
    plt.close(fig)
    print("wrote", OUT / f"{name}.png")


# ---------------------------------------------------------------- Fig 1
def fig1():
    fig, ax = canvas(9.2, 7.6)

    group(ax, 2, 82, 92, 16, "CORPUS  —  seeded, deterministic, self-verifying")
    box(ax, 4, 83, 27, 9, "generate_corpus.py\n12 equipment · 119 work orders\n6 inspections · 8 SOP PDFs")
    box(ax, 34, 83, 27, 9, "generate_qms.py\nQS-001 · 9 clauses\n72 KPIs · 6 NCRs")
    box(ax, 64, 83, 28, 9, "3 voice clips\nTamil · Hindi · +1")

    group(ax, 2, 58, 92, 20, "P1 · INGEST & BUILD      P2 · VOICE CAPTURE")
    box(ax, 4, 65, 20, 8, "Structured\nno LLM", bold=True)
    box(ax, 26, 65, 21, 8, "Narrative\nchunk → regex → bind")
    box(ax, 49, 65, 21, 8, "Clause-aware\nsplit on clause no.")
    box(ax, 72, 65, 20, 8, "Voice\ntranslate → claims")
    box(ax, 24, 59, 48, 4.6, "ENTITY RESOLUTION   —   4 spellings → 1 node",
        bold=True, round_=True)

    group(ax, 2, 38, 92, 16, "NEO4J  —  single datastore, dual retrieval mode")
    box(ax, 5, 39.5, 41, 10, "VECTOR + FULL-TEXT INDEX\nChunk · Procedure\nClause · TacitKnowledge")
    box(ax, 50, 39.5, 41, 10, "STRUCTURED TYPED NODES\nEquipment · WorkOrder\nQualityKPI · NCR — never embedded")

    group(ax, 2, 18, 92, 16, "P3 · ASK      P4 · WATCH")
    box(ax, 5, 19.5, 41, 10, "Ask — hybrid retrieval, graph\nexpansion, analytics leg,\ncited synthesis")
    box(ax, 50, 19.5, 41, 10, "Watch — arithmetic detection\non a timer; LLM only\nwrites the narrative")

    group(ax, 2, 2, 92, 12, "DELIVERY  —  FastAPI + responsive web")
    box(ax, 5, 3, 26, 6.5, "Chat + citations")
    box(ax, 35, 3, 26, 6.5, "Alert panel")
    box(ax, 65, 3, 26, 6.5, "Graph explorer")

    arrow(ax, (17, 83), (14, 73))
    arrow(ax, (17, 83), (36, 73))
    arrow(ax, (47, 83), (59, 73))
    arrow(ax, (78, 83), (82, 73))
    for x in (14, 36, 59, 82):
        arrow(ax, (x, 65), (48, 63.6), rad=0.04)
    arrow(ax, (48, 59), (48, 54))
    arrow(ax, (25, 39.5), (25, 29.5))
    arrow(ax, (70, 39.5), (70, 29.5))
    arrow(ax, (25, 19.5), (18, 14))
    arrow(ax, (70, 19.5), (78, 14))
    arrow(ax, (95, 24), (95, 44), dashed=True)
    ax.text(96.4, 34, "writes :Alert back", rotation=90, ha="left", va="center",
            fontsize=6.2, **FONT)
    save(fig, "fig1_architecture")


# ---------------------------------------------------------------- Fig 2
def fig2():
    fig, ax = canvas(9.4, 6.2)
    cols = [
        (2, "PATH 1 — STRUCTURED (no LLM)",
         ["registers · work orders\ninspections · KPIs · NCRs",
          "parse dates,\nboth formats",
          "repair failure code against\nclosed vocabulary",
          "typed nodes"]),
        (26.5, "PATH 2 — NARRATIVE",
         ["SOP PDFs",
          "chunk on heading / step\n~600 tokens · 15% overlap",
          "regex pass:\ntags · dates · measurements",
          "then LLM binds relations\nbetween known entities"]),
        (51, "PATH 3 — CLAUSE-AWARE",
         ["QS-001 standard",
          "split on clause number,\nnot token window",
          ":Clause + embedding"]),
        (75.5, "PATH 4 — VOICE",
         ["audio, any language",
          "Whisper translate;\nkeep timestamps + language",
          "normalise spoken digits,\ntag regex — never trust ASR",
          "LLM structures typed claims"]),
    ]
    for x, title, steps in cols:
        group(ax, x, 30, 22.5, 64, "")
        ax.text(x + 11.25, 91, title, ha="center", va="center", fontsize=6.5,
                fontweight="bold", **FONT)
        y = 77
        for i, s in enumerate(steps):
            box(ax, x + 1.2, y, 20.1, 10, s, size=6.5)
            if i < len(steps) - 1:
                arrow(ax, (x + 11.25, y), (x + 11.25, y - 4))
            y -= 14
    box(ax, 24, 16, 52, 6, "ENTITY RESOLUTION   —   canonicalise · merge · alias list",
        bold=True, round_=True)
    for x, *_ in cols:
        arrow(ax, (x + 11.25, 30), (50, 22.5), rad=0.05)
    box(ax, 40, 4, 20, 6, "NEO4J", bold=True)
    arrow(ax, (50, 16), (50, 10))
    save(fig, "fig2_ingestion")


# ---------------------------------------------------------------- Fig 3
def fig3a():
    """Maintenance core — Equipment as hub, short straight spokes."""
    fig, ax = canvas(9.4, 6.4)
    B = lambda x, y, w, h, t, b=False: box(ax, x, y, w, h, t, size=6.6, bold=b)

    B(38, 44, 24, 11, "(:Equipment)\ntag · class\ncriticality · aliases[]", True)

    B(20, 87, 16, 6, "(:Site)")
    B(44, 87, 16, 6, "(:Area)")
    arrow(ax, (36, 90), (44, 90), label="CONTAINS", size=5.8)
    arrow(ax, (52, 87), (52, 55), label="CONTAINS", size=5.8)

    B(2, 68, 22, 10, "(:WorkOrder)\ndate · type · downtime_hrs")
    B(2, 54, 22, 8, "(:FailureMode)\nISO 14224 code")
    arrow(ax, (13, 68), (13, 62), label="RESULTED_IN", size=5.8)
    arrow(ax, (24, 71), (39, 55), label="PERFORMED_ON", size=5.8)

    B(2, 36, 24, 8, "(:InspectionRecord)\nvalid_until")
    arrow(ax, (26, 40), (38, 46), label="ON", size=5.8)

    B(2, 16, 15, 7, "(:Document)")
    B(26, 16, 18, 7, "(:Chunk)\nembedding")
    arrow(ax, (17, 19.5), (26, 19.5), label="HAS_CHUNK", size=5.8)
    arrow(ax, (40, 23), (45, 44), label="MENTIONS", size=5.8)

    B(72, 68, 24, 8, "(:Procedure)\nembedding")
    arrow(ax, (76, 68), (62, 54), label="APPLIES_TO", size=5.8)

    B(70, 44, 28, 11, "(:TacitKnowledge)\nlang · audio_id · t_start\nembedding")
    arrow(ax, (70, 49.5), (62, 49.5), label="APPLIES_TO", size=5.8)

    B(70, 18, 26, 9, "(:Alert)\nkind · severity")
    arrow(ax, (76, 27), (58, 44), label="ABOUT", size=5.8)
    ax.text(83, 12, "EVIDENCED_BY  →  WorkOrder · Chunk · TacitKnowledge",
            ha="center", va="center", fontsize=6.0, **FONT)
    save(fig, "fig3a_schema_core")


def fig3b():
    """QMS extension — clause, non-conformance, process, KPI."""
    fig, ax = canvas(9.4, 4.6)
    B = lambda x, y, w, h, t, b=False: box(ax, x, y, w, h, t, size=6.8, bold=b)

    B(4, 78, 20, 8, "(:Standard)\nQS-001")
    B(40, 78, 22, 8, "(:Clause)\nclause_id · embedding")
    arrow(ax, (24, 82), (40, 82), label="HAS_CLAUSE", size=6.0)

    B(38, 40, 26, 11, "(:Equipment)", True)
    arrow(ax, (51, 78), (51, 51), label="APPLIES_TO", size=6.0)

    B(76, 58, 22, 8, "(:NCR)\nnon-conformance")
    arrow(ax, (80, 66), (62, 82), label="CITES", size=6.0)
    arrow(ax, (80, 58), (64, 48), label="AGAINST", size=6.0)

    B(4, 40, 24, 8, "(:Process)\nPRC-101 · PRC-301")
    arrow(ax, (28, 44), (38, 45), label="USES", size=6.0)

    B(2, 10, 30, 12, "(:QualityKPI)\nCpk · PPM · period\nnot embedded  —  computed over", True)
    arrow(ax, (12, 22), (12, 40))
    ax.text(13.6, 31, "OF", fontsize=6.0, ha="left", va="center", **FONT)
    arrow(ax, (32, 18), (44, 40), label="FOR", size=6.0)
    save(fig, "fig3b_schema_qms")


# ---------------------------------------------------------------- Fig 4
def fig4():
    fig, ax = canvas(8.6, 7.0)
    box(ax, 34, 92, 32, 6, "Question", bold=True, round_=True)
    box(ax, 14, 79, 72, 9,
        "Anchor detection\nequipment tag · class/area phrase · process name · clause number")
    box(ax, 30, 68, 40, 7, "Intent classifier  —  sets blend ratio", bold=True)
    arrow(ax, (50, 92), (50, 88))
    arrow(ax, (50, 79), (50, 75))

    legs = [(2, "BM25\nfull-text"), (26, "Dense vector\n768 d"),
            (50, "Graph expansion\n2 hops, one round trip"),
            (75, "Analytics leg\ncomputed KPIs")]
    for x, t in legs:
        box(ax, x, 54, 23, 8, t)
        arrow(ax, (50, 68), (x + 11.5, 62), rad=0.05)

    box(ax, 8, 43, 35, 6, "RRF fusion   Σ 1/(60+rank)", bold=True)
    arrow(ax, (13, 54), (20, 49))
    arrow(ax, (37, 54), (30, 49))

    box(ax, 18, 29, 64, 10,
        "Evidence assembly\ncomputed → clauses → graph / text by blend\nsymptom-mode rows first")
    arrow(ax, (25, 43), (35, 39))
    arrow(ax, (61, 54), (58, 39))
    arrow(ax, (86, 54), (72, 39))

    box(ax, 22, 20, 56, 6, "Synthesis  —  every sentence carries [E n]")
    arrow(ax, (50, 29), (50, 26))
    box(ax, 18, 9, 64, 8,
        "Computed confidence\n0.5 retrieval + 0.4 citation fraction + 0.1 overlap", bold=True)
    arrow(ax, (50, 20), (50, 17))

    box(ax, 2, -1, 40, 6, "Cited answer → page · timestamp · query", round_=True)
    box(ax, 56, -1, 42, 6, "Abstain — 'not present in the corpus'", round_=True)
    arrow(ax, (34, 9), (22, 5))
    arrow(ax, (66, 9), (77, 5))
    ax.text(25, 7.4, "above", fontsize=6.2, ha="center", **FONT)
    ax.text(74, 7.4, "below", fontsize=6.2, ha="center", **FONT)
    save(fig, "fig4_retrieval")


# ---------------------------------------------------------------- Fig 5
def fig5():
    fig, ax = canvas(8.2, 6.4)
    box(ax, 18, 91, 64, 6, "Every (:Procedure, :TacitKnowledge) pair", round_=True)
    gates = [
        (78, "Same equipment?   both APPLIES_TO", "reject"),
        (62, "Cosine similarity ≥ 0.60 on chunk text?", "reject"),
        (46, "Shared activity keyword?  strainer · seal · cleaning",
         "reject — SAME-TOPIC GATE\nembedding alone fires on\nunrelated documents\nin a small corpus"),
    ]
    y_prev = 91
    for y, q, rej in gates:
        box(ax, 12, y, 56, 7, q, bold=True)
        arrow(ax, (40, y_prev), (40, y + 7))
        tall = "GATE" in rej
        box(ax, 72, y - 3 if tall else y + 1, 27, 13 if tall else 5, rej, size=5.9)
        arrow(ax, (68, y + 3.5), (72, y + 3.5), label="no", size=5.8)
        y_prev = y

    box(ax, 12, 32, 56, 6, "Extract stated frequencies from both texts")
    arrow(ax, (40, 46), (40, 38), label="yes", size=5.8)

    box(ax, 8, 19, 60, 7,
        "Does the operator state a frequency the procedure does NOT?", bold=True)
    arrow(ax, (40, 32), (40, 26))
    box(ax, 72, 20, 27, 5, "reject — they agree", size=5.9)
    arrow(ax, (68, 22.5), (72, 22.5), label="no", size=5.8)

    box(ax, 8, 4, 60, 10,
        "DIVERGENCE\nprocedure says X · N operators say Y\n→ governing clause · audio timestamps",
        bold=True, round_=True)
    arrow(ax, (40, 19), (40, 14), label="yes", size=5.8)
    save(fig, "fig5_divergence")


if __name__ == "__main__":
    fig1(); fig2(); fig3a(); fig3b(); fig4(); fig5()
    print("done")
