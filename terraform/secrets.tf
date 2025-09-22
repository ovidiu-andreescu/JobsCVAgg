resource "aws_secretsmanager_secret" "adzuna_app_id" {
  name        = var.prefix != "" ? "${var.prefix}/adzuna_app_id" : "adzuna_app_id"
  description = "Adzuna Application ID, managed by Terraform."
}

resource "aws_secretsmanager_secret_version" "adzuna_app_id_version" {
  secret_id     = aws_secretsmanager_secret.adzuna_app_id.id
  secret_string = var.secrets["adzuna_app_id"]
}

resource "aws_secretsmanager_secret" "adzuna_app_key" {
  name        = var.prefix != "" ? "${var.prefix}/adzuna_app_key" : "adzuna_app_key"
  description = "Adzuna Application KEY, managed by Terraform."
}

resource "aws_secretsmanager_secret_version" "adzuna_app_key_version" {
  secret_id     = aws_secretsmanager_secret.adzuna_app_key.id
  secret_string = var.secrets["adzuna_app_key"]
}

resource "aws_secretsmanager_secret" "cv_s3_bucket" {
  name        = var.prefix != "" ? "${var.prefix}/cv_s3_bucket" : "cv_s3_bucket"
  description = "CV S3 Bucket, managed by Terraform."
}

resource "aws_secretsmanager_secret" "jwt_secret" {
  name        = var.prefix != "" ? "${var.prefix}/jwt_secret" : "jwt_secret"
  description = "JWT secret for the user API."
}

resource "random_password" "jwt_secret_value" {
  length  = 48
  special = true
}

resource "aws_secretsmanager_secret_version" "jwt_secret_initial_version" {
  secret_id     = aws_secretsmanager_secret.jwt_secret.id
  secret_string = random_password.jwt_secret_value.result
}

locals {
  secret_arn_patterns = [
    replace(aws_secretsmanager_secret.adzuna_app_id.arn, "/secret:[^:]+$/", "secret:*"),
    replace(aws_secretsmanager_secret.adzuna_app_key.arn, "/secret:[^:]+$/", "secret:*"),
    replace(aws_secretsmanager_secret.cv_s3_bucket.arn,    "/secret:[^:]+$/", "secret:*"),
    replace(aws_secretsmanager_secret.jwt_secret.arn,      "/secret:[^:]+$/", "secret:*"),
  ]
}
