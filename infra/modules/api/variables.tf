variable "name_prefix" { type = string }
variable "client_id" { type = string }
variable "issuer" { type = string }
variable "lambda_invoke_arn" { type = string }
variable "lambda_function_name" { type = string }
variable "log_group_arn" { type = string }

variable "command_function_name" {
  type    = string
  default = null
}
variable "command_invoke_arn" {
  type    = string
  default = null
}

variable "document_function_name" {
  type    = string
  default = null
}
variable "document_invoke_arn" {
  type    = string
  default = null
}
variable "browser_origins" {
  type    = list(string)
  default = []
}

variable "review_function_name" {
  type    = string
  default = null
}
variable "review_invoke_arn" {
  type    = string
  default = null
}

variable "review_command_function_name" {
  type    = string
  default = null
}
variable "review_command_invoke_arn" {
  type    = string
  default = null
}
