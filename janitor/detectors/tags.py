"""
Detector: resources missing one or more required tags (Project, Environment, Owner).

Untagged resources are impossible to attribute to a team or cost centre, making
cleanup risky and budgeting inaccurate. This detector scans EC2 instances and
EBS volumes for missing required tags.
"""

from typing import Any

from constants import REQUIRED_TAGS


def _tags_dict(tag_list: list) -> dict:
    return {t["Key"]: t["Value"] for t in (tag_list or [])}


def _missing_tags(tags: dict) -> list[str]:
    return [key for key in REQUIRED_TAGS if key not in tags]


def _is_protected(tags: dict) -> bool:
    return tags.get("Protected", "").lower() == "true"


def _check_instances(ec2_client: Any) -> list[dict]:
    findings = []
    paginator = ec2_client.get_paginator("describe_instances")

    for page in paginator.paginate():
        for reservation in page["Reservations"]:
            for inst in reservation["Instances"]:
                # Skip terminated instances — they no longer cost money.
                if inst["State"]["Name"] == "terminated":
                    continue

                tags = _tags_dict(inst.get("Tags", []))
                missing = _missing_tags(tags)
                if not missing:
                    continue

                findings.append(
                    {
                        "resource_id": inst["InstanceId"],
                        "resource_type": "ec2_instance",
                        "reason": f"missing required tags: {', '.join(missing)}",
                        "age_days": 0,
                        "estimated_monthly_cost_usd": 0.0,
                        "tags": {k: tags.get(k) for k in REQUIRED_TAGS},
                        "suggested_action": "tag",
                        "safe_to_auto_delete": False,  # never auto-delete for missing tags
                    }
                )

    return findings


def _check_volumes(ec2_client: Any) -> list[dict]:
    findings = []
    paginator = ec2_client.get_paginator("describe_volumes")

    for page in paginator.paginate():
        for vol in page["Volumes"]:
            tags = _tags_dict(vol.get("Tags", []))
            missing = _missing_tags(tags)
            if not missing:
                continue

            findings.append(
                {
                    "resource_id": vol["VolumeId"],
                    "resource_type": "ebs_volume",
                    "reason": f"missing required tags: {', '.join(missing)}",
                    "age_days": 0,
                    "estimated_monthly_cost_usd": 0.0,
                    "tags": {k: tags.get(k) for k in REQUIRED_TAGS},
                    "suggested_action": "tag",
                    "safe_to_auto_delete": False,
                }
            )

    return findings


def detect(ec2_client: Any) -> list[dict]:
    """Return findings for EC2 instances and EBS volumes missing required tags."""
    return _check_instances(ec2_client) + _check_volumes(ec2_client)
