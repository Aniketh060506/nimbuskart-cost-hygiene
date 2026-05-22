"""
Reporter: generates report.json and report.md from a list of findings.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _get_account_id(sts_client: Any) -> str:
    try:
        return sts_client.get_caller_identity()["Account"]
    except Exception:
        return "000000000000"


def build_report(findings: list[dict], region: str, sts_client: Any) -> dict:
    """Assemble the canonical report structure."""
    total_waste = round(
        sum(f.get("estimated_monthly_cost_usd", 0.0) for f in findings), 2
    )
    return {
        "scan_timestamp": datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "account_id": _get_account_id(sts_client),
        "region": region,
        "summary": {
            "total_orphans": len(findings),
            "estimated_monthly_waste_usd": total_waste,
        },
        "findings": findings,
    }


def write_json(report: dict, path: str) -> None:
    Path(path).write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(f"[reporter] JSON report written to {path}")


def write_markdown(report: dict, path: str) -> None:
    lines = [
        "# 🔍 NimbusKart Cost Janitor Report",
        "",
        f"**Scan time:** {report['scan_timestamp']}  ",
        f"**Account:** `{report['account_id']}`  ",
        f"**Region:** `{report['region']}`  ",
        "",
        "## Summary",
        "",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Total orphans | **{report['summary']['total_orphans']}** |",
        f"| Estimated monthly waste | **${report['summary']['estimated_monthly_waste_usd']:.2f}** |",
        "",
    ]

    if not report["findings"]:
        lines.append("✅ **No orphaned resources found.**")
    else:
        lines += [
            "## Findings",
            "",
            "| Resource ID | Type | Reason | Age (days) | Est. Monthly Cost | Safe to Delete |",
            "|-------------|------|--------|------------|-------------------|----------------|",
        ]
        for f in report["findings"]:
            safe = "✅" if f.get("safe_to_auto_delete") else "⚠️ No"
            cost = f"${f.get('estimated_monthly_cost_usd', 0):.2f}"
            lines.append(
                f"| `{f['resource_id']}` | {f['resource_type']} | {f['reason']} "
                f"| {f.get('age_days', 0)} | {cost} | {safe} |"
            )

    Path(path).write_text("\n".join(lines), encoding="utf-8")
    print(f"[reporter] Markdown report written to {path}")
