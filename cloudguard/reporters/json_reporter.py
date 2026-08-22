"""JSON reporter - the machine-readable output for SIEM/CI integration."""

from __future__ import annotations

import json
from pathlib import Path

from ..models import ScanResult
from ..scoring import compute_score


def build_document(result: ScanResult) -> dict:
    score = compute_score(result)
    return {
        "schema": "cloudguard.scan/v1",
        "provider": result.provider,
        "account_id": result.account_id,
        "regions": result.regions,
        "started_at": result.started_at,
        "finished_at": result.finished_at,
        "summary": score.to_dict(),
        "findings": [f.to_dict() for f in result.findings],
    }


def render_json(result: ScanResult) -> str:
    return json.dumps(build_document(result), indent=2, default=str)


def write_json(result: ScanResult, path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_json(result), encoding="utf-8")
    return path
