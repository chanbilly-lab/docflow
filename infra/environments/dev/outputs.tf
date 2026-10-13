output "table_name" {
  description = "Database table_name for future backend configuration and IAM."
  value       = module.database.table_name
}

output "table_arn" {
  description = "Database table_arn for future backend configuration and IAM."
  value       = module.database.table_arn
}

output "stream_arn" {
  description = "Database stream_arn for future backend configuration and IAM."
  value       = module.database.stream_arn
}

output "log_group_names" {
  description = "Pre-created log_group_names, keyed by name, for later service integrations."
  value       = module.observability.log_group_names
}

output "log_group_arns" {
  description = "Pre-created log_group_arns, keyed by name, for later service integrations."
  value       = module.observability.log_group_arns
}
