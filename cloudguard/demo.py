"""Provision an intentionally-insecure AWS environment for demos and tests.

Everything here uses ordinary boto3 calls. In demo/test mode those calls are
intercepted by ``moto`` (an in-memory AWS mock), so the whole thing runs with
no real AWS account, no credentials, and no cost - while still exercising the
exact same collectors and checks that run against a real account.

The environment deliberately mixes insecure and secure resources so reports
show a realistic mix of PASS and FAIL results rather than an all-red wall.
"""

from __future__ import annotations

import json

import boto3

REGION = "us-east-1"


def provision_insecure_environment(session: boto3.Session | None = None) -> None:
    session = session or boto3.Session()
    _provision_s3(session)
    _provision_iam(session)
    _provision_security_groups(session)
    # (No CloudTrail is created on purpose: the absence itself is a finding.)


def _provision_s3(session: boto3.Session) -> None:
    s3 = session.client("s3", region_name=REGION)

    # --- Insecure bucket: public policy, no encryption, no block-public-access ---
    public_bucket = "acme-customer-exports"
    s3.create_bucket(Bucket=public_bucket)
    s3.put_bucket_policy(
        Bucket=public_bucket,
        Policy=json.dumps(
            {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Sid": "PublicRead",
                        "Effect": "Allow",
                        "Principal": "*",
                        "Action": "s3:GetObject",
                        "Resource": f"arn:aws:s3:::{public_bucket}/*",
                    }
                ],
            }
        ),
    )

    # --- Hardened bucket: encryption, versioning, and block-public-access on ---
    secure_bucket = "acme-secure-backups"
    s3.create_bucket(Bucket=secure_bucket)
    s3.put_public_access_block(
        Bucket=secure_bucket,
        PublicAccessBlockConfiguration={
            "BlockPublicAcls": True,
            "IgnorePublicAcls": True,
            "BlockPublicPolicy": True,
            "RestrictPublicBuckets": True,
        },
    )
    s3.put_bucket_encryption(
        Bucket=secure_bucket,
        ServerSideEncryptionConfiguration={
            "Rules": [{"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}]
        },
    )
    s3.put_bucket_versioning(
        Bucket=secure_bucket, VersioningConfiguration={"Status": "Enabled"}
    )


def _provision_iam(session: boto3.Session) -> None:
    iam = session.client("iam")

    # Weak account password policy (below the 14-char recommendation).
    iam.update_account_password_policy(MinimumPasswordLength=8, RequireNumbers=False)

    # Over-privileged human user: console access, no MFA, direct admin, two keys.
    iam.create_user(UserName="devops-admin")
    iam.create_login_profile(UserName="devops-admin", Password="Temp!Password123")
    iam.attach_user_policy(
        UserName="devops-admin",
        PolicyArn="arn:aws:iam::aws:policy/AdministratorAccess",
    )
    iam.create_access_key(UserName="devops-admin")
    iam.create_access_key(UserName="devops-admin")

    # A tidy service account: programmatic only, single key, no admin.
    iam.create_user(UserName="ci-deployer")
    iam.create_access_key(UserName="ci-deployer")


def _provision_security_groups(session: boto3.Session) -> None:
    ec2 = session.client("ec2", region_name=REGION)
    vpc_id = ec2.create_vpc(CidrBlock="10.0.0.0/16")["Vpc"]["VpcId"]

    # Wide-open group: SSH, RDP, and all traffic from the internet.
    open_sg = ec2.create_security_group(
        GroupName="legacy-jumpbox", Description="legacy jump box", VpcId=vpc_id
    )["GroupId"]
    ec2.authorize_security_group_ingress(
        GroupId=open_sg,
        IpPermissions=[
            {
                "IpProtocol": "tcp",
                "FromPort": 22,
                "ToPort": 22,
                "IpRanges": [{"CidrIp": "0.0.0.0/0"}],
            },
            {
                "IpProtocol": "tcp",
                "FromPort": 3389,
                "ToPort": 3389,
                "IpRanges": [{"CidrIp": "0.0.0.0/0"}],
            },
        ],
    )

    # Well-scoped group: SSH from a corporate CIDR only.
    scoped_sg = ec2.create_security_group(
        GroupName="app-tier", Description="app tier", VpcId=vpc_id
    )["GroupId"]
    ec2.authorize_security_group_ingress(
        GroupId=scoped_sg,
        IpPermissions=[
            {
                "IpProtocol": "tcp",
                "FromPort": 22,
                "ToPort": 22,
                "IpRanges": [{"CidrIp": "203.0.113.0/24"}],
            }
        ],
    )
