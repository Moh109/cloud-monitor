"""Collector registry.

Import all collectors here so the engine can discover them via ``ALL_COLLECTORS``.
"""

from __future__ import annotations

from .cloudtrail import CloudTrailCollector
from .ec2 import EC2SecurityGroupCollector
from .iam import IAMCollector
from .s3 import S3Collector

ALL_COLLECTORS = [
    S3Collector,
    IAMCollector,
    EC2SecurityGroupCollector,
    CloudTrailCollector,
]
