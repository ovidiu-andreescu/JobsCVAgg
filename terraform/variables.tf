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