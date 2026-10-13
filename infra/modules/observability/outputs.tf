output "log_group_names" {
  description = "Log group names keyed by their configured service name."
  value       = { for name, group in aws_cloudwatch_log_group.this : name => group.name }
}

output "log_group_arns" {
  description = "Log group ARNs keyed by their configured service name."
  value       = { for name, group in aws_cloudwatch_log_group.this : name => group.arn }
}
