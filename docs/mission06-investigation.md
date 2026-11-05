# Mission 06: Observability and Evaluation

## 1. Objective

Investigate BUG-005, a simulated false-success scenario in which an AI service returns HTTP 200 despite providing an incorrect answer from an outdated policy.

The objective is to distinguish transport-level success from retrieval quality and answer correctness.

## 2. Investigation Method

**ASK → HYPOTHESIZE → INSPECT → TEST → PROVE → EXPLAIN**

**ASK:** Does HTTP 200 guarantee a correct AI response?

**HYPOTHESIZE:** An API request can succeed even when the retrieved source is outdated or the answer is incorrect.

**INSPECT:** Reviewed `observability.py`, `evaluation.py`, `run_evaluation.py`, and `test_mission06_observability.py`.

**TEST:** Executed the offline regression tests and expanded the evaluation dataset from three cases to four.

**PROVE:** All four evaluation cases passed. The existing BUG-005 regression test correctly distinguished an incorrect response from a corrected one.

**EXPLAIN:** HTTP status measures request success, whereas source and answer checks provide separate quality signals.

## 3. Trace Diagram

```text
Synthetic User Question
         |
         v
Generate Trace ID
         |
         v
TraceRecorder.run_stage()
         |
         v
Mission 05 Retrieval
         |
         v
Retrieved Source IDs
         |
         v
Evaluation Framework
         |
         +-- HTTP Status Check
         |
         +-- Expected Source Check
         |
         +-- Expected Answer Fragment Check
         |
         v
Evaluation Results
         |
         v
Trace Summary
```

The trace recorder captures execution stage, duration, success status, error type, and trace ID. It deliberately excludes prompts, answers, user identities, and retrieved document bodies.

## 4. BUG-005 Failure Analysis

The simulated incorrect response returned:

- HTTP status: 200
- Source: REMOTE-2025
- Answer: Two days
- Evaluation result: Failed

The corrected fixture returned:

- HTTP status: 200
- Source: REMOTE-2026
- Answer: Three days
- Evaluation result: Passed

The regression test demonstrates that HTTP success alone is insufficient to establish answer correctness.

The corrected fixture satisfies the configured evaluation checks but does not establish independent semantic verification of the answer.

## 5. Expanded Evaluation Dataset

Added a fourth evaluation case:

**Question:** Manager approval for remote work

**Expected source:** REMOTE-2026

The expanded dataset contains four cases.

## 6. Test Transcript

Command:

`python lab/mission-06/run_evaluation.py`

Results:

- Total cases: 4
- Passed: 4
- Pass rate: 100%
- Trace events: 4
- Errors: 0
- Average stage duration: 0.084 ms

Regression test command:

`python tests/test_mission06_observability.py`

Result:

`PASS: tracing, false-success detection, retrieval evaluation`

## 7. Engineering Explanation

The evaluation framework separates transport success, source provenance, and expected answer-fragment checks.

This separation helps identify false-success scenarios in which an application returns HTTP 200 but delivers incorrect information.

The `answer_support_verified` field remains false because the current implementation does not perform claim-level verification against source documents.

The implementation uses synthetic data and in-memory tracing. It does not represent production observability, Azure monitoring, or live LLM evaluation.

## 8. Conclusion

Mission 06's offline regression tests passed, and the expanded four-case retrieval evaluation achieved a 100% pass rate.

The investigation demonstrated that transport success and answer quality must be evaluated independently.

A future improvement would be to introduce claim-level grounding verification to assess whether generated answers are actually supported by their retrieved sources.