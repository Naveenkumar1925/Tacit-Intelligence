"""QMS corpus generator: quality standard + KPIs + NCR register (seeded).

Run:  py datagen/generate_qms.py

Outputs:
    corpus/qms/QS-001.pdf        original-text plant quality standard, clause-numbered
    corpus/quality_kpis.xlsx     monthly Cpk / PPM per process — structured, NEVER embedded
    corpus/ncr_register.xlsx     non-conformance reports linking equipment -> clause

Planted quality patterns (asserted below):
    Q1 capability drift: PRC-301 (CV-301A) Cpk falls below 1.33 in the latest
       months — coheres with CV-301A's expired stroke-test inspection + NCR-002
    Q2 PPM rise: PRC-101 (P-101A) PPM climbs through the monsoon months —
       coheres with the strainer divergence story + NCR-001 against clause 8.5.1

All standard text is original; clause numbering style follows common QMS
taxonomies but no real standard's text is reproduced.
"""

import random
import sys
from datetime import date
from pathlib import Path

from openpyxl import Workbook
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / "corpus"
DEMO_DATE = date(2026, 7, 22)          # keep in lockstep with generate_corpus.py
rng = random.Random(9)

# --------------------------------------------------------------------- standard
STANDARD = {
    "std_id": "QS-001",
    "title": "Plant Site A Quality Management Standard",
    "revision": "Rev 2",
    "rev_date": "10/01/2025",
    "overlay": "automotive customer overlay (IATF 16949 aligned)",
}

CLAUSES = [
    ("4.1", "Context of the plant quality system", None,
     "The plant shall determine the internal and external issues that affect its ability to "
     "deliver conforming product, including the condition of production equipment, the "
     "availability of experienced operators, and seasonal factors that alter process inputs. "
     "The quality system applies to all production and utilities equipment registered at "
     "Plant Site A and shall be reviewed when the equipment register changes. Interested "
     "parties include the customer whose overlay requirements this standard carries, the "
     "site maintenance organisation, and the regulatory authorities for the site. Where a "
     "customer-specific requirement conflicts with a base clause of this standard, the "
     "customer-specific requirement prevails and the conflict shall be recorded in the "
     "compliance mapping table maintained by the quality department."),
    ("7.1.5", "Measurement traceability and calibration", "control_valve",
     "All instruments used to control or verify product characteristics, including control "
     "valve positioners and their calibration equipment, shall carry current calibration "
     "status traceable to the site standard. An instrument found with expired calibration or "
     "an expired inspection record shall be treated as suspect: product controlled by it "
     "since the last valid record shall be evaluated for conformity, and the instrument "
     "shall not be used for acceptance decisions until calibration is restored. Stroke "
     "testing per SOP-108 constitutes the calibration record for control valves."),
    ("7.2", "Competence and knowledge retention", None,
     "The plant shall retain critical operational knowledge when experienced staff leave or "
     "retire. Undocumented practices that operators rely on shall be captured, reviewed "
     "against the written procedure, and either incorporated into the procedure or "
     "corrected. Where captured operator practice diverges from an approved procedure, the "
     "divergence shall be treated as a nonconformity of the documentation system and "
     "resolved through clause 10.2. Knowledge capture may use any recorded medium, "
     "including transcribed and translated spoken accounts from retiring operators; a "
     "captured claim is unverified experience until reviewed, and shall be stored "
     "separately from approved procedures so the two can never be confused at the point "
     "of use."),
    ("8.1", "Operational planning and control", None,
     "Production processes shall be planned and executed under controlled conditions, "
     "including approved procedures at the point of use, equipment maintained per the "
     "preventive schedule, and process parameters within their specified limits. Planned "
     "preventive maintenance intervals form part of controlled conditions; missed or "
     "deferred intervals on quality-critical equipment shall be recorded and assessed for "
     "product risk. Changes to operating conditions that could affect conformity, "
     "including seasonal changes to raw water quality and airborne debris load, shall be "
     "reviewed for their effect on planned intervals before the season begins, not after "
     "defects appear."),
    ("8.5.1", "Control of production equipment condition", "centrifugal_pump",
     "Production shall be carried out with equipment whose condition cannot degrade product "
     "conformity. For fluid transfer equipment, suction strainer condition and seal "
     "integrity are product-quality controls, not only maintenance concerns: a plugged "
     "strainer or passing seal can introduce contamination or pressure instability into the "
     "product stream. Cleaning and inspection intervals for such equipment shall reflect "
     "actual operating conditions, including seasonal debris load, and shall be reviewed "
     "when defect rates rise. Deviations from the published interval shall be recorded as "
     "nonconformities against this clause."),
    ("8.7", "Control of nonconforming output", None,
     "Product that does not conform to requirements shall be identified, segregated and "
     "dispositioned before release. Every nonconformity shall be recorded in the NCR "
     "register with the equipment or process implicated, the clause of this standard "
     "affected, and the disposition. Recurring nonconformities from the same equipment "
     "or cause shall escalate to root cause analysis under clause 10.2. Dispositions are "
     "limited to rework, reprocess, accept under concession with customer approval, or "
     "scrap; release of nonconforming product without a recorded disposition is a "
     "reportable quality system failure."),
    ("9.1", "Process performance monitoring", None,
     "Key quality indicators shall be computed monthly for each registered production "
     "process: process capability (Cpk) against specified limits and defect rate in parts "
     "per million (PPM). Indicators shall be computed from measured data held in the "
     "structured quality store; computed values, not narrative estimates, are the basis "
     "for decisions. A process with Cpk below 1.33 is not capable and shall not run "
     "unattended; a PPM value rising for three consecutive months triggers investigation "
     "regardless of absolute level. Indicator thresholds are defined per industry overlay "
     "in the standards pack configuration: parts per million defect rate for the "
     "automotive overlay carried by this site, with batch yield and lot traceability "
     "defined for other overlays. Computed indicators shall be traceable to the exact "
     "query and dataset used to produce them."),
    ("9.2", "Internal audit", None,
     "The quality system shall be audited internally at planned intervals. Audit findings "
     "shall reference the specific clause of this standard, the objective evidence "
     "observed, and the equipment or process concerned. Findings remain open until "
     "corrective action is verified effective by follow-up evidence, not by assertion."),
    ("10.2", "Nonconformity and corrective action", None,
     "For every nonconformity, the plant shall determine root cause before closing the "
     "record. Correction without root cause — repairing the same failure repeatedly, or "
     "re-aligning the same machine each quarter — does not satisfy this clause. Corrective "
     "action shall address the system that allowed the nonconformity: the procedure, the "
     "interval, the training, or the equipment condition, and its effectiveness shall be "
     "verified against subsequent performance indicators. Where operator practice has "
     "diverged from an approved procedure and the practice is found technically sound, "
     "the corrective action is a controlled revision of the procedure, not retraining of "
     "the operators to a written interval that field conditions contradict."),
]

