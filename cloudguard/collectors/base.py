"""Base class for cloud resource collectors.

A *collector* is responsible for one service (S3, IAM, EC2, ...). It calls the
provider APIs and returns a list of normalized ``Resource`` objects. Collectors
never make pass/fail decisions - that is the job of the checks - which keeps the
"gather state" and "judge state" concerns cleanly separated.
"""

from __future__ import annotations

import boto3

from ..models import Resource


class Collector:
    service: str = ""
    resource_type: str = ""
    # "global" collectors (IAM, S3) are run once regardless of region count;
    # "regional" collectors are run once per requested region.
    scope: str = "regional"

    def __init__(self, session: boto3.Session, region: str):
        self.session = session
        self.region = region

    def collect(self) -> list[Resource]:
        raise NotImplementedError
