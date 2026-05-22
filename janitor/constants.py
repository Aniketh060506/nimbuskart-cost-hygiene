# ---------------------------------------------------------------------------
# Pricing constants for Cost Janitor waste estimation
# All prices are for us-east-1 (on-demand, as of Jan 2026)
# ---------------------------------------------------------------------------

# Source: https://aws.amazon.com/ebs/pricing/
EBS_GP3_COST_PER_GB_MONTH: float = 0.08   # $/GB-month
EBS_GP2_COST_PER_GB_MONTH: float = 0.10   # $/GB-month (older volumes)

# Source: https://aws.amazon.com/ec2/pricing/on-demand/ (Linux, t3.micro)
EC2_T3_MICRO_HOURLY: float = 0.0104       # $/hour
EC2_HOURS_PER_MONTH: int = 730            # approximate hours in a month

# Source: https://aws.amazon.com/ec2/pricing/on-demand/#Elastic_IP_Addresses
# Idle EIP (not associated with a running instance) costs $0.005/hr
EIP_IDLE_COST_PER_HOUR: float = 0.005     # $/hour
EIP_COST_PER_MONTH: float = EIP_IDLE_COST_PER_HOUR * EC2_HOURS_PER_MONTH  # ~$3.65

# Tags that every resource must carry
REQUIRED_TAGS: list[str] = ["Project", "Environment", "Owner"]

# Resources tagged with Protected=true are never auto-deleted
PROTECTED_TAG_KEY: str = "Protected"
PROTECTED_TAG_VALUE: str = "true"
