"""EC2 security-group checks: unrestricted ingress from the internet."""

from __future__ import annotations

from ..models import Resource, Severity
from .base import Check, register

_WORLD_CIDRS = {"0.0.0.0/0"}
_WORLD_IPV6 = {"::/0"}


def _open_to_world_on_port(sg: dict, port: int) -> bool:
    """True if the security group allows ingress from anywhere to ``port``."""
    for perm in sg.get("IpPermissions", []):
        world = any(r.get("CidrIp") in _WORLD_CIDRS for r in perm.get("IpRanges", []))
        world_v6 = any(
            r.get("CidrIpv6") in _WORLD_IPV6 for r in perm.get("Ipv6Ranges", [])
        )
        if not (world or world_v6):
            continue
        if perm.get("IpProtocol") == "-1":  # all protocols / all ports
            return True
        from_port, to_port = perm.get("FromPort"), perm.get("ToPort")
        if from_port is not None and to_port is not None and from_port <= port <= to_port:
            return True
    return False


def _open_to_world_all_ports(sg: dict) -> bool:
    for perm in sg.get("IpPermissions", []):
        if perm.get("IpProtocol") != "-1":
            continue
        if any(r.get("CidrIp") in _WORLD_CIDRS for r in perm.get("IpRanges", [])):
            return True
        if any(r.get("CidrIpv6") in _WORLD_IPV6 for r in perm.get("Ipv6Ranges", [])):
            return True
    return False


class _PortCheck(Check):
    port: int = 0

    def evaluate(self, resource: Resource) -> bool:
        return not _open_to_world_on_port(resource.raw, self.port)

    def evidence(self, resource: Resource) -> str:
        return (
            f"Security group {resource.resource_id} allows 0.0.0.0/0 "
            f"ingress to port {self.port}."
        )


@register
class SGOpenSSH(_PortCheck):
    check_id = "EC2.1"
    title = "Security groups should not allow ingress from 0.0.0.0/0 to port 22 (SSH)"
    service = "ec2"
    resource_type = "aws_security_group"
    severity = Severity.CRITICAL
    port = 22
    description = (
        "SSH open to the entire internet exposes hosts to credential brute-force "
        "and exploitation of the SSH service."
    )
    remediation = (
        "Restrict port 22 to known admin CIDRs or a bastion/SSM Session Manager; "
        "never use 0.0.0.0/0."
    )
    frameworks = {"CIS AWS 3.0": "5.2", "MITRE ATT&CK": "T1110", "NIST 800-53": "AC-4"}


@register
class SGOpenRDP(_PortCheck):
    check_id = "EC2.2"
    title = "Security groups should not allow ingress from 0.0.0.0/0 to port 3389 (RDP)"
    service = "ec2"
    resource_type = "aws_security_group"
    severity = Severity.CRITICAL
    port = 3389
    description = (
        "RDP open to the internet is a leading initial-access vector for "
        "ransomware operators."
    )
    remediation = (
        "Restrict port 3389 to known admin CIDRs or a bastion; prefer SSM "
        "Session Manager over exposed RDP."
    )
    frameworks = {"CIS AWS 3.0": "5.3", "MITRE ATT&CK": "T1133", "NIST 800-53": "AC-4"}


@register
class SGOpenAllPorts(Check):
    check_id = "EC2.3"
    title = "Security groups should not allow ingress from 0.0.0.0/0 to all ports"
    service = "ec2"
    resource_type = "aws_security_group"
    severity = Severity.HIGH
    description = (
        "An 'all traffic' rule from anywhere removes the network boundary "
        "entirely, exposing every listening service on attached instances."
    )
    remediation = "Replace the all-ports/all-protocols rule with least-privilege rules."
    frameworks = {"CIS AWS 3.0": "5.4", "MITRE ATT&CK": "T1046", "NIST 800-53": "AC-4"}

    def evaluate(self, resource: Resource) -> bool:
        return not _open_to_world_all_ports(resource.raw)

    def evidence(self, resource: Resource) -> str:
        return (
            f"Security group {resource.resource_id} allows all traffic "
            f"from 0.0.0.0/0."
        )