# --------------------------------------------------------------------- processes / KPIs
# process -> (equipment, spec description)
PROCESSES = [
    ("PRC-101", "P-101A", "Feed transfer to Process Area"),
    ("PRC-201", "HX-201A", "Feed preheat duty"),
    ("PRC-301", "CV-301A", "Feed flow control"),
]

def month_str(offset_back):
    """YYYY-MM for N months before the demo month."""
    y, m = DEMO_DATE.year, DEMO_DATE.month
    m -= offset_back
    while m <= 0:
        m += 12
        y -= 1
    return f"{y}-{m:02d}"


def build_kpis():
    rows = []  # process_id, equipment_tag, metric, period, value

    # PRC-101 PPM: stable ~180, then monsoon rise 240 -> 310 -> 420 (Q2 pattern)
    ppm = [180, 175, 190, 168, 185, 172, 178, 182, 165, 240, 310, 420]
    # PRC-101 Cpk stays capable
    cpk_101 = [round(rng.uniform(1.48, 1.62), 2) for _ in range(12)]

    # PRC-301 Cpk: capable ~1.55 then drift 1.41 -> 1.34 -> 1.21 (Q1 pattern)
    cpk_301 = [1.58, 1.55, 1.57, 1.52, 1.54, 1.50, 1.49, 1.47, 1.44, 1.41, 1.34, 1.21]
    # non-pattern PPM series are hand-set so no 3-consecutive rise can occur by
    # chance and fire a false ppm_trend alert (it did, once, from rng)
    ppm_301 = [118, 96, 131, 104, 122, 99, 137, 112, 126, 101, 133, 108]

    # PRC-201 control case: everything stable
    cpk_201 = [round(rng.uniform(1.60, 1.75), 2) for _ in range(12)]
    ppm_201 = [55, 70, 48, 66, 52, 71, 47, 63, 58, 72, 50, 61]

    series = {
        "PRC-101": {"PPM": ppm, "CPK": cpk_101},
        "PRC-201": {"PPM": ppm_201, "CPK": cpk_201},
        "PRC-301": {"PPM": ppm_301, "CPK": cpk_301},
    }
    for pid, tag, desc in PROCESSES:
        for metric, values in series[pid].items():
            for i, v in enumerate(values):            # i=0 oldest .. 11 latest
                rows.append([pid, tag, desc, metric, month_str(11 - i), v])
    return rows


