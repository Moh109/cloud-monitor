"""Check registry.

Importing this package imports every check module, which registers each check
in ``CHECK_REGISTRY`` via the ``@register`` decorator.
"""

from __future__ import annotations

from .base import CHECK_REGISTRY, Check, register

# Importing these modules populates CHECK_REGISTRY as a side effect.
from . import cloudtrail_checks  # noqa: E402,F401
from . import ec2_checks  # noqa: E402,F401
from . import iam_checks  # noqa: E402,F401
from . import s3_checks  # noqa: E402,F401

__all__ = ["CHECK_REGISTRY", "Check", "register"]
