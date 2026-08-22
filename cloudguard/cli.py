"""CloudGuard command-line interface.

Examples
--------
    # Scan a real AWS account (uses your configured credentials / profile):
    cloudguard scan --region us-east-1 --region eu-west-1 --html report.html

    # Run a fully offline demo against a mock, intentionally-insecure account:
    cloudguard scan --demo --html report.html

    # Shift-left in CI: exit non-zero if any HIGH-or-worse control fails:
    cloudguard scan --demo --fail-on HIGH
"""

from __future__ import annotations

import argparse
import os
import sys

import boto3

from . import __version__
from .engine import Scanner
from .models import ScanResult, Severity
from .reporters import render_console, render_json, write_html, write_json


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cloudguard",
        description="CloudGuard - Cloud Security Posture Management scanner.",
    )
    parser.add_argument("--version", action="version", version=f"cloudguard {__version__}")

    sub = parser.add_subparsers(dest="command", required=True)
    scan = sub.add_parser("scan", help="Run a posture scan.")
    scan.add_argument(
        "--region",
        action="append",
        dest="regions",
        help="AWS region to scan (repeatable). Default: us-east-1.",
    )
    scan.add_argument("--profile", help="Named AWS profile to use.")
    scan.add_argument(
        "--demo",
        action="store_true",
        help="Provision and scan a mock insecure account offline (no AWS needed).",
    )
    scan.add_argument("--json", dest="json_path", help="Write JSON report to this path.")
    scan.add_argument("--html", dest="html_path", help="Write HTML report to this path.")
    scan.add_argument(
        "--no-console",
        action="store_true",
        help="Suppress the console summary table.",
    )
    scan.add_argument(
        "--fail-on",
        choices=[s.value for s in Severity],
        help="Exit non-zero if any failing finding is at or above this severity.",
    )
    return parser


def _run_scan(args: argparse.Namespace) -> ScanResult:
    regions = args.regions or ["us-east-1"]

    if args.demo:
        # Mock AWS in-process, provision insecure infra, then scan it.
        from moto import mock_aws

        from .demo import provision_insecure_environment

        os.environ.setdefault("AWS_ACCESS_KEY_ID", "testing")
        os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "testing")
        os.environ.setdefault("AWS_DEFAULT_REGION", regions[0])
        # Let moto resolve AWS-managed policy ARNs (e.g. AdministratorAccess).
        os.environ["MOTO_IAM_LOAD_MANAGED_POLICIES"] = "true"

        with mock_aws():
            session = boto3.Session(region_name=regions[0])
            provision_insecure_environment(session)
            return Scanner(session=session, regions=regions).scan()

    session = boto3.Session(profile_name=args.profile) if args.profile else boto3.Session()
    return Scanner(session=session, regions=regions).scan()


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    result = _run_scan(args)

    if not args.no_console:
        render_console(result)

    if args.json_path:
        path = write_json(result, args.json_path)
        print(f"[cloudguard] JSON report written to {path}")
    if args.html_path:
        path = write_html(result, args.html_path)
        print(f"[cloudguard] HTML report written to {path}")

    if args.fail_on:
        threshold = Severity(args.fail_on)
        if result.has_failure_at_or_above(threshold):
            print(
                f"[cloudguard] Failing controls at or above {threshold.value} found "
                f"- exiting with code 1.",
                file=sys.stderr,
            )
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
