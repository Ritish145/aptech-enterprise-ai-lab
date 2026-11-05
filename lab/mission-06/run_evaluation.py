"""Run a deterministic Mission 05 retrieval evaluation offline."""
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
M05 = ROOT / "lab" / "mission-05"
M06 = Path(__file__).resolve().parent
sys.path.insert(0, str(M05))
sys.path.insert(0, str(M06))

from retrieval import load_chunks, retrieve
from evaluation import EvalCase, evaluate_dataset
from observability import TraceRecorder

CASES = [
    EvalCase("remote work days per week", "REMOTE-2026"),
    EvalCase("expense reimbursement deadline", "EXPENSE-2026"),
    EvalCase("unmatchedzzzzzz", None),
    EvalCase("manager approval for remote work", "REMOTE-2026"),
]

def run() -> dict:
    chunks = load_chunks()
    recorder = TraceRecorder()
    def query(question: str) -> dict:
        trace_id = recorder.new_trace_id()
        hits = recorder.run_stage(trace_id, "retrieval",
            lambda: retrieve(question, chunks))
        return {"answer": "Retrieval-only evaluation: no generated answer",
                "sources": [{"source_id": h["source_id"]} for h in hits],
                "http_status": 200}
    report = evaluate_dataset(CASES, query)
    report["trace_summary"] = recorder.summary()
    report["evaluation_scope"] = "retrieval provenance only; no LLM answer support"
    return report

if __name__ == "__main__":
    import json
    print(json.dumps(run(), indent=2))
