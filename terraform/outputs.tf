output "vpc_id" {
  description = "The ID of the NimbusKart VPC."
  value       = module.network.vpc_id
}

output "public_subnet_ids" {
  description = "IDs of the two public subnets."
  value       = module.network.public_subnet_ids
}

output "log_bucket_name" {
  description = "Name of the S3 application log bucket."
  value       = aws_s3_bucket.app_logs.bucket
}

output "web_instance_ids" {
  description = "IDs of the web tier EC2 instances."
  value       = aws_instance.web[*].id
}

output "security_group_id" {
  description = "ID of the web security group."
  value       = aws_security_group.web.id
}

output "orphan_ebs_volume_id" {
  description = "ID of the intentionally unattached EBS volume (Cost Janitor test fixture)."
  value       = aws_ebs_volume.orphan.id
}
