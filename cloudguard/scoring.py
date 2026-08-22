"""Posture scoring.

The score is a severity-weighted pass rate: passing a CRITICAL control is worth
far more than passing a LOW one, and failing a CRITICAL control hurts far more.
This mirrors how real CSPM products summarize an account's health in a single,
resume-friendly number.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .models import ScanResult, Severity, Status


@dataclass
class PostureScore:
    score: int  # 0-100
    grade: str  # A-F
    total_controls: int
    passed_controls: int
    failed_controls: int
    errored_controls: int
    failed_by_severity: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "score": self.score,
            "grade": self.grade,
            "total_controls": self.total_controls,
            "passed_controls": self.passed_controls,
            "failed_controls": self.failed_controls,
            "errored_controls": self.errored_controls,
            "failed_by_severity": self.failed_by_severity,
        }


def _grade(score: int) -> str:
    if score >= 90:
        return "A"
    if score >= 80:
        return "B"
    if score >= 70:
        return "C"
    if score >= 60:
        return "D"
    return "F"


def compute_score(result: ScanResult) -> PostureScore:
    scored = [f for f in result.findings if f.status in (Status.PASS, Status.FAIL)]
    total_weight = sum(f.severity.weight for f in scored)
    passed_weight = sum(
        f.severity.weight for f in scored if f.status == Status.PASS
    )

    score = round(100 * passed_weight / total_weight) if total_weight else 100

    failed_by_severity = {
        sev.value: len(result.failed_by_severity(sev)) for sev in Severity
    }

    return PostureScore(
        score=score,
        grade=_grade(score),
        total_controls=len(scored),
        passed_controls=len(result.passed),
        failed_controls=len(result.failed),
        errored_controls=len(result.errored),
        failed_by_severity=failed_by_severity,
    )
