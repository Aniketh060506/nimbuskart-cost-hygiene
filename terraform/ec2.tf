# ---------------------------------------------------------------------------
# EC2 Web Tier — two t3.micro instances across the two public subnets
# ---------------------------------------------------------------------------

# Use a data source for the AMI so it stays dynamic.
# LocalStack accepts any AMI ID; this resolves to Amazon Linux 2 in us-east-1.
data "aws_ami" "amazon_linux_2" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

resource "aws_instance" "web" {
  count = var.web_instance_count

  ami                    = data.aws_ami.amazon_linux_2.id
  instance_type          = var.instance_type
  subnet_id              = module.network.public_subnet_ids[count.index]
  vpc_security_group_ids = [aws_security_group.web.id]

  # No key pair is provisioned here intentionally — SSH access is controlled
  # at the security group level and key management is out of scope for this
  # staging baseline. See README "Decisions & deviations".

  tags = merge(local.common_tags, {
    Name = "${var.project}-${var.environment}-web-${count.index + 1}"
    Tier = "web"
  })
}
