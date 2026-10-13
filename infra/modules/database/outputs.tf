output "table_name" {
  description = "DynamoDB table name."
  value       = aws_dynamodb_table.this.name
}

output "table_arn" {
  description = "DynamoDB table ARN."
  value       = aws_dynamodb_table.this.arn
}

output "stream_arn" {
  description = "Stream ARN for the TASK-011 publisher."
  value       = aws_dynamodb_table.this.stream_arn
}
