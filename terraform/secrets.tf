locals {
  secret_names = {
    for name, value in var.secrets :
    name => var.prefix != "" ? "${var.prefix}/${name}" : name
  }
}
resource "aws_secretsmanager_secret" "secret" {
  for_each = local.secret_names

  name        = each.value
  description = "Managed by Terraform"
  kms_key_id  = var.kms_key_id
}

resource "aws_secretsmanager_secret_version" "version" {
  for_each = var.secrets
  secret_id     = aws_secretsmanager_secret.secret[each.key].id
  secret_string = each.value
}