"""Base class and registry for security posture checks.

A *check* encapsulates one security control. Subclasses declare metadata
(id, severity, framework mappings, remediation) and implement ``evaluate``,
which returns ``True`` when a resource is compliant and ``False`` when it
violates the control. The base class turns that boolean into a normalized
``Finding`` and shields the scan from checks that raise.
"""

from __future__ import annotations

from ..models import Finding, Resource, Severity, Status

# Populated by the @register decorator when check modules are imported.
CHECK_REGISTRY: list[type["Check"]] = []


def register(cls: type["Check"]) -> type["Check"]:
    CHECK_REGISTRY.append(cls)
    return cls


class Check:
    check_id: str = ""
    title: str = ""
    service: str = ""
    resource_type: str = ""
    severity: Severity = Severity.MEDIUM
    description: str = ""
    remediation: str = ""
    frameworks: dict = {}

    def evaluate(self, resource: Resource) -> bool:
        """Return True if the resource is compliant with this control."""
        raise NotImplementedError

    def evidence(self, resource: Resource) -> str:
        """Human-readable proof of the violation, shown on FAIL only."""
        return ""

    def run(self, resource: Resource) -> Finding:
        try:
            compliant = self.evaluate(resource)
            status = Status.PASS if compliant else Status.FAIL
            evidence = "" if compliant else self.evidence(resource)
        except Exception as exc:  # a buggy check must never abort the whole scan
            status = Status.ERROR
            evidence = f"check raised: {exc!r}"

        return Finding(
            check_id=self.check_id,
            title=self.title,
            service=self.service,
            severity=self.severity,
            status=status,
            resource_id=resource.resource_id,
            resource_type=resource.resource_type,
            region=resource.region,
            description=self.description,
            remediation=self.remediation,
            frameworks=dict(self.frameworks),
            evidence=evidence,
        )
