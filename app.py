"""Plant Brain — FastAPI backend + responsive web UI (spec 5, 8, 9).

Run:  py app.py          (serves http://localhost:8000)

Endpoints:
  POST /api/ask            {question} -> cited answer, confidence, citations, timing
  GET  /api/alerts         open alerts with evidence chains (Watch agent output)
  POST /api/watch/run      trigger a Watch sweep now
  GET  /api/stats          graph counts + entity-resolution panel data
  GET  /api/doc/{doc_id}   procedure PDF (citation click-through, #page= anchor)
  GET  /api/audio/{name}   voice clip (seek-to-timestamp playback)

The Watch agent runs on an APScheduler timer (spec 5); narratives are only
generated for alerts that don't have one yet, so sweeps stay cheap.
"""

import json
import sys
import threading
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "pipeline"))
from config import (NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, NEO4J_DATABASE,  # noqa: E402
                    CORPUS)
from neo4j import GraphDatabase                                             # noqa: E402
import ask as ask_mod                                                       # noqa: E402
import watch as watch_mod                                                   # noqa: E402

scheduler = BackgroundScheduler()


@asynccontextmanager
async def lifespan(_app):
    threading.Thread(target=_prewarm_safe, daemon=True).start()
    scheduler.add_job(lambda: watch_mod.sweep(write=True, with_narrative=True),
                      "interval", minutes=30, id="watch")
    scheduler.start()
    yield
    scheduler.shutdown(wait=False)


def _prewarm_safe():
    try:
        ask_mod.prewarm()
        print("prewarm: models loaded, register cached")
    except Exception as e:
        print(f"prewarm failed (will warm on first question): {e}")


app = FastAPI(title="Plant Brain", lifespan=lifespan)
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD),
                              notifications_min_severity="OFF")


class Question(BaseModel):
    question: str


@app.post("/api/ask")
def api_ask(q: Question):
    return ask_mod.ask(q.question)


@app.post("/api/ask/stream")
def api_ask_stream(q: Question):
    def gen():
        for event in ask_mod.ask_stream(q.question):
            yield f"data: {json.dumps(event)}\n\n"
    return StreamingResponse(gen(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache",
                                      "X-Accel-Buffering": "no"})


@app.get("/api/alerts")
def api_alerts():
    with driver.session(database=NEO4J_DATABASE) as s:
        rows = s.run("""
            MATCH (al:Alert)
            OPTIONAL MATCH (al)-[:ABOUT]->(e:Equipment)
            RETURN al.alert_id AS alert_id, al.kind AS kind, al.severity AS severity,
                   al.narrative AS narrative, al.detail AS detail,
                   al.avoidable_hrs AS avoidable_hrs,
                   toString(al.created_at) AS created_at,
                   collect(e.tag) AS tags
            ORDER BY CASE al.severity WHEN 'high' THEN 0 ELSE 1 END, al.kind
        """).data()
    for r in rows:
        r["detail"] = json.loads(r["detail"]) if r["detail"] else {}
    return rows


@app.post("/api/watch/run")
def api_watch_run():
    alerts = watch_mod.sweep(write=True, with_narrative=True)
    return {"alerts_found": len(alerts)}


def _name(v):
    """Cypher expression for a node's best display label."""
    return (f"coalesce({v}.tag,{v}.code,{v}.clause_id,{v}.ncr_id,{v}.alert_id,"
            f"{v}.process_id,{v}.sop_id,{v}.wo_id,{v}.record_id,{v}.name,"
            f"{v}.std_id,{v}.claim_id,{v}.chunk_id,elementId({v}))")


def _graph_from_queries(session, queries, params=None):
    """Run (a)-[r]->(b)-returning queries, merge into unique nodes + links."""
    ret = (f" RETURN elementId(a) AS sid, labels(a)[0] AS sg, {_name('a')} AS sn,"
           f" elementId(b) AS tid, labels(b)[0] AS tg, {_name('b')} AS tn,"
           " type(r) AS rt")
    nodes, links, seen = {}, [], set()
    for q in queries:
        for row in session.run(q + ret, **(params or {})):
            for pfx in ("s", "t"):
                nid = row[f"{pfx}id"]
                nodes.setdefault(nid, {"id": nid, "name": row[f"{pfx}n"],
                                       "group": row[f"{pfx}g"]})
            key = (row["sid"], row["tid"], row["rt"])
            if key not in seen:
                seen.add(key)
                links.append({"source": row["sid"], "target": row["tid"],
                              "type": row["rt"]})
    return {"nodes": list(nodes.values()), "links": links}


