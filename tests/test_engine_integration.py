"""End-to-end test: provision the mock insecure account and run a full scan."""

from __future__ import annotations

import boto3
import pytest
from moto import mock_aws

from cloudguard.demo import provision_insecure_environment
from cloudguard.engine import Scanner
from cloudguard.models import Severity, Status
from cloudguard.reporters import render_html, render_json
from cloudguard.scoring import compute_score


@pytest.fixture
def scan_result(monkeypatch):
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")
    monkeypatch.setenv("MOTO_IAM_LOAD_MANAGED_POLICIES", "true")
    with mock_aws():
        session = boto3.Session(region_name="us-east-1")
        provision_insecure_environment(session)
        yield Scanner(session=session, regions=["us-east-1"]).scan()


def test_scan_produces_findings(scan_result):
    assert scan_result.findings, "scan should produce findings"
    assert scan_result.account_id == "123456789012"  # moto's canned account id


def test_no_checks_error(scan_result):
    errored = [f for f in scan_result.findings if f.status == Status.ERROR]
    assert not errored, f"checks errored: {[f.check_id for f in errored]}"


def test_public_bucket_is_flagged(scan_result):
    fails = {
        (f.check_id, f.resource_id)
        for f in scan_result.failed
    }
    assert ("S3.4", "acme-customer-exports") in fails  # public bucket policy
    assert ("S3.1", "acme-customer-exports") in fails  # no block public access


def test_secure_bucket_passes_key_controls(scan_result):
    passes = {(f.check_id, f.resource_id) for f in scan_result.passed}
    assert ("S3.1", "acme-secure-backups") in passes
    assert ("S3.2", "acme-secure-backups") in passes


def test_open_security_group_flagged_for_ssh_and_rdp(scan_result):
    ssh = [f for f in scan_result.failed if f.check_id == "EC2.1"]
    rdp = [f for f in scan_result.failed if f.check_id == "EC2.2"]
    assert ssh and rdp


def test_admin_user_flagged(scan_result):
    admin_fails = {
        f.check_id
        for f in scan_result.failed
        if f.resource_id == "devops-admin"
    }
    assert {"IAM.2", "IAM.3", "IAM.4"} <= admin_fails


def test_score_is_reasonable(scan_result):
    score = compute_score(scan_result)
    assert 0 <= score.score <= 100
    assert score.grade in {"A", "B", "C", "D", "F"}
    assert score.failed_by_severity[Severity.CRITICAL.value] >= 1


def test_reporters_render(scan_result):
    assert '"schema": "cloudguard.scan/v1"' in render_json(scan_result)
    html = render_html(scan_result)
    assert "CloudGuard" in html and "Posture score" in html
