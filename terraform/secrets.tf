# Define the adzuna_app_id secret
resource "aws_secretsmanager_secret" "adzuna_app_id" {
  name        = var.prefix != "" ? "${var.prefix}/adzuna_app_id" : "adzuna_app_id"
  description = "Managed by Terraform"
}

resource "aws_secretsmanager_secret_version" "adzuna_app_id_version" {
  secret_id     = aws_secretsmanager_secret.adzuna_app_id.id
  secret_string = var.secrets["adzuna_app_id"]
}

# Define the adzuna_app_key secret
resource "aws_secretsmanager_secret" "adzuna_app_key" {
  name        = var.prefix != "" ? "${var.prefix}/adzuna_app_key" : "adzuna_app_key"
  description = "Managed by Terraform"
}

resource "aws_secretsmanager_secret_version" "adzuna_app_key_version" {
  secret_id     = aws_secretsmanager_secret.adzuna_app_key.id
  secret_string = var.secrets["adzuna_app_key"]
}

# This local variable now safely collects the ARNs from the explicitly defined resources
locals {
  secret_arn_patterns = [
    replace(aws_secretsmanager_secret.adzuna_app_id.arn, "/secret:[^:]+$/", "secret:*"),
    replace(aws_secretsmanager_secret.adzuna_app_key.arn, "/secret:[^:]+$/", "secret:*"),
  ]
}