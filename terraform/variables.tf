variable "region" {
  description = "The AWS region where resources will be created."
  type        = string
  default     = "eu-central-1"
}

variable "prefix" {
  description = "A prefix to add to all resource names (e.g., 'dev', 'prod')."
  type        = string
  default     = "dev"
}

variable "secrets" {
  description = "A map of secret names to their values for AWS Secrets Manager."
  type        = map(string)
  sensitive   = true
  default     = {}
}

variable "lambda_image_uri" {
  description = "The full URI of the Docker image in ECR for the Lambda function."
  type        = string
}

variable "lambda_env" {
  description = "A map of extra environment variables to pass to the Lambda function."
  type        = map(string)
  default     = {}
}

variable "schedule_expression" {
  description = "The EventBridge schedule expression (e.g., 'rate(24 hours)'). Leave empty to disable."
  type        = string
  default     = ""
}

variable "lambda_matcher_image_uri" {
  description = "The full URI of the Docker image in ECR for the job-matcher function."
  type        = string
}

variable "lambda_user_api_image_uri" {
  description = "The full URI of the Docker image in ECR for the user-api function."
  type        = string
}

variable "lambda_cv_upload_image_uri" {
  description = "The full URI of the Docker image in ECR for the cv-upload function."
  type        = string
}

