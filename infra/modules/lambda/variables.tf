variable "function_name" {
  type = string
}
variable "log_group_arn" {
  type = string
}
variable "archive_path" {
  type = string
}

variable "handler" {
  type    = string
  default = "case_api.health.handler"
}
variable "table_name" {
  type    = string
  default = ""
}
variable "table_arn" {
  type    = string
  default = ""
}
variable "access_mode" {
  type    = string
  default = "none"
  validation {
    condition     = contains(["none", "query", "command", "document", "processor", "publisher", "workflow", "review_creator", "review_query", "review_command"], var.access_mode)
    error_message = "Use none, query, command, document, processor, publisher, workflow, review_creator, review_query or review_command access."
  }
}

variable "document_bucket_name" {
  type    = string
  default = ""
}
variable "document_bucket_arn" {
  type    = string
  default = ""
}

variable "processing_queue_arn" {
  type    = string
  default = ""
}

variable "domain_bus_arn" {
  type    = string
  default = ""
}
variable "outbox_stream_arn" {
  type    = string
  default = ""
}
variable "outbox_stream_enabled" {
  type    = bool
  default = false
}

variable "workflow_arn" {
  type    = string
  default = ""
}
variable "workflow_stream_arn" {
  type    = string
  default = ""
}
variable "workflow_enabled" {
  type    = bool
  default = false
}
