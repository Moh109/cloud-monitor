"""Collector for IAM: account password policy and per-user posture."""

from __future__ import annotations

from botocore.exceptions import ClientError

from ..models import Resource
from .base import Collector


class IAMCollector(Collector):
    service = "iam"
    scope = "global"  # IAM is a global service

    def collect(self) -> list[Resource]:
        client = self.session.client("iam")
        resources: list[Resource] = []

        # --- Account-level password policy (one synthetic resource) ---
        try:
            password_policy = client.get_account_password_policy().get("PasswordPolicy")
        except ClientError:
            password_policy = None  # no policy configured == insecure
        resources.append(
            Resource(
                resource_id="account-password-policy",
                resource_type="aws_iam_account",
                region="global",
                name="account-password-policy",
                raw={"PasswordPolicy": password_policy},
            )
        )

        # --- IAM users ---
        try:
            users = client.list_users().get("Users", [])
        except ClientError:
            users = []

        for user in users:
            username = user["UserName"]
            raw: dict = {"User": user}
            raw["AccessKeys"] = self._safe(
                client.list_access_keys, key="AccessKeyMetadata", UserName=username
            ) or []
            raw["MFADevices"] = self._safe(
                client.list_mfa_devices, key="MFADevices", UserName=username
            ) or []
            raw["AttachedPolicies"] = self._safe(
                client.list_attached_user_policies,
                key="AttachedPolicies",
                UserName=username,
            ) or []
            raw["InlinePolicyNames"] = self._safe(
                client.list_user_policies, key="PolicyNames", UserName=username
            ) or []

            try:
                client.get_login_profile(UserName=username)
                raw["HasConsoleAccess"] = True
            except ClientError:
                raw["HasConsoleAccess"] = False

            resources.append(
                Resource(
                    resource_id=username,
                    resource_type="aws_iam_user",
                    region="global",
                    name=username,
                    raw=raw,
                )
            )
        return resources

    @staticmethod
    def _safe(fn, key: str | None = None, **kwargs):
        try:
            resp = fn(**kwargs)
            return resp.get(key) if key else resp
        except ClientError:
            return None
