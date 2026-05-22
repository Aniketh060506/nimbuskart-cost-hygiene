#!/usr/bin/env python3
"""
NimbusKart Cost Janitor

Scans an AWS account (or LocalStack) for orphaned resources and emits a
structured report. Supports --dry-run (default) and --delete modes.

Usage:
    python janitor.py --dry-run                     # safe scan, exit 1 if orphans
    python janitor.py --delete                       # delete orphans (skips Protected=true)
    python janitor.py --endpoint-url http://localhost:4566  # target LocalStack
"""

import sys
import argparse
from typing import Optional

import boto3

from constants import PROTECTED_TAG_KEY, PROTECTED_TAG_VALUE
from detectors import ebs, ec2, eip, tags
from reporter import build_report, write_json, write_markdown


# ---------------------------------------------------------------------------
# Session helpers
# ---------------------------------------------------------------------------

def build_clients(region: str, endpoint_url: Optional[str]):
    """Create boto3 EC2, S3, and STS clients."""
    client_kwargs = {"region_name": region}
    if endpoint_url:
        client_kwargs["endpoint_url"] = endpoint_url

    session = boto3.Session(region_name=region)
    mk = lambda svc: session.client(svc, **({} if not endpoint_url else {"endpoint_url": endpoint_url}))
    return mk("ec2"), mk("s3"), mk("sts")


# ---------------------------------------------------------------------------
# Delete helpers (--delete mode only)
# ---------------------------------------------------------------------------

def _is_protected(tags_dict: dict) -> bool:
    return tags_dict.get(PROTECTED_TAG_KEY, "").lower() == PROTECTED_TAG_VALUE


def _delete_findings(ec2_client, findings: list[dict]) -> None:
    """Attempt to delete/release each finding that is safe_to_auto_delete."""
    for finding in findings:
        rid = finding["resource_id"]
        rtype = finding["resource_type"]
        ftags = finding.get("tags", {})

        if _is_protected(ftags):
            print(f"[delete] SKIP {rid} — tagged {PROTECTED_TAG_KEY}={PROTECTED_TAG_VALUE}")
            continue

        if not finding.get("safe_to_auto_delete", False):
            print(f"[delete] SKIP {rid} — safe_to_auto_delete=false")
            continue

        try:
            if rtype == "ebs_volume":
                ec2_client.delete_volume(VolumeId=rid)
                print(f"[delete] Deleted EBS volume {rid}")
            elif rtype == "ec2_instance":
                ec2_client.terminate_instances(InstanceIds=[rid])
                print(f"[delete] Terminated EC2 instance {rid}")
            elif rtype == "elastic_ip":
                ec2_client.release_address(AllocationId=rid)
                print(f"[delete] Released Elastic IP {rid}")
            else:
                print(f"[delete] SKIP {rid} — no delete handler for type {rtype}")
        except Exception as exc:
            print(f"[delete] ERROR on {rid}: {exc}", file=sys.stderr)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        prog="janitor",
        description="Detect and optionally remove orphaned AWS resources.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Report orphans without deleting (default).",
    )
    parser.add_argument(
        "--delete",
        action="store_true",
        help="Delete orphaned resources; respects Protected=true tag.",
    )
    parser.add_argument(
        "--stopped-days",
        type=int,
        default=14,
        metavar="N",
        help="Flag EC2 instances stopped for more than N days (default: 14).",
    )
    parser.add_argument(
        "--region",
        type=str,
        default="us-east-1",
        help="AWS region to scan (default: us-east-1).",
    )
    parser.add_argument(
        "--endpoint-url",
        type=str,
        default=None,
        help="Override endpoint URL (e.g. http://localhost:4566 for LocalStack).",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="report.json",
        help="Path for the JSON report (default: report.json).",
    )
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)

    # --delete implies NOT dry-run
    if args.delete:
        args.dry_run = False

    mode = "DRY-RUN" if args.dry_run else "DELETE ⚠️"
    print(f"[janitor] mode={mode} region={args.region} stopped_days={args.stopped_days}")

    ec2_client, s3_client, sts_client = build_clients(args.region, args.endpoint_url)

    # -----------------------------------------------------------------------
    # Run all detectors
    # -----------------------------------------------------------------------
    print("[janitor] Detecting unattached EBS volumes ...")
    ebs_findings = ebs.detect(ec2_client)

    print("[janitor] Detecting long-stopped EC2 instances ...")
    ec2_findings = ec2.detect(ec2_client, stopped_days=args.stopped_days)

    print("[janitor] Detecting unassociated Elastic IPs ...")
    eip_findings = eip.detect(ec2_client)

    print("[janitor] Detecting resources with missing required tags ...")
    tag_findings = tags.detect(ec2_client)

    all_findings = ebs_findings + ec2_findings + eip_findings + tag_findings

    # -----------------------------------------------------------------------
    # Generate report
    # -----------------------------------------------------------------------
    report = build_report(all_findings, args.region, sts_client)

    md_path = args.output.replace(".json", ".md")
    write_json(report, args.output)
    write_markdown(report, md_path)

    total = report["summary"]["total_orphans"]
    waste = report["summary"]["estimated_monthly_waste_usd"]
    print(f"\n[janitor] Found {total} orphan(s) | Est. waste: ${waste:.2f}/month")

    # -----------------------------------------------------------------------
    # Delete mode
    # -----------------------------------------------------------------------
    if args.delete and all_findings:
        print("\n[janitor] Running DELETE mode ...")
        _delete_findings(ec2_client, all_findings)

    # -----------------------------------------------------------------------
    # Exit code: non-zero if orphans found in dry-run (so CI fails)
    # -----------------------------------------------------------------------
    if args.dry_run and total > 0:
        print(f"\n[janitor] Exiting with code 1 — {total} orphan(s) detected in dry-run mode.")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
