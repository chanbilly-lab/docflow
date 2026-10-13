variable "name_prefix" { type = string }
variable "region" { type = string }
variable "table_name" { type = string }
variable "table_arn" { type = string }
variable "log_group_arn" { type = string }
variable "archive_path" { type = string }
variable "workflow_arn" { type = string }
variable "function_names" { type = set(string) }
variable "dlq_names" { type = set(string) }
variable "alarm_action_arns" {
  type    = list(string)
  default = []
  validation {
    condition     = alltrue([for arn in var.alarm_action_arns : can(regex("^arn:aws[a-z-]*:sns:[a-z0-9-]+:[0-9]{12}:[A-Za-z0-9_-]+$", arn))])
    error_message = "Use existing approved SNS topic ARNs only."
  }
}

variable "event_rule_dimensions" {
  type    = map(map(string))
  default = {}
}
