variable "name_prefix" { type = string }
variable "allowed_origins" {
  type = list(string)
  validation {
    condition = length(var.allowed_origins) > 0 && alltrue([
      for origin in var.allowed_origins : !strcontains(origin, "*") && can(regex("^https?://[^/]+$", origin))
    ])
    error_message = "Specify exact browser origins without wildcards or paths."
  }
}
