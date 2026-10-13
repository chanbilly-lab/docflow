variable "aws_region" {
  description = "AWS region for dev; matches the root environment example."
  type        = string
  default     = "us-east-1"
  nullable    = false
}

variable "log_retention_in_days" {
  description = "Finite CloudWatch retention for baseline dev log groups."
  type        = number
  default     = 14
  nullable    = false
}

variable "database_deletion_protection_enabled" {
  description = "Protect the table against deletion. Disable and apply deliberately before a later teardown."
  type        = bool
  default     = true
  nullable    = false
}
