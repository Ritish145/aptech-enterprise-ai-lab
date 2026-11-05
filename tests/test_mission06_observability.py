"""Offline Mission 06 tests. Run from root: python tests/test_mission06_observability.py"""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "lab" / "mission-06"))
from observability import TraceRecorder
from evaluation import EvalCase, evaluate_case, evaluate_dataset
from run_evaluation import run

def test_traces():
    recorder = TraceRecorder()
    trace = recorder.new_trace_id()
    assert recorder.run_stage(trace, "retrieval", lambda: 3) == 3
    try:
        recorder.run_stage(trace, "model", lambda: 1 / 0)
        raise AssertionError("expected failure")
    except ZeroDivisionError:
        pass
    assert recorder.summary()["events"] == 2
    assert recorder.summary()["errors"] == 1
    assert recorder.export()[1]["error_type"] == "ZeroDivisionError"
    assert all("prompt" not in event for event in recorder.export())

def test_false_success():
    case = EvalCase("remote work policy", "REMOTE-2026", "three days")
    # BUG-005: transport succeeds, but provenance and content are wrong.
    result = evaluate_case(case, "two days", [{"source_id": "REMOTE-2025"}], 200)
    assert result["http_success"] is True
    assert result["passed"] is False
    assert result["answer_support_verified"] is False
    repaired = evaluate_case(case, "three days", [{"source_id": "REMOTE-2026"}], 200)
    assert repaired["passed"] is True
    assert repaired["answer_support_verified"] is False

def test_dataset():
    report = evaluate_dataset([EvalCase("x", None)], lambda q: {"answer": "", "sources": []})
    assert report["pass_rate"] == 1.0
    try:
        evaluate_dataset([], lambda q: {})
        raise AssertionError("empty dataset should fail")
    except ValueError:
        pass
    integration = run()
    assert integration["cases"] == 4
    assert integration["passed"] == 4
    assert integration["trace_summary"]["events"] == 4

if __name__ == "__main__":
    test_traces()
    test_false_success()
    test_dataset()
    print("PASS: tracing, false-success detection, retrieval evaluation")
