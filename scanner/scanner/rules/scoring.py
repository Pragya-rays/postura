"""Present stage's grade/score aggregation. Deliberately simple and tunable —
a flat per-severity point deduction from 100, floored at 0."""
from __future__ import annotations

from scanner.enums import SEVERITY_ORDER, Grade, Severity
from scanner.models import EvaluatedFinding

SEVERITY_WEIGHTS: dict[Severity, int] = {
    Severity.CRITICAL: 40,
    Severity.HIGH: 20,
    Severity.MEDIUM: 10,
    Severity.LOW: 4,
    Severity.INFO: 0,
}

# Checked high-to-low; the first threshold the score clears wins.
GRADE_THRESHOLDS: list[tuple[int, Grade]] = [
    (90, Grade.A),
    (75, Grade.B),
    (60, Grade.C),
    (40, Grade.D),
]


def compute_grade(findings: list[EvaluatedFinding]) -> tuple[Grade, int]:
    score = 100
    for finding in findings:
        score -= SEVERITY_WEIGHTS.get(finding.severity, 0)
    score = max(0, score)

    for threshold, grade in GRADE_THRESHOLDS:
        if score >= threshold:
            return grade, score
    return Grade.F, score


def severity_breakdown(findings: list[EvaluatedFinding]) -> dict[str, int]:
    """Always returns all 5 severity keys, zero-filled — the frontend's
    `Record<Severity, number>` contract expects every key present, never a
    sparse object, so a chart component doesn't have to null-check."""
    counts = {s.value: 0 for s in SEVERITY_ORDER}
    for finding in findings:
        counts[finding.severity.value] += 1
    return counts


def generate_summary(hostname: str, grade: Grade, findings: list[EvaluatedFinding]) -> str:
    """Deterministic one-sentence report overview — NOT an AI call. A
    whole-report summary would need to see every finding at once, which
    doesn't fit "Explain writes copy for the one finding it's handed"; a
    template keeps the "AI only touches individual findings" boundary
    exact rather than blurring it for one UI string."""
    if not findings:
        return f"{hostname} passed every check we ran — no issues found in this scan."

    counts = severity_breakdown(findings)
    headline_parts = [f"{counts[s.value]} {s.value}" for s in SEVERITY_ORDER if counts[s.value]]
    headline = ", ".join(headline_parts)

    top_finding = max(findings, key=lambda f: SEVERITY_WEIGHTS.get(f.severity, 0))
    return f'{hostname} scored a {grade.value} with {headline} finding(s) — start with "{top_finding.title}".'
