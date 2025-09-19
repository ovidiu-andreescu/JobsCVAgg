output "secret_names" {
  description = "Created secret names"
  # FIX: Reference the two secret resources directly by name.
  value = [
    aws_secretsmanager_secret.adzuna_app_id.name,
    aws_secretsmanager_secret.adzuna_app_key.name,
  ]
}

output "secret_arns" {
  description = "Created secret ARNs"
  # FIX: Create a map with the ARNs from the two secret resources.
  value = {
    adzuna_app_id  = aws_secretsmanager_secret.adzuna_app_id.arn
    adzuna_app_key = aws_secretsmanager_secret.adzuna_app_key.arn
  }
}

output "lambda_name" {
  value = aws_lambda_function.this.function_name
}

output "lambda_arn" {
  value = aws_lambda_function.this.arn
}

