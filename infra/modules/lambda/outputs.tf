output "function_name" {
  value = aws_lambda_function.this.function_name
}
output "invoke_arn" {
  value = aws_lambda_function.this.invoke_arn
}

output "outbox_stream_enabled" {
  value = var.access_mode == "publisher" ? aws_lambda_event_source_mapping.outbox[0].enabled : false
}

output "domain_bus_arn" {
  value = var.access_mode == "publisher" ? aws_lambda_function.this.environment[0].variables.DOMAIN_BUS_ARN : null
}

output "function_arn" { value = aws_lambda_function.this.arn }
