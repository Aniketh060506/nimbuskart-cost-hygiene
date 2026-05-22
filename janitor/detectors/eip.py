"""
Detector: Elastic IPs not associated with any running instance.

An idle EIP costs $0.005/hour (~$3.65/month). They accumulate quickly when
engineers spin up instances, allocate IPs, and then terminate without releasing.
"""

from datetime import datetime, timezone
from typing import Any

from constants import EIP_COST_PER_MONTH


def _tags_dict(tag_list: list) -> dict:
    return {t["Key"]: t["Value"] for t in (tag_list or [])}


def _is_protected(tags: dict) -> bool:
    return tags.get("Protected", "").lower() == "true"


def detect(ec2_client: Any) -> list[dict]:
    """
    Return findings for Elastic IPs that have no InstanceId and no AssociationId.
    """
    findings = []

    response = ec2_client.describe_addresses()

    for addr in response.get("Addresses", []):
        # An EIP is orphaned when it is allocated but not associated with anything.
        if addr.get("InstanceId") or addr.get("AssociationId"):
            continue

        tags = _tags_dict(addr.get("Tags", []))

        findings.append(
            {
                "resource_id": addr.get("AllocationId", addr.get("PublicIp")),
                "resource_type": "elastic_ip",
                "reason": "not associated with any instance",
                "age_days": 0,  # AWS does not expose allocation timestamp in this API
                "estimated_monthly_cost_usd": round(EIP_COST_PER_MONTH, 2),
                "tags": tags,
                "suggested_action": "release",
                "safe_to_auto_delete": not _is_protected(tags),
            }
        )

    return findings