OVERVIEW_QUERIES = [
    "MATCH (a:Site)-[r:CONTAINS]->(b:Area)",
    "MATCH (a:Area)-[r:CONTAINS]->(b:Equipment)",
    "MATCH (a:Equipment)<-[:PERFORMED_ON]-(:WorkOrder)-[r:RESULTED_IN]->(b:FailureMode)",
    "MATCH (a:Standard)-[r:HAS_CLAUSE]->(b:Clause)",
    "MATCH (a:Clause)-[r:APPLIES_TO]->(b:Equipment)",
    "MATCH (a:Process)-[r:USES]->(b:Equipment)",
    "MATCH (a:NCR)-[r:AGAINST]->(b:Equipment)",
    "MATCH (a:NCR)-[r:CITES]->(b:Clause)",
    "MATCH (a:Alert)-[r:ABOUT]->(b:Equipment)",
]

FOCUS_QUERIES = [
    "MATCH (a:Site)-[r:CONTAINS]->(b:Area)-[:CONTAINS]->(:Equipment {tag:$tag})",
    "MATCH (a:Area)-[r:CONTAINS]->(b:Equipment {tag:$tag})",
    "MATCH (a:WorkOrder)-[r:PERFORMED_ON]->(b:Equipment {tag:$tag})",
    "MATCH (a:WorkOrder)-[r:RESULTED_IN]->(b:FailureMode) "
    "WHERE (a)-[:PERFORMED_ON]->(:Equipment {tag:$tag})",
    "MATCH (t:Equipment {tag:$tag}) MATCH (a:Area)-[r:CONTAINS]->(b:Equipment) "
    "WHERE b.iso14224_class = t.iso14224_class AND b.tag <> $tag",
    "MATCH (a:Procedure)-[r:APPLIES_TO]->(b:Equipment {tag:$tag})",
    "MATCH (a:Clause)-[r:APPLIES_TO]->(b:Equipment {tag:$tag})",
    "MATCH (a:TacitKnowledge)-[r:APPLIES_TO]->(b:Equipment {tag:$tag})",
    "MATCH (a:InspectionRecord)-[r:ON]->(b:Equipment {tag:$tag})",
    "MATCH (a:NCR)-[r:AGAINST]->(b:Equipment {tag:$tag})",
    "MATCH (a:NCR)-[r:CITES]->(b:Clause) "
    "WHERE (a)-[:AGAINST]->(:Equipment {tag:$tag})",
    "MATCH (a:Alert)-[r:ABOUT]->(b:Equipment {tag:$tag})",
]


@app.get("/api/graph")
def api_graph(focus: str = ""):
    with driver.session(database=NEO4J_DATABASE) as s:
        if focus:
            g = _graph_from_queries(s, FOCUS_QUERIES, {"tag": focus})
        else:
            g = _graph_from_queries(s, OVERVIEW_QUERIES)
        equipment = [r["tag"] for r in s.run(
            "MATCH (a:Area)-[:CONTAINS]->(e:Equipment) RETURN e.tag AS tag "
            "ORDER BY e.tag")]
    g["equipment"] = equipment
    g["focus"] = focus
    return g


@app.get("/graph", response_class=HTMLResponse)
def graph_page():
    return (ROOT / "static" / "graph.html").read_text(encoding="utf-8")


@app.get("/api/stats")
def api_stats():
    with driver.session(database=NEO4J_DATABASE) as s:
        counts = {r["label"]: r["n"] for r in s.run(
            "MATCH (n) WITH labels(n)[0] AS label, count(*) AS n RETURN label, n")}
        resolution = s.run("""
            MATCH (e:Equipment) WHERE size(e.aliases) > 1
            RETURN e.tag AS tag, e.aliases AS aliases ORDER BY size(e.aliases) DESC
        """).data()
        langs = [r["l"] for r in s.run(
            "MATCH (t:TacitKnowledge) RETURN DISTINCT t.lang AS l")]
    return {"counts": counts, "entity_resolution": resolution,
            "tacit_languages": langs}


@app.get("/api/doc/{doc_id}")
def api_doc(doc_id: str):
    name = Path(doc_id).name
    for folder in ("procedures", "qms"):
        path = CORPUS / folder / f"{name}.pdf"
        if path.exists():
            return FileResponse(path, media_type="application/pdf")
    raise HTTPException(404)


@app.get("/api/audio/{name}")
def api_audio(name: str):
    path = CORPUS / "audio" / Path(name).name
    if not path.exists():
        raise HTTPException(404)
    return FileResponse(path)


@app.get("/", response_class=HTMLResponse)
def index():
    return (ROOT / "static" / "index.html").read_text(encoding="utf-8")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
