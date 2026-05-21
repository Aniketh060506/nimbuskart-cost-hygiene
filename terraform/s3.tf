# ---------------------------------------------------------------------------
# S3 — application log bucket
# Versioning enabled; lifecycle rule expires non-current versions after 30 days
# ---------------------------------------------------------------------------
resource "aws_s3_bucket" "app_logs" {
  bucket = var.log_bucket_name

  tags = merge(local.common_tags, {
    Name    = var.log_bucket_name
    Purpose = "application-logs"
  })
}

resource "aws_s3_bucket_versioning" "app_logs" {
  bucket = aws_s3_bucket.app_logs.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "app_logs" {
  bucket = aws_s3_bucket.app_logs.id

  rule {
    id     = "expire-noncurrent-versions"
    status = "Enabled"

    noncurrent_version_expiration {
      noncurrent_days = var.noncurrent_version_expiry_days
    }
  }
}

# Block all public access — log buckets must never be public
resource "aws_s3_bucket_public_access_block" "app_logs" {
  bucket = aws_s3_bucket.app_logs.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
