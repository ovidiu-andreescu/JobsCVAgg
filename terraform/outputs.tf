output "lambda_function_name" {
  description = "The name of the created Lambda function."
  value       = aws_lambda_function.aggregator.function_name
}

output "lambda_function_arn" {
  description = "The ARN of the created Lambda function."
  value       = aws_lambda_function.aggregator.arn
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
    jwt_secret_arn = aws_secretsmanager_secret.jwt_secret.arn
  }
}

output "matcher_api_endpoint_url" {
  description = "The invocation URL for the Job Matcher API."
  value       = aws_apigatewayv2_api.matcher.api_endpoint
}

output "user_api_endpoint" {
  description = "The invocation URL for the User API."
  value       = aws_apigatewayv2_api.user_api.api_endpoint
}

output "bucket_name" {
  value = aws_s3_bucket.cv_uploads.bucket
  description = "S3 bucket for CV PDFs + keywords JSON"
}

output "cv_api_endpoint" {
  description = "Base invoke URL for the CV FastAPI (HTTP API v2)."
  value       = aws_apigatewayv2_api.cv_api.api_endpoint
}

