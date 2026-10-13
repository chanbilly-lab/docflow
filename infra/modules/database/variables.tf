variable "environment" {
  description = "Logical environment used in the stable docflow-{env} table name."
  type        = string
  nullable    = false

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "deletion_protection_enabled" {
  description = "Require an explicit configuration change before deleting the table."
  type        = bool
  default     = true
  nullable    = false
}
