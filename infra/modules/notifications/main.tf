locals {
  routes = { review_ready = ["CaseReadyForReview"], requester = ["AdditionalInformationRequested", "CaseApproved", "CaseRejected"] }
}
resource "aws_sqs_queue" "dlq" {
  name                      = "${var.name_prefix}-notification-dlq"
  message_retention_seconds = 1209600
  receive_wait_time_seconds = 20
  sqs_managed_sse_enabled   = true
}
resource "aws_sqs_queue" "main" {
  name                       = "${var.name_prefix}-notification"
  visibility_timeout_seconds = 360
  message_retention_seconds  = 345600
  receive_wait_time_seconds  = 20
  sqs_managed_sse_enabled    = true
  redrive_policy             = jsonencode({ deadLetterTargetArn = aws_sqs_queue.dlq.arn, maxReceiveCount = 5 })
}
resource "aws_sqs_queue_redrive_allow_policy" "dlq" {
  queue_url            = aws_sqs_queue.dlq.id
  redrive_allow_policy = jsonencode({ redrivePermission = "byQueue", sourceQueueArns = [aws_sqs_queue.main.arn] })
}
resource "aws_cloudwatch_event_rule" "notification" {
  for_each       = local.routes
  name           = "${var.name_prefix}-notification-${each.key}"
  event_bus_name = var.domain_bus_name
  state          = var.email_config == null ? "DISABLED" : "ENABLED"
  event_pattern  = jsonencode({ source = ["docflow.case"], "detail-type" = each.value })
}
resource "aws_sqs_queue_policy" "main" {
  queue_url = aws_sqs_queue.main.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      { Effect   = "Allow", Principal = { Service = "events.amazonaws.com" }, Action = "sqs:SendMessage",
        Resource = aws_sqs_queue.main.arn,
      Condition = { ArnEquals = { "aws:SourceArn" = [for rule in aws_cloudwatch_event_rule.notification : rule.arn] } } },
      { Effect = "Deny", Principal = "*", Action = "sqs:*", Resource = aws_sqs_queue.main.arn,
      Condition = { Bool = { "aws:SecureTransport" = "false" } } }
    ]
  })
}
resource "aws_sqs_queue_policy" "dlq" {
  queue_url = aws_sqs_queue.dlq.id
  policy = jsonencode({ Version = "2012-10-17", Statement = [
    { Effect = "Deny", Principal = "*", Action = "sqs:*", Resource = aws_sqs_queue.dlq.arn,
    Condition = { Bool = { "aws:SecureTransport" = "false" } } }
  ] })
}
resource "aws_cloudwatch_event_target" "notification" {
  for_each       = aws_cloudwatch_event_rule.notification
  rule           = each.value.name
  event_bus_name = var.domain_bus_name
  target_id      = "notification"
  arn            = aws_sqs_queue.main.arn
  retry_policy {
    maximum_event_age_in_seconds = 86400
    maximum_retry_attempts       = 185
  }
  depends_on = [aws_sqs_queue_policy.main, aws_sqs_queue_policy.dlq, aws_sqs_queue_redrive_allow_policy.dlq]
}
output "queue_arn" { value = aws_sqs_queue.main.arn }
output "queue_url" { value = aws_sqs_queue.main.url }
output "dlq_arn" { value = aws_sqs_queue.dlq.arn }

output "dlq_name" { value = aws_sqs_queue.dlq.name }
