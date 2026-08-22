"""Unit tests for individual checks using synthetic resources (no AWS/moto)."""

from __future__ import annotations

import json

from cloudguard.checks.cloudtrail_checks import CloudTrailEnabled, CloudTrailMultiRegion
from cloudguard.checks.ec2_checks import SGOpenAllPorts, SGOpenRDP, SGOpenSSH
from cloudguard.checks.iam_checks import (
    IAMDirectAdminPolicy,
    IAMMultipleAccessKeys,
    IAMPasswordPolicyLength,
    IAMUserMFA,
)
from cloudguard.checks.s3_checks import (
    S3BlockPublicAccess,
    S3EncryptionAtRest,
    S3PublicAcl,
    S3PublicPolicy,
)
from cloudguard.models import Resource, Status


def s3(raw: dict) -> Resource:
    return Resource("b", "aws_s3_bucket", "us-east-1", "b", raw)


# --- S3 -------------------------------------------------------------------

def test_s3_block_public_access_all_flags_required():
    good = {"BlockPublicAcls": True, "IgnorePublicAcls": True,
            "BlockPublicPolicy": True, "RestrictPublicBuckets": True}
    assert S3BlockPublicAccess().evaluate(s3({"PublicAccessBlock": good})) is True
    partial = dict(good, RestrictPublicBuckets=False)
    assert S3BlockPublicAccess().evaluate(s3({"PublicAccessBlock": partial})) is False
    assert S3BlockPublicAccess().evaluate(s3({"PublicAccessBlock": None})) is False


def test_s3_encryption():
    assert S3EncryptionAtRest().evaluate(s3({"Encryption": {"Rules": [{}]}})) is True
    assert S3EncryptionAtRest().evaluate(s3({"Encryption": None})) is False


def test_s3_public_acl():
    public = {"Grants": [{"Grantee": {"URI":
              "http://acs.amazonaws.com/groups/global/AllUsers"}, "Permission": "READ"}]}
    assert S3PublicAcl().evaluate(s3({"Acl": public})) is False
    assert S3PublicAcl().evaluate(s3({"Acl": {"Grants": []}})) is True


def test_s3_public_policy_wildcard_without_condition_fails():
    policy = json.dumps({"Statement": [
        {"Effect": "Allow", "Principal": "*", "Action": "s3:GetObject"}]})
    assert S3PublicPolicy().evaluate(s3({"Policy": policy})) is False


def test_s3_public_policy_wildcard_with_condition_passes():
    policy = json.dumps({"Statement": [
        {"Effect": "Allow", "Principal": "*", "Action": "s3:GetObject",
         "Condition": {"IpAddress": {"aws:SourceIp": "203.0.113.0/24"}}}]})
    assert S3PublicPolicy().evaluate(s3({"Policy": policy})) is True


# --- IAM ------------------------------------------------------------------

def test_iam_password_policy_length():
    acct = Resource("a", "aws_iam_account", "global", "a",
                    {"PasswordPolicy": {"MinimumPasswordLength": 14}})
    assert IAMPasswordPolicyLength().evaluate(acct) is True
    acct.raw["PasswordPolicy"]["MinimumPasswordLength"] = 8
    assert IAMPasswordPolicyLength().evaluate(acct) is False


def test_iam_mfa_only_applies_to_console_users():
    prog = Resource("u", "aws_iam_user", "global", "u",
                    {"HasConsoleAccess": False, "MFADevices": []})
    assert IAMUserMFA().evaluate(prog) is True  # not applicable -> pass
    console = Resource("u", "aws_iam_user", "global", "u",
                       {"HasConsoleAccess": True, "MFADevices": []})
    assert IAMUserMFA().evaluate(console) is False


def test_iam_direct_admin_policy():
    admin = Resource("u", "aws_iam_user", "global", "u", {"AttachedPolicies": [
        {"PolicyName": "AdministratorAccess",
         "PolicyArn": "arn:aws:iam::aws:policy/AdministratorAccess"}]})
    assert IAMDirectAdminPolicy().evaluate(admin) is False


def test_iam_multiple_access_keys():
    two = Resource("u", "aws_iam_user", "global", "u", {"AccessKeys": [
        {"AccessKeyId": "A", "Status": "Active"},
        {"AccessKeyId": "B", "Status": "Active"}]})
    assert IAMMultipleAccessKeys().evaluate(two) is False
    one = Resource("u", "aws_iam_user", "global", "u", {"AccessKeys": [
        {"AccessKeyId": "A", "Status": "Active"},
        {"AccessKeyId": "B", "Status": "Inactive"}]})
    assert IAMMultipleAccessKeys().evaluate(one) is True


# --- EC2 security groups --------------------------------------------------

def sg(perms) -> Resource:
    return Resource("sg-1", "aws_security_group", "us-east-1", "sg", {"IpPermissions": perms})


def test_sg_open_ssh():
    open_22 = [{"IpProtocol": "tcp", "FromPort": 22, "ToPort": 22,
                "IpRanges": [{"CidrIp": "0.0.0.0/0"}]}]
    assert SGOpenSSH().evaluate(sg(open_22)) is False
    scoped = [{"IpProtocol": "tcp", "FromPort": 22, "ToPort": 22,
               "IpRanges": [{"CidrIp": "10.0.0.0/8"}]}]
    assert SGOpenSSH().evaluate(sg(scoped)) is True


def test_sg_open_rdp_via_range():
    wide = [{"IpProtocol": "tcp", "FromPort": 1024, "ToPort": 4000,
             "IpRanges": [{"CidrIp": "0.0.0.0/0"}]}]
    assert SGOpenRDP().evaluate(sg(wide)) is False  # 3389 is inside 1024-4000


def test_sg_all_ports():
    allp = [{"IpProtocol": "-1", "IpRanges": [{"CidrIp": "0.0.0.0/0"}]}]
    assert SGOpenAllPorts().evaluate(sg(allp)) is False
    assert SGOpenSSH().evaluate(sg(allp)) is False  # -1 covers every port


# --- CloudTrail -----------------------------------------------------------

def test_cloudtrail_absent_fails():
    absent = Resource("none", "aws_cloudtrail_trail", "us-east-1", "none",
                      {"Status": {"IsLogging": False}, "IsMultiRegionTrail": False,
                       "__absent__": True})
    assert CloudTrailEnabled().evaluate(absent) is False
    assert CloudTrailMultiRegion().evaluate(absent) is False


def test_check_never_raises_on_bad_input():
    """The base run() must convert exceptions into an ERROR finding, not crash."""
    broken = Resource("x", "aws_s3_bucket", "us-east-1", "x", {"Policy": "{not-json"})
    finding = S3PublicPolicy().run(broken)
    assert finding.status == Status.ERROR
