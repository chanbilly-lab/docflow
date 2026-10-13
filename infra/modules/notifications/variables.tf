variable "name_prefix" { type = string }
variable "domain_bus_name" { type = string }
variable "table_name" { type = string }
variable "table_arn" { type = string }
variable "user_pool_id" { type = string }
variable "user_pool_arn" { type = string }
variable "log_group_arn" { type = string }
variable "archive_path" { type = string }
variable "email_config" {
  type        = object({ sender = string, reviewer = string, identity_arn = string })
  default     = null
  description = "Existing verified SES identity and approved addresses; null keeps delivery disabled."
  validation {
    condition = var.email_config == null ? true : (
      can(regex("^[^ @\\r\\n]+@[^ @\\r\\n]+\\.[^ @\\r\\n]+$", var.email_config.sender)) &&
      can(regex("^[^ @\\r\\n]+@[^ @\\r\\n]+\\.[^ @\\r\\n]+$", var.email_config.reviewer)) &&
      can(regex("^arn:aws[a-z-]*:ses:[a-z0-9-]+:[0-9]{12}:identity/[^*]+$", var.email_config.identity_arn))
    )
    error_message = "Use explicit email addresses and an exact existing SES identity ARN."
  }
}
