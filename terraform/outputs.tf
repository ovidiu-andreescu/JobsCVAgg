output "lambda_function_name" {
  description = "The name of the created Lambda function."
  value       = aws_lambda_function.this.function_name
}

output "lambda_function_arn" {
  description = "The ARN of the created Lambda function."
  value       = aws_lambda_function.this.arn
}

output "dynamodb_table_name" {
  description = "The name of the created DynamoDB table."
  value       = aws_dynamodb_table.jobs.name
}

output "secret_arns" {
  description = "The ARNs of the created secrets in Secrets Manager."
  value = {
    adzuna_app_id  = aws_secretsmanager_secret.adzuna_app_id.arn
    adzuna_app_key = aws_secretsmanager_secret.adzuna_app_key.arn
  }
}

