resource "aws_dynamodb_table" "jobs" {
  name           = var.prefix != "" ? "${var.prefix}-jobs" : "jobs"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "source_job_id" # A unique ID from the source API

  attribute {
    name = "source_job_id"
    type = "S" # S for String
  }

  tags = {
    Project     = "JobAggregator"
    ManagedBy   = "Terraform"
  }
}
