# ---------------------------------------------------------------------------
# Orphan EBS volume — intentionally NOT attached to any instance.
# This is a known test fixture for the Cost Janitor (Part B).
# In a real environment this would represent forgotten scratch storage.
# ---------------------------------------------------------------------------
resource "aws_ebs_volume" "orphan" {
  availability_zone = var.azs[0]
  size              = var.orphan_ebs_size_gb
  type              = "gp3"

  # NOTE: No attachment resource — this volume stays in "available" state
  # so the Cost Janitor can detect it as an orphan during CI.

  tags = merge(local.common_tags, {
    Name    = "${var.project}-${var.environment}-orphan-vol"
    Purpose = "janitor-test-fixture"
  })
}
