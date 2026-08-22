"""Collector for S3 buckets and their security-relevant configuration."""

from __future__ import annotations

from botocore.exceptions import ClientError

from ..models import Resource
from .base import Collector


class S3Collector(Collector):
    service = "s3"
    resource_type = "aws_s3_bucket"
    scope = "global"  # ListBuckets is account-wide

    def collect(self) -> list[Resource]:
        client = self.session.client("s3", region_name=self.region)
        resources: list[Resource] = []

        try:
            buckets = client.list_buckets().get("Buckets", [])
        except ClientError:
            return resources

        for bucket in buckets:
            name = bucket["Name"]
            raw: dict = {"Name": name}

            try:
                loc = client.get_bucket_location(Bucket=name).get("LocationConstraint")
                region = loc or "us-east-1"
            except ClientError:
                region = self.region
            raw["Region"] = region

            # Each of these APIs raises when the feature is not configured;
            # a missing configuration is itself the insecure state, so we
            # normalize the error to None and let the checks decide.
            raw["PublicAccessBlock"] = self._safe(
                client.get_public_access_block,
                key="PublicAccessBlockConfiguration",
                Bucket=name,
            )
            raw["Encryption"] = self._safe(
                client.get_bucket_encryption,
                key="ServerSideEncryptionConfiguration",
                Bucket=name,
            )
            raw["Acl"] = self._safe(client.get_bucket_acl, Bucket=name)
            raw["Policy"] = self._safe(
                client.get_bucket_policy, key="Policy", Bucket=name
            )
            raw["Versioning"] = self._safe(client.get_bucket_versioning, Bucket=name)
            raw["Logging"] = self._safe(client.get_bucket_logging, Bucket=name)

            resources.append(
                Resource(
                    resource_id=name,
                    resource_type=self.resource_type,
                    region=region,
                    name=name,
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
