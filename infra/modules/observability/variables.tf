variable "log_group_names" {
  description = "Exact service log group names owned by this module."
  type        = set(string)
  nullable    = false
}

variable "retention_in_days" {
  description = "Supported finite CloudWatch Logs retention; indefinite retention is excluded."
  type        = number
  default     = 14
  nullable    = false

  validation {
    condition = contains([
      1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731,
      1096, 1827, 2192, 2557, 2922, 3288, 3653,
    ], var.retention_in_days)
    error_message = "Choose a supported, nonzero CloudWatch Logs retention period in days."
  }
}
