variable "project" {
  description = "Project name used for resource naming and tagging."
  type        = string
  default     = "nimbuskart"
}

variable "environment" {
  description = "Deployment environment (e.g. staging, prod)."
  type        = string
  default     = "staging"
}

variable "owner" {
  description = "Team or individual who owns these resources."
  type        = string
  default     = "platform-team"
}

variable "region" {
  description = "AWS region to deploy into."
  type        = string
  default     = "us-east-1"
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC."
  type        = string
  default     = "10.20.0.0/16"
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for the two public subnets (one per AZ)."
  type        = list(string)
  default     = ["10.20.1.0/24", "10.20.2.0/24"]
}

variable "azs" {
  description = "List of availability zones to distribute subnets across."
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b"]
}

# NOTE: Decisions & Deviations — SSH CIDR
# The assignment brief defaults this to 0.0.0.0/0 but that is a critical
# security risk (exposes SSH to the entire internet). We default to a private
# RFC-1918 range and require an explicit override for any public access.
# See README §"Decisions & deviations" for full rationale.
variable "ssh_cidr" {
  description = "CIDR allowed inbound on port 22. MUST NOT be 0.0.0.0/0 in production."
  type        = string
  default     = "10.0.0.0/8"
}

variable "instance_type" {
  description = "EC2 instance type for web tier nodes."
  type        = string
  default     = "t3.micro"
}

variable "web_instance_count" {
  description = "Number of EC2 instances in the web tier."
  type        = number
  default     = 2
}

variable "log_bucket_name" {
  description = "Name of the S3 bucket for application logs."
  type        = string
  default     = "nimbuskart-app-logs"
}

variable "noncurrent_version_expiry_days" {
  description = "Days before non-current S3 object versions are expired."
  type        = number
  default     = 30
}

variable "orphan_ebs_size_gb" {
  description = "Size in GB of the intentionally unattached EBS volume used to test the Cost Janitor."
  type        = number
  default     = 20
}