def build_ncrs():
    def d(days):
        return (DEMO_DATE.toordinal() - days)
    def iso(days):
        return date.fromordinal(d(days)).isoformat()
    return [
        ["NCR-001", iso(18), "P-101A", "8.5.1",
         "Product contamination event traced to strainer debris carry-over during monsoon "
         "operation; strainer cleaning interval under review against seasonal load.", "open"],
        ["NCR-002", iso(35), "CV-301A", "7.1.5",
         "Flow control valve stroke-test record expired; measurement traceability broken "
         "for acceptance decisions on feed flow. Recalibration scheduled.", "open"],
        ["NCR-003", iso(160), "P-102A", "10.2",
         "Repeat vibration corrective work without root cause determination; fourth "
         "occurrence in twelve months escalated for RCA.", "open"],
        ["NCR-004", iso(240), "HX-201B", "8.7",
         "Off-spec product temperature during exchanger fouling; batch segregated and "
         "reprocessed. Closed after cleaning per SOP-105.", "closed"],
        ["NCR-005", iso(320), "P-101B", "8.1",
         "Preventive maintenance interval missed during outage congestion; risk assessment "
         "completed, no product impact found.", "closed"],
        ["NCR-006", iso(400), "CV-303A", "9.1",
         "Monthly KPI computation gap for utilities makeup process; reporting restored.",
         "closed"],
    ]


# --------------------------------------------------------------------- renderers
def render_standard_pdf(outpath):
    styles = getSampleStyleSheet()
    h = ParagraphStyle("ClauseHead", parent=styles["Heading2"], spaceBefore=12,
                       spaceAfter=4)
    body = ParagraphStyle("ClauseBody", parent=styles["Normal"], fontSize=10.5,
                          leading=15, spaceAfter=8)
    doc = SimpleDocTemplate(str(outpath), pagesize=A4,
                            leftMargin=2 * cm, rightMargin=2 * cm,
                            topMargin=2 * cm, bottomMargin=2 * cm,
                            title=f"{STANDARD['std_id']} {STANDARD['title']}")
    story = [
        Paragraph(f"{STANDARD['std_id']} — {STANDARD['title']}", styles["Title"]),
        Paragraph(f"{STANDARD['revision']} · Issued {STANDARD['rev_date']} · "
                  f"{STANDARD['overlay']}", styles["Italic"]),
        Spacer(1, 10),
    ]
    words = 0
    for num, title, _applies, text in CLAUSES:
        story.append(Paragraph(f"{num} {title}", h))
        story.append(Paragraph(text, body))
        words += len(text.split())
    doc.build(story)
    return words


def write_xlsx(path, header, rows):
    wb = Workbook()
    ws = wb.active
    ws.append(header)
    for r in rows:
        ws.append(r)
    for col in ws.columns:
        width = max(len(str(c.value or "")) for c in col) + 2
        ws.column_dimensions[col[0].column_letter].width = min(width, 90)
    wb.save(path)


# --------------------------------------------------------------------- main
def main():
    (CORPUS / "qms").mkdir(parents=True, exist_ok=True)
    words = render_standard_pdf(CORPUS / "qms" / "QS-001.pdf")

    kpis = build_kpis()
    write_xlsx(CORPUS / "quality_kpis.xlsx",
               ["process_id", "equipment_tag", "process_desc", "metric", "period",
                "value"], kpis)

    ncrs = build_ncrs()
    write_xlsx(CORPUS / "ncr_register.xlsx",
               ["ncr_id", "date", "equipment_tag", "clause_id", "description",
                "status"], ncrs)

    # ---- verification ----
    fails = []
    prc301_cpk = [r[5] for r in kpis if r[0] == "PRC-301" and r[3] == "CPK"]
    if not (prc301_cpk[-1] < 1.33 <= prc301_cpk[-3]):
        fails.append(f"Q1: PRC-301 Cpk drift wrong: {prc301_cpk[-3:]}")
    prc101_ppm = [r[5] for r in kpis if r[0] == "PRC-101" and r[3] == "PPM"]
    if not (prc101_ppm[-1] > prc101_ppm[-2] > prc101_ppm[-3] > max(prc101_ppm[:-3])):
        fails.append(f"Q2: PRC-101 PPM rise wrong: {prc101_ppm[-4:]}")
    clause_ids = {c[0] for c in CLAUSES}
    if not all(n[3] in clause_ids for n in ncrs):
        fails.append("NCR cites unknown clause")
    for pid in ("PRC-201", "PRC-301"):        # control series must never trigger
        ser = [r[5] for r in kpis if r[0] == pid and r[3] == "PPM"]
        if any(ser[i] < ser[i + 1] < ser[i + 2] for i in range(len(ser) - 2)):
            fails.append(f"{pid} PPM has an accidental 3-month rise: {ser}")
    if not 800 <= words <= 1400:
        fails.append(f"standard word count {words} outside 800-1400")

    print(f"QS-001.pdf: {len(CLAUSES)} clauses, {words} words")
    print(f"quality_kpis.xlsx: {len(kpis)} rows "
          f"({len(PROCESSES)} processes x 2 metrics x 12 months)")
    print(f"ncr_register.xlsx: {len(ncrs)} NCRs")
    print(f"Q1 capability drift: PRC-301 Cpk last 3 = {prc301_cpk[-3:]}")
    print(f"Q2 PPM rise       : PRC-101 PPM last 4 = {prc101_ppm[-4:]}")
    if fails:
        print("\nVERIFICATION FAILURES:")
        for f in fails:
            print(" -", f)
        sys.exit(1)
    print("\nAll QMS verification checks passed.")


if __name__ == "__main__":
    main()
