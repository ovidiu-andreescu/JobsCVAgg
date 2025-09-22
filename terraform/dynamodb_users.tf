resource "aws_dynamodb_table" "users" {
  name         = var.prefix != "" ? "${var.prefix}-users" : "users"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "email"

  attribute {
    name = "email"
    type = "S"
  }
  attribute {
    name = "token"
    type = "S"
  }

  global_secondary_index {
    name            = "token-index"
    hash_key        = "token"
    projection_type = "ALL"
  }

  tags = { Project = "JobAggregator", ManagedBy = "Terraform" }
}
