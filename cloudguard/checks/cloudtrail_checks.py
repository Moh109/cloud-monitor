"""CloudTrail checks: audit logging must exist, be complete, and be trustworthy."""

from __future__ import annotations

from ..models import Resource, Severity
from .base import Check, register


@register
class CloudTrailEnabled(Check):
    check_id = "CT.1"
    title = "CloudTrail logging should be enabled"
    service = "cloudtrail"
    resource_type = "aws_cloudtrail_trail"
    severity = Severity.HIGH
    description = (
        "Without CloudTrail, API activity is not recorded, leaving no audit "
        "trail for detection or incident response."
    )
    remediation = "Create a trail and start logging via `aws cloudtrail start-logging`."
    frameworks = {"CIS AWS 3.0": "3.1", "MITRE ATT&CK": "T1562.008", "NIST 800-53": "AU-2"}

    def evaluate(self, resource: Resource) -> bool:
        return bool(resource.raw.get("Status", {}).get("IsLogging"))

    def evidence(self, resource: Resource) -> str:
        if resource.raw.get("__absent__"):
            return "No CloudTrail trail is configured in this account/region."
        return "Trail exists but logging is stopped (IsLogging=false)."


@register
class CloudTrailMultiRegion(Check):
    check_id = "CT.2"
    title = "CloudTrail should be multi-region"
    service = "cloudtrail"
    resource_type = "aws_cloudtrail_trail"
    severity = Severity.MEDIUM
    description = (
        "A multi-region trail captures activity in every region, including ones "
        "an attacker might use precisely because they are unmonitored."
    )
    remediation = "Enable IsMultiRegionTrail on the trail."
    frameworks = {"CIS AWS 3.0": "3.1", "NIST 800-53": "AU-2"}

    def evaluate(self, resource: Resource) -> bool:
        return bool(resource.raw.get("IsMultiRegionTrail"))


@register
class CloudTrailLogValidation(Check):
    check_id = "CT.3"
    title = "CloudTrail log file validation should be enabled"
    service = "cloudtrail"
    resource_type = "aws_cloudtrail_trail"
    severity = Severity.MEDIUM
    description = (
        "Log file validation produces a tamper-evident digest so you can prove "
        "logs were not altered or deleted after the fact."
    )
    remediation = "Enable log file validation on the trail (EnableLogFileValidation)."
    frameworks = {"CIS AWS 3.0": "3.2", "MITRE ATT&CK": "T1070", "NIST 800-53": "AU-9"}

    def evaluate(self, resource: Resource) -> bool:
        return bool(resource.raw.get("LogFileValidationEnabled"))


@register
class CloudTrailKmsEncryption(Check):
    check_id = "CT.4"
    title = "CloudTrail logs should be encrypted with a KMS key"
    service = "cloudtrail"
    resource_type = "aws_cloudtrail_trail"
    severity = Severity.LOW
    description = (
        "Encrypting trail logs with a customer-managed KMS key protects their "
        "confidentiality and adds an access-control boundary around them."
    )
    remediation = "Set a KmsKeyId on the trail to enable SSE-KMS on delivered logs."
    frameworks = {"CIS AWS 3.0": "3.5", "NIST 800-53": "SC-28"}

    def evaluate(self, resource: Resource) -> bool:
        return bool(resource.raw.get("KmsKeyId"))
