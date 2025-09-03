output "secret_names" {
  description = "Created secret names"
  value       = [for s in aws_secretsmanager_secret.secret : s.name]
}

output "secret_arns" {
  description = "Created secret ARNs"
  value       = { for k, s in aws_secretsmanager_secret.secret : k => s.arn }
}
