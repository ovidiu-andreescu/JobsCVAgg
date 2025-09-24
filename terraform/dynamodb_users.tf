resource "aws_dynamodb_table" "users" {
  name         = "${var.prefix}-users"
  billing_mode = "PAY_PER_REQUEST"

  hash_key = "email"

  attribute {
    name = "email"
    type = "S"
  }
  attribute {
    name = "verify_token"
    type = "S"
  }

  global_secondary_index {
    name            = "verify_token-index"
    hash_key        = "verify_token"
    projection_type = "ALL"
  }

  tags = {
    Project   = "JobAggregator"
    ManagedBy = "Terraform"
  }
}
