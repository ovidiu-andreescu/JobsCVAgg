variable "region" {
  description = "AWS region"
  type        = string
  default     = "eu-central-1"
}

variable "prefix" {
  description = "An optional prefix to add to all secret names."
  type        = string
  default     = "app/dev"
}

variable "secrets" {
  description = "Map of secret_name -> secret_value"
  type        = map(string)
  sensitive   = true
  default     = {}
}

variable "kms_key_id" {
  description = "The ARN of the KMS key to use for encrypting the secrets."
  type        = string
  default     = null
}

variable "lambda_image_uri" {
  type        = string
  description = "ECR image URI for Lambda (container-based). Leave empty if using zip."
  default     = ""
}
variable "lambda_zip_s3_bucket" {
  type        = string
  description = "S3 bucket with the Lambda zip (zip-based)."
  default     = ""
}
variable "lambda_zip_s3_key" {
  type        = string
  description = "S3 key for the Lambda zip (zip-based)."
  default     = ""
}

variable "lambda_env" {
  type        = map(string)
  description = "Extra environment variables for the Lambda (e.g., SECRETS_PREFIX, ADZUNA_COUNTRY)"
  default     = {}
}

variable "schedule_expression" {
  type        = string
  description = "EventBridge schedule expression, e.g. rate(30 minutes) or cron(...) . Leave empty to disable scheduler."
  default     = ""
}

