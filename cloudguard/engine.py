"""Scan orchestration: collect resources, run checks, assemble results."""

from __future__ import annotations

from datetime import datetime, timezone

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from .checks import CHECK_REGISTRY
from .collectors import ALL_COLLECTORS
from .models import Resource, ScanResult


class Scanner:
    def __init__(self, session: boto3.Session | None = None, regions: list[str] | None = None):
        self.session = session or boto3.Session()
        self.regions = regions or ["us-east-1"]

    def _account_id(self) -> str:
        try:
            return self.session.client("sts").get_caller_identity().get("Account", "")
        except (ClientError, BotoCoreError):
            return ""

    def _collect(self) -> list[Resource]:
        resources: list[Resource] = []
        global_done: set[str] = set()

        for region in self.regions:
            for collector_cls in ALL_COLLECTORS:
                # Global services (IAM, S3) are enumerated once, not per region.
                if collector_cls.scope == "global":
                    if collector_cls.__name__ in global_done:
                        continue
                    global_done.add(collector_cls.__name__)
                resources.extend(collector_cls(self.session, region).collect())
        return resources

    def scan(self) -> ScanResult:
        started = datetime.now(timezone.utc).isoformat()
        resources = self._collect()

        by_type: dict[str, list[Resource]] = {}
        for res in resources:
            by_type.setdefault(res.resource_type, []).append(res)

        findings = []
        for check_cls in CHECK_REGISTRY:
            check = check_cls()
            for res in by_type.get(check.resource_type, []):
                findings.append(check.run(res))

        return ScanResult(
            findings=findings,
            account_id=self._account_id(),
            provider="aws",
            regions=list(self.regions),
            started_at=started,
            finished_at=datetime.now(timezone.utc).isoformat(),
        )
