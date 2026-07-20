"""Central configuration for Plant Brain. One place for every locked decision."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / "corpus"

# --- Neo4j -------------------------------------------------------------------
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "plantbrain"
NEO4J_DATABASE = "neo4j"

# --- Ollama ------------------------------------------------------------------
OLLAMA_BASE_URL = "http://localhost:11434"
LLM_MODEL = "qwen2.5:7b-instruct"     # primary (spec) — benchmark vs fallback on 6 GB GPU
LLM_MODEL_FALLBACK = "qwen3:4b"       # fits fully on GPU
EMBED_MODEL = "nomic-embed-text"
EMBED_DIM = 768                        # LOCKED (spec 4) — changing this forces full re-ingest

# --- Watch agent thresholds (spec 8, P4) -------------------------------------
RISK_RATIO_THRESHOLD = 0.8            # days_since_last / mtbf above this -> overdue alert
CHRONIC_COUNT = 3                     # same mode >= 3 times in window -> chronic flag
CHRONIC_WINDOW_DAYS = 365

# --- Chunking (spec 8, P1) ---------------------------------------------------
CHUNK_TARGET_TOKENS = 600
CHUNK_OVERLAP = 0.15

# --- QMS standards pack (industry-agnostic swap point) -----------------------
# Swap this pack per industry: the graph schema and agent logic stay identical,
# only the ingested standard and the KPI definitions change.
STANDARDS_PACK = {
    "std_id": "QS-001",
    "overlay": "automotive customer overlay (IATF 16949 aligned)",
    "kpi_defs": {
        "CPK": {"label": "process capability (Cpk)", "min": 1.33,
                "rule": "below min is not capable"},
        "PPM": {"label": "defect rate (PPM)", "rising_months": 3,
                "rule": "rising for N consecutive months triggers investigation"},
    },
}
