"""Mission 07 offline regression. Run: python tests/test_mission07_orchestration.py"""
import importlib.util
import sys
from pathlib import Path
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
M07 = ROOT / "lab" / "mission-07"
sys.path.insert(0, str(M07))
from orchestrator import Orchestrator, choose_specialist, make_offline_orchestrator

def test_routing():
    assert choose_specialist("What is the remote work policy?").specialist == "policy"
    assert choose_specialist("Debug FastAPI code error").specialist == "engineering"
    assert choose_specialist("hello").specialist == "clarifier"
    assert choose_specialist("remote policy and FastAPI error").specialist == "clarifier"

def test_isolation_and_bounded_handoff():
    seen = []
    def specialist(q):
        seen.append(q)
        return "Handled"
    engine = Orchestrator({k: specialist for k in ("policy", "engineering", "clarifier")})
    alice = engine.run("remote policy", "alice", "a-1")
    bob = engine.run("FastAPI error", "bob", "b-1")
    assert alice["user_id"] == "alice" and bob["user_id"] == "bob"
    assert alice["request_id"] != bob["request_id"]
    assert alice["handoff_count"] == bob["handoff_count"] == 1
    assert alice["verified"] is False
    assert seen == ["remote policy", "FastAPI error"]
    assert "alice" not in seen[1]

def test_api():
    spec = importlib.util.spec_from_file_location("m07_service", M07 / "service.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    client = TestClient(module.create_app(make_offline_orchestrator()))
    assert client.get("/health").json()["mode"] == "offline"
    payload = {"user_id": "alice", "request_id": "r-1", "question": "remote work policy"}
    assert client.post("/orchestrate", json=payload).json()["specialist"] == "policy"
    assert client.post("/orchestrate", json={**payload, "question": ""}).status_code == 422
    assert client.post("/orchestrate", json={**payload, "user_id": ""}).status_code == 422
    failing = Orchestrator({k: lambda q: (_ for _ in ()).throw(RuntimeError("secret"))
                            for k in ("policy", "engineering", "clarifier")})
    assert client.post("/orchestrate", json=payload).status_code == 200
    broken = TestClient(module.create_app(failing)).post("/orchestrate", json=payload)
    assert broken.status_code == 502 and broken.json()["detail"] == "Specialist execution failed"


# TEST 4: BUG-006 Alternating User Isolation
def test_alternating_user_isolation():
    received = []

    def policy_handler(question):
        received.append(question)
        return "Policy request received"

    engine = Orchestrator({
        "policy": policy_handler,
        "engineering": lambda q: "Engineering response",
        "clarifier": lambda q: "Clarification needed"
    })

    requests = [
        ("alice", "a-1", "remote policy"),
        ("bob", "b-1", "leave policy"),
        ("alice", "a-2", "expense reimbursement policy")
    ]

    for user_id, request_id, question in requests:
        result = engine.run(question, user_id, request_id)

        # Verify user isolation
        assert result["user_id"] == user_id

        # Verify request isolation
        assert result["request_id"] == request_id

        # Verify specialist routing
        assert result["specialist"] == "policy"

        # Verify bounded handoff
        assert result["handoff_count"] == 1

        # Verify answer validation status
        assert result["verified"] is False

    # Verify each request reached the handler correctly
    assert received == [
        "remote policy",
        "leave policy",
        "expense reimbursement policy"
    ]

    print("PASS: BUG-006 alternating user isolation")


if __name__ == "__main__":
    test_routing()
    test_isolation_and_bounded_handoff()
    test_api()
    test_alternating_user_isolation()

    print("PASS: routing, bounded handoffs, isolation, validation and error boundary")