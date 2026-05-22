"""
Detector: EBS volumes in 'available' state (not attached to any instance).
"""

from datetime import datetime, timezone
from typing import Any

from constants import EBS_GP3_COST_PER_GB_MONTH, EBS_GP2_COST_PER_GB_MONTH


def _age_days(create_time: datetime) -> int:
    now = datetime.now(tz=timezone.utc)
    return (now - create_time).days


def _monthly_cost(size_gb: int, volume_type: str) -> float:
    rate = EBS_GP2_COST_PER_GB_MONTH if volume_type == "gp2" else EBS_GP3_COST_PER_GB_MONTH
    return round(size_gb * rate, 2)


def _tags_dict(tag_list: list) -> dict:
    """Convert AWS tag list [{'Key':k,'Value':v}] → {k: v}."""
    return {t["Key"]: t["Value"] for t in (tag_list or [])}


def _is_protected(tags: dict) -> bool:
    return tags.get("Protected", "").lower() == "true"


def detect(ec2_client: Any) -> list[dict]:
    """
    Return a list of findings for EBS volumes in 'available' state.
    These volumes are not attached to any instance and are incurring cost.
    """
    findings = []

    paginator = ec2_client.get_paginator("describe_volumes")
    for page in paginator.paginate(Filters=[{"Name": "status", "Values": ["available"]}]):
        for vol in page["Volumes"]:
            tags = _tags_dict(vol.get("Tags", []))
            age = _age_days(vol["CreateTime"])
            cost = _monthly_cost(vol["Size"], vol.get("VolumeType", "gp3"))

            findings.append(
                {
                    "resource_id": vol["VolumeId"],
                    "resource_type": "ebs_volume",
                    "reason": "unattached",
                    "age_days": age,
                    "estimated_monthly_cost_usd": cost,
                    "tags": tags,
                    "suggested_action": "delete",
                    "safe_to_auto_delete": not _is_protected(tags),
                }
            )

    return findings
