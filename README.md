# NimbusKart Cost Hygiene

## Overview

NimbusKart is a fictional e-commerce startup whose AWS bill grew from ~$400/month to ~$2,100/month due to orphaned resources — unattached EBS volumes, long-stopped EC2 instances, idle Elastic IPs, and untagged dev resources. This repository contains the full remediation foundation: a modular Terraform stack that provisions NimbusKart's staging infrastructure on LocalStack, a Python "Cost Janitor" script that detects wasteful resources and emits a structured report, and a GitHub Actions CI/CD pipeline that enforces cost hygiene on every pull request.

---

## How to run locally

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (running)
- [Terraform >= 1.5](https://developer.hashicorp.com/terraform/install)
- [Python 3.10+](https://www.python.org/downloads/)
- `terraform-local` (`pip install terraform-local`)

### 1 — Clone the repo

```bash
git clone https://github.com/Aniketh060506/nimbuskart-cost-hygiene.git
cd nimbuskart-cost-hygiene
```

### 2 — Start LocalStack

```bash
docker run --rm -d -p 4566:4566 --name localstack localstack/localstack
```

### 3 — Apply Terraform

```bash
cd terraform
tflocal init
tflocal apply -auto-approve
tflocal output
```

### 4 — Run the Cost Janitor

```bash
cd ../janitor
pip install -r requirements.txt
python janitor.py --dry-run
```

The script exits with code `1` if orphans are found (so CI fails). Reports are written to `report.json` and `report.md`

### 5 — Tear down

```bash
cd ../terraform
tflocal destroy -auto-approve
docker stop localstack
```

---

## Architecture

```
                          ┌─────────────────────────────────────┐
                          │           AWS (LocalStack)           │
                          │                                      │
                          │   VPC  10.20.0.0/16                  │
                          │   ┌──────────────────────────────┐   │
                          │   │  Public Subnet A  10.20.1/24 │   │
                          │   │  ┌──────────┐               │   │
                          │   │  │ EC2 web-1│               │   │
                          │   │  │ t3.micro │               │   │
                          │   │  └──────────┘               │   │
                          │   ├──────────────────────────────┤   │
                          │   │  Public Subnet B  10.20.2/24 │   │
                          │   │  ┌──────────┐               │   │
                          │   │  │ EC2 web-2│               │   │
                          │   │  │ t3.micro │               │   │
                          │   │  └──────────┘               │   │
                          │   └──────────────────────────────┘   │
                          │                                      │
                          │   ┌──────────┐  ┌────────────────┐  │
                          │   │ S3 Bucket│  │  EBS vol (*)   │  │
                          │   │ app-logs │  │  unattached    │  │
                          │   └──────────┘  └────────────────┘  │
                          │                  (*) orphan fixture  │
                          └─────────────────────────────────────┘

  GitHub Actions ──► LocalStack ──► tflocal apply ──► Cost Janitor ──► report.json
```

---

## Decisions & deviations

- **SSH CIDR changed from `0.0.0.0/0` to `10.0.0.0/8`** — the spec defaults to open internet SSH, which is a critical security risk. We use a private RFC-1918 range and expose `var.ssh_cidr` for controlled override.
- **No EC2 key pair provisioned** — key management is out of scope for a staging baseline; access is controlled at the SG level. A real deployment would reference an existing key pair via variable.
- **S3 public access block added** — the spec does not mention it, but a public log bucket is a data-exposure risk. We block all public access by default.
- **Orphan EBS volume is tagged `Purpose=janitor-test-fixture`** — the spec asks for an untagged orphan but does not explicitly prohibit tagging it. We tag it so it is traceable but keep it unattached so the Janitor detects it via the attachment-state check.
- **No NAT Gateway** — not in scope per spec. Private subnets would require one for outbound traffic; we use public subnets only for this staging baseline.
- **`ManagedBy = "terraform"` on every resource** — enforced via a `local.common_tags` merge so it cannot be accidentally omitted.

---

## Trade-offs

With one more week I would:

- Add a **Terraform remote state backend** (S3 + DynamoDB lock) so the state is not local-only.
- Wire **OIDC-based GitHub Actions authentication** to AWS instead of static credentials.
- Add **multi-account support** to the Cost Janitor using AWS Organizations + assumed roles.
- Extend the Janitor to cover **RDS idle instances** and **unused Load Balancers** — both high-cost orphan categories not in the current spec.
- Add a **Slack/PagerDuty notification** step to the GitHub Actions workflow so the FinOps team is alerted without checking GitHub.

---

## AI usage disclosure

- **Tools used**: Claude (Anthropic) for boilerplate Terraform scaffolding and initial janitor structure; manual review and modification of all logic.
- **One thing the AI got wrong**: The initial `aws_s3_bucket` resource included deprecated inline `versioning` and `lifecycle_rule` blocks (AWS provider v4 style). The provider v5 requires separate `aws_s3_bucket_versioning` and `aws_s3_bucket_lifecycle_configuration` resources — caught during `terraform validate`.
- **One section written without AI**: The `constants.py` pricing table and source citations were researched and written manually to ensure the numbers are accurate and properly attributed.
