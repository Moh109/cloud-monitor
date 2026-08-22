"""Collector for EC2 security groups (network exposure)."""

from __future__ import annotations

from botocore.exceptions import ClientError

from ..models import Resource
from .base import Collector


class EC2SecurityGroupCollector(Collector):
    service = "ec2"
    resource_type = "aws_security_group"
    scope = "regional"

    def collect(self) -> list[Resource]:
        client = self.session.client("ec2", region_name=self.region)
        resources: list[Resource] = []

        try:
            groups = client.describe_security_groups().get("SecurityGroups", [])
        except ClientError:
            return resources

        for sg in groups:
            resources.append(
                Resource(
                    resource_id=sg["GroupId"],
                    resource_type=self.resource_type,
                    region=self.region,
                    name=sg.get("GroupName", ""),
                    raw=sg,
                )
            )
        return resources
