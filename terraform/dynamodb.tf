resource "aws_dynamodb_table" "jobs" {
    name = var.prefix != "" ? "${var.prefix}-jobs": "jobs"
    billing_mode   = "PAY_PER_REQUEST"

  attribute {
    name = "source"
    type = "S"
  }

  attribute {
    name = "source_job_id"
    type = "S"
  }

  tags = {
    Project     = "JobAggregator"
    ManagedBy   = "Terraform"
  }
}