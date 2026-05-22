"""
Detector: EC2 instances that have been in 'stopped' state for more than N days.

Note: stopped EC2 instances do NOT incur compute charges, but their attached
EBS root volumes continue to cost money. We report the estimated EBS cost only.
"""

import re
from datetime import datetime, timezone
from typing import Any

from constants import EBS_GP3_COST_PER_GB_MONTH


# AWS encodes the stop time inside StateTransitionReason, e.g.:
# "User initiated (2026-01-01 12:00:00 GMT)"
_STOP_TIME_RE = re.compile(r"\((\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} GMT)\)")


def _parse_stop_time(reason: str) -> datetime | None:
    match = _STOP_TIME_RE.search(reason or "")
    if not match:
        return None
    try:
        return datetime.strptime(match.group(1), "%Y-%m-%d %H:%M:%S GMT").replace(
            tzinfo=timezone.utc
        )
    except ValueError:
        return None


def _days_stopped(reason: str) -> int:
    stop_time = _parse_stop_time(reason)
    if stop_time is None:
        # Cannot determine stop time — treat as 0 so we don't false-positive.
        return 0
    return (datetime.now(tz=timezone.utc) - stop_time).days


def _tags_dict(tag_list: list) -> dict:
    return {t["Key"]: t["Value"] for t in (tag_list or [])}


def _is_protected(tags: dict) -> bool:
    return tags.get("Protected", "").lower() == "true"


def _root_volume_cost(instance: dict) -> float:
    """Estimate monthly cost of the root EBS volume (assume gp3, 8 GB default)."""
    for mapping in instance.get("BlockDeviceMappings", []):
        if mapping.get("DeviceName") in ("/dev/xvda", "/dev/sda1"):
            # We can't get volume size from instance metadata without a describe_volumes
            # call; assume 8 GB (typical root volume) for the estimate.
            return round(8 * EBS_GP3_COST_PER_GB_MONTH, 2)
    return round(8 * EBS_GP3_COST_PER_GB_MONTH, 2)


def detect(ec2_client: Any, stopped_days: int = 14) -> list[dict]:
    """
    Return findings for EC2 instances in 'stopped' state for > stopped_days days.
    """
    findings = []

    paginator = ec2_client.get_paginator("describe_instances")
    for page in paginator.paginate(
        Filters=[{"Name": "instance-state-name", "Values": ["stopped"]}]
    ):
        for reservation in page["Reservations"]:
            for inst in reservation["Instances"]:
                tags = _tags_dict(inst.get("Tags", []))
                reason = inst.get("StateTransitionReason", "")
                days = _days_stopped(reason)

                if days < stopped_days:
                    continue

                findings.append(
                    {
                        "resource_id": inst["InstanceId"],
                        "resource_type": "ec2_instance",
                        "reason": f"stopped for {days} days",
                        "age_days": days,
                        "estimated_monthly_cost_usd": _root_volume_cost(inst),
                        "tags": tags,
                        "suggested_action": "terminate",
                        "safe_to_auto_delete": not _is_protected(tags),
                    }
                )

    return findings
