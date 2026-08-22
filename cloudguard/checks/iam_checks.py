"""IAM security checks: password policy and per-user least-privilege / MFA."""

from __future__ import annotations

from ..models import Resource, Severity
from .base import Check, register


@register
class IAMPasswordPolicyLength(Check):
    check_id = "IAM.1"
    title = "IAM password policy should require a minimum length of 14"
    service = "iam"
    resource_type = "aws_iam_account"
    severity = Severity.MEDIUM
    description = (
        "A strong account password policy resists brute-force and guessing "
        "attacks against console users."
    )
    remediation = (
        "Set a password policy with MinimumPasswordLength >= 14 via "
        "`aws iam update-account-password-policy`."
    )
    frameworks = {"CIS AWS 3.0": "1.8", "NIST 800-53": "IA-5"}

    def evaluate(self, resource: Resource) -> bool:
        policy = resource.raw.get("PasswordPolicy")
        if not policy:
            return False
        return policy.get("MinimumPasswordLength", 0) >= 14

    def evidence(self, resource: Resource) -> str:
        policy = resource.raw.get("PasswordPolicy")
        if not policy:
            return "No account password policy is configured."
        return f"MinimumPasswordLength = {policy.get('MinimumPasswordLength')}"


@register
class IAMUserMFA(Check):
    check_id = "IAM.2"
    title = "IAM users with console access should have MFA enabled"
    service = "iam"
    resource_type = "aws_iam_user"
    severity = Severity.HIGH
    description = (
        "MFA adds a second factor so a leaked password alone cannot grant "
        "console access."
    )
    remediation = "Enable an MFA device for every user that has a login profile."
    frameworks = {"CIS AWS 3.0": "1.10", "MITRE ATT&CK": "T1078", "NIST 800-53": "IA-2"}

    def evaluate(self, resource: Resource) -> bool:
        if not resource.raw.get("HasConsoleAccess"):
            return True  # not applicable to programmatic-only users
        return len(resource.raw.get("MFADevices", [])) > 0

    def evidence(self, resource: Resource) -> str:
        return "User has console access but no MFA device registered."


@register
class IAMDirectAdminPolicy(Check):
    check_id = "IAM.3"
    title = "IAM users should not have AdministratorAccess attached directly"
    service = "iam"
    resource_type = "aws_iam_user"
    severity = Severity.HIGH
    description = (
        "Attaching AdministratorAccess directly to users violates least "
        "privilege and makes a single credential compromise catastrophic. "
        "Grant broad permissions through assumable roles instead."
    )
    remediation = (
        "Detach AdministratorAccess from the user and grant scoped permissions, "
        "using IAM roles for privileged operations."
    )
    frameworks = {"CIS AWS 3.0": "1.16", "MITRE ATT&CK": "T1098", "NIST 800-53": "AC-6"}

    def evaluate(self, resource: Resource) -> bool:
        for policy in resource.raw.get("AttachedPolicies", []):
            arn = policy.get("PolicyArn", "")
            if policy.get("PolicyName") == "AdministratorAccess" or arn.endswith(
                "/AdministratorAccess"
            ):
                return False
        return True

    def evidence(self, resource: Resource) -> str:
        return "AdministratorAccess managed policy is attached directly to this user."


@register
class IAMMultipleAccessKeys(Check):
    check_id = "IAM.4"
    title = "IAM users should not have more than one active access key"
    service = "iam"
    resource_type = "aws_iam_user"
    severity = Severity.MEDIUM
    description = (
        "Multiple active access keys widen the attack surface and complicate "
        "rotation and revocation."
    )
    remediation = "Deactivate and delete unused access keys; keep at most one active key."
    frameworks = {"CIS AWS 3.0": "1.13", "NIST 800-53": "AC-2"}

    def evaluate(self, resource: Resource) -> bool:
        active = [
            k
            for k in resource.raw.get("AccessKeys", [])
            if k.get("Status") == "Active"
        ]
        return len(active) <= 1

    def evidence(self, resource: Resource) -> str:
        active = [
            k.get("AccessKeyId")
            for k in resource.raw.get("AccessKeys", [])
            if k.get("Status") == "Active"
        ]
        return f"Active access keys: {len(active)}"
