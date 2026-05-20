variable "project" {
  description = "Project name for naming and tagging."
  type        = string
}

variable "environment" {
  description = "Deployment environment."
  type        = string
}

variable "owner" {
  description = "Owning team or individual."
  type        = string
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC."
  type        = string
}

variable "public_subnet_cidrs" {
  description = "List of CIDR blocks for public subnets (one per AZ)."
  type        = list(string)
}

variable "azs" {
  description = "List of availability zones."
  type        = list(string)
}

variable "common_tags" {
  description = "Map of common tags to apply to every resource in this module."
  type        = map(string)
}
