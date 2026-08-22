"""Collector for CloudTrail audit-logging configuration."""

from __future__ import annotations

from botocore.exceptions import ClientError

from ..models import Resource
from .base import Collector


class CloudTrailCollector(Collector):
    service = "cloudtrail"
    resource_type = "aws_cloudtrail_trail"
    scope = "regional"

    def collect(self) -> list[Resource]:
        client = self.session.client("cloudtrail", region_name=self.region)

        try:
            trails = client.describe_trails().get("trailList", [])
        except ClientError:
            trails = []

        # No trail at all is a serious gap: emit a synthetic resource whose
        # configuration fails every CloudTrail check, so the absence is loud.
        if not trails:
            return [
                Resource(
                    resource_id="NO_CLOUDTRAIL_CONFIGURED",
                    resource_type=self.resource_type,
                    region=self.region,
                    name="none",
                    raw={
                        "IsMultiRegionTrail": False,
                        "LogFileValidationEnabled": False,
                        "KmsKeyId": None,
                        "Status": {"IsLogging": False},
                        "__absent__": True,
                    },
                )
            ]

        resources: list[Resource] = []
        for trail in trails:
            raw = dict(trail)
            try:
                raw["Status"] = client.get_trail_status(Name=trail["TrailARN"])
            except (ClientError, KeyError):
                raw["Status"] = {}
            resources.append(
                Resource(
                    resource_id=trail.get("Name", trail.get("TrailARN", "unknown")),
                    resource_type=self.resource_type,
                    region=self.region,
                    name=trail.get("Name", ""),
                    raw=raw,
                )
            )
        return resources
