terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# When using tflocal, this block is automatically overridden to point at
# LocalStack (http://localhost:4566). No real AWS credentials are used.
provider "aws" {
  region = var.region

  # LocalStack does not need real credentials — these are dummy values.
  # tflocal injects the correct endpoint overrides automatically.
  access_key = "test"
  secret_key = "test"

  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true
}

# ---------------------------------------------------------------------------
# Common tags — applied to every resource via merge()
# ---------------------------------------------------------------------------
locals {
  common_tags = {
    Project     = var.project
    Environment = var.environment
    Owner       = var.owner
    ManagedBy   = "terraform"
  }
}

# ---------------------------------------------------------------------------
# Network module — VPC, subnets, route tables
# ---------------------------------------------------------------------------
module "network" {
  source = "./modules/network"

  project             = var.project
  environment         = var.environment
  owner               = var.owner
  vpc_cidr            = var.vpc_cidr
  public_subnet_cidrs = var.public_subnet_cidrs
  azs                 = var.azs
  common_tags         = local.common_tags
}

# ---------------------------------------------------------------------------
# Security Group
# Deviation: SSH (port 22) is restricted to var.ssh_cidr (default 10.0.0.0/8)
# instead of the spec's 0.0.0.0/0.  Exposing SSH to the entire internet is a
# critical security risk — see README "Decisions & deviations".
# ---------------------------------------------------------------------------
resource "aws_security_group" "web" {
  name        = "${var.project}-${var.environment}-web-sg"
  description = "Allow HTTP/HTTPS from anywhere; SSH from restricted CIDR only."
  vpc_id      = module.network.vpc_id

  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "SSH — restricted; override var.ssh_cidr carefully"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.ssh_cidr]
  }

  egress {
    description = "Allow all outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, {
    Name = "${var.project}-${var.environment}-web-sg"
  })
}
