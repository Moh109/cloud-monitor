"""Core data models shared across collectors, checks, and reporters."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class Severity(str, Enum):
    """Finding severity, ordered from most to least serious.

    The ``weight`` is used by the scoring engine so that a failing CRITICAL
    control drags the posture score down far more than a failing LOW control.
    """

    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFORMATIONAL = "INFORMATIONAL"

    @property
    def weight(self) -> int:
        return {
            "CRITICAL": 40,
            "HIGH": 20,
            "MEDIUM": 10,
            "LOW": 3,
            "INFORMATIONAL": 1,
        }[self.value]

    @property
    def rank(self) -> int:
        """Lower number == more severe. Handy for sorting and thresholds."""
        return {
            "CRITICAL": 0,
            "HIGH": 1,
            "MEDIUM": 2,
            "LOW": 3,
            "INFORMATIONAL": 4,
        }[self.value]


class Status(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    ERROR = "ERROR"  # the check itself raised - surfaced so bugs are visible


@dataclass
class Resource:
    """A normalized cloud resource collected from a provider API.

    ``raw`` holds the provider-specific payload (e.g. the boto3 response) that
    checks inspect. Keeping the raw dict avoids leaking provider details into
    the check interface while still giving checks everything they need.
    """

    resource_id: str
    resource_type: str  # e.g. "aws_s3_bucket"
    region: str
    name: str = ""
    raw: dict = field(default_factory=dict)


@dataclass
class Finding:
    """The result of evaluating one check against one resource."""

    check_id: str
    title: str
    service: str
    severity: Severity
    status: Status
    resource_id: str
    resource_type: str
    region: str
    description: str
    remediation: str
    frameworks: dict = field(default_factory=dict)
    evidence: str = ""
    timestamp: str = field(default_factory=_utcnow_iso)

    def to_dict(self) -> dict:
        data = asdict(self)
        data["severity"] = self.severity.value
        data["status"] = self.status.value
        return data


@dataclass
class ScanResult:
    """The full output of a scan: findings plus run metadata."""

    findings: list[Finding] = field(default_factory=list)
    account_id: str = ""
    provider: str = "aws"
    regions: list[str] = field(default_factory=list)
    started_at: str = field(default_factory=_utcnow_iso)
    finished_at: str = ""

    @property
    def failed(self) -> list[Finding]:
        return [f for f in self.findings if f.status == Status.FAIL]

    @property
    def passed(self) -> list[Finding]:
        return [f for f in self.findings if f.status == Status.PASS]

    @property
    def errored(self) -> list[Finding]:
        return [f for f in self.findings if f.status == Status.ERROR]

    def failed_by_severity(self, severity: Severity) -> list[Finding]:
        return [f for f in self.failed if f.severity == severity]

    def has_failure_at_or_above(self, severity: Severity) -> bool:
        return any(f.severity.rank <= severity.rank for f in self.failed)
