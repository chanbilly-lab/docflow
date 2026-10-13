output "queue_arn" { value = aws_sqs_queue.processing.arn }
output "queue_url" { value = aws_sqs_queue.processing.id }
output "queue_name" { value = aws_sqs_queue.processing.name }
output "dlq_arn" { value = aws_sqs_queue.dead_letter.arn }
output "dlq_url" { value = aws_sqs_queue.dead_letter.id }
output "rule_arn" { value = aws_cloudwatch_event_rule.created.arn }
output "visibility_timeout_seconds" { value = aws_sqs_queue.processing.visibility_timeout_seconds }

output "dlq_name" { value = aws_sqs_queue.dead_letter.name }
