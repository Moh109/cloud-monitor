"""S3 security checks.

Each check maps to one or more industry frameworks so that findings can be
traced back to a recognized control (CIS AWS Foundations Benchmark, MITRE
ATT&CK techniques, NIST 800-53 control families).
"""

from __future__ import annotations

import json

from ..models import Resource, Severity
from .base import Check, register

_PUBLIC_ACL_URIS = {
    "http://acs.amazonaws.com/groups/global/AllUsers",
    "http://acs.amazonaws.com/groups/global/AuthenticatedUsers",
}


def _as_list(value):
    return value if isinstance(value, list) else [value]


@register
class S3BlockPublicAccess(Check):
    check_id = "S3.1"
    title = "S3 buckets should block all public access"
    service = "s3"
    resource_type = "aws_s3_bucket"
    severity = Severity.HIGH
    description = (
        "S3 Block Public Access is a safety net that overrides bucket ACLs and "
        "policies that would otherwise expose data. All four settings should be on."
    )
    remediation = (
        "Enable Block Public Access (BlockPublicAcls, IgnorePublicAcls, "
        "BlockPublicPolicy, RestrictPublicBuckets) at the bucket or, preferably, "
        "the account level via the S3 console or `aws s3api put-public-access-block`."
    )
    frameworks = {"CIS AWS 3.0": "2.1.4", "MITRE ATT&CK": "T1530", "NIST 800-53": "AC-3"}

    def evaluate(self, resource: Resource) -> bool:
        pab = resource.raw.get("PublicAccessBlock")
        if not pab:
            return False
        return all(
            pab.get(flag)
            for flag in (
                "BlockPublicAcls",
                "IgnorePublicAcls",
                "BlockPublicPolicy",
                "RestrictPublicBuckets",
            )
        )

    def evidence(self, resource: Resource) -> str:
        return f"PublicAccessBlock configuration: {resource.raw.get('PublicAccessBlock')}"


@register
class S3EncryptionAtRest(Check):
    check_id = "S3.2"
    title = "S3 buckets should enable server-side encryption at rest"
    service = "s3"
    resource_type = "aws_s3_bucket"
    severity = Severity.HIGH
    description = (
        "Default encryption ensures every object written to the bucket is "
        "encrypted at rest without relying on clients to request it."
    )
    remediation = (
        "Enable default encryption (SSE-S3 or SSE-KMS) on the bucket via "
        "`aws s3api put-bucket-encryption`."
    )
    frameworks = {"CIS AWS 3.0": "2.1.1", "NIST 800-53": "SC-28"}

    def evaluate(self, resource: Resource) -> bool:
        enc = resource.raw.get("Encryption")
        return bool(enc and enc.get("Rules"))


@register
class S3PublicAcl(Check):
    check_id = "S3.3"
    title = "S3 bucket ACLs should not grant access to Everyone/AuthenticatedUsers"
    service = "s3"
    resource_type = "aws_s3_bucket"
    severity = Severity.CRITICAL
    description = (
        "ACL grants to the AllUsers or AuthenticatedUsers groups expose bucket "
        "contents to anyone on the internet or any AWS account."
    )
    remediation = (
        "Remove public ACL grants and prefer bucket policies with explicit "
        "principals; enable Block Public Access as a backstop."
    )
    frameworks = {"CIS AWS 3.0": "2.1.5", "MITRE ATT&CK": "T1530", "NIST 800-53": "AC-3"}

    def evaluate(self, resource: Resource) -> bool:
        acl = resource.raw.get("Acl")
        if not acl:
            return True  # nothing to grant publicly
        for grant in acl.get("Grants", []):
            if grant.get("Grantee", {}).get("URI") in _PUBLIC_ACL_URIS:
                return False
        return True

    def evidence(self, resource: Resource) -> str:
        acl = resource.raw.get("Acl") or {}
        public = [
            g.get("Permission")
            for g in acl.get("Grants", [])
            if g.get("Grantee", {}).get("URI") in _PUBLIC_ACL_URIS
        ]
        return f"Public ACL grants: {public}"


@register
class S3PublicPolicy(Check):
    check_id = "S3.4"
    title = "S3 bucket policies should not allow anonymous (Principal '*') access"
    service = "s3"
    resource_type = "aws_s3_bucket"
    severity = Severity.CRITICAL
    description = (
        "A bucket policy that Allows a wildcard principal without a restricting "
        "condition makes the bucket readable or writable by anyone."
    )
    remediation = (
        "Scope bucket policy statements to specific principals, or add a "
        "restricting Condition (e.g. aws:SourceVpce) and enable Block Public Access."
    )
    frameworks = {"CIS AWS 3.0": "2.1.5", "MITRE ATT&CK": "T1530", "NIST 800-53": "AC-3"}

    def evaluate(self, resource: Resource) -> bool:
        policy = resource.raw.get("Policy")
        if not policy:
            return True
        doc = json.loads(policy) if isinstance(policy, str) else policy
        for stmt in _as_list(doc.get("Statement", [])):
            if stmt.get("Effect") != "Allow":
                continue
            principal = stmt.get("Principal")
            is_wildcard = principal == "*" or (
                isinstance(principal, dict)
                and principal.get("AWS") in ("*", ["*"])
            )
            if is_wildcard and not stmt.get("Condition"):
                return False
        return True

    def evidence(self, resource: Resource) -> str:
        return "Bucket policy Allows a wildcard principal with no restricting Condition."


@register
class S3Versioning(Check):
    check_id = "S3.5"
    title = "S3 buckets should have versioning enabled"
    service = "s3"
    resource_type = "aws_s3_bucket"
    severity = Severity.MEDIUM
    description = (
        "Versioning preserves prior object versions, aiding recovery from "
        "accidental deletion and ransomware that overwrites objects."
    )
    remediation = "Enable versioning via `aws s3api put-bucket-versioning`."
    frameworks = {"CIS AWS 3.0": "2.1.2", "NIST 800-53": "CP-9"}

    def evaluate(self, resource: Resource) -> bool:
        versioning = resource.raw.get("Versioning")
        return bool(versioning and versioning.get("Status") == "Enabled")


@register
class S3AccessLogging(Check):
    check_id = "S3.6"
    title = "S3 buckets should have server access logging enabled"
    service = "s3"
    resource_type = "aws_s3_bucket"
    severity = Severity.LOW
    description = (
        "Access logs record requests made to the bucket, supporting incident "
        "investigation and detection of unauthorized access."
    )
    remediation = "Configure access logging to a dedicated log bucket."
    frameworks = {"CIS AWS 3.0": "2.1.3", "MITRE ATT&CK": "T1530", "NIST 800-53": "AU-2"}

    def evaluate(self, resource: Resource) -> bool:
        logging = resource.raw.get("Logging")
        return bool(logging and logging.get("LoggingEnabled"))
