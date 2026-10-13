resource "aws_sqs_queue" "dead_letter" {
  name                      = "${var.name_prefix}-document-processing-dlq"
  fifo_queue                = false
  message_retention_seconds = 1209600
  receive_wait_time_seconds = 20
  sqs_managed_sse_enabled   = true
}
resource "aws_sqs_queue" "processing" {
  name                       = "${var.name_prefix}-document-processing"
  fifo_queue                 = false
  visibility_timeout_seconds = 360
  message_retention_seconds  = 345600
  receive_wait_time_seconds  = 20
  sqs_managed_sse_enabled    = true
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dead_letter.arn
    maxReceiveCount     = 5
  })
}
resource "aws_sqs_queue_redrive_allow_policy" "dead_letter" {
  queue_url = aws_sqs_queue.dead_letter.id
  redrive_allow_policy = jsonencode({
    redrivePermission = "byQueue"
    sourceQueueArns   = [aws_sqs_queue.processing.arn]
  })
}
resource "aws_cloudwatch_event_rule" "created" {
  name           = "${var.name_prefix}-s3-document-created"
  description    = "Route document-bucket Object Created facts under cases/ to processing."
  event_bus_name = "default"
  state          = "ENABLED"
  event_pattern  = templatefile("${path.module}/s3-created.json.tftpl", { bucket_name = var.bucket_name })
}
resource "aws_sqs_queue_policy" "processing" {
  queue_url = aws_sqs_queue.processing.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "AllowDocumentRule"
        Effect    = "Allow"
        Principal = { Service = "events.amazonaws.com" }
        Action    = "sqs:SendMessage"
        Resource  = aws_sqs_queue.processing.arn
        Condition = { ArnEquals = { "aws:SourceArn" = aws_cloudwatch_event_rule.created.arn } }
      },
      {
        Sid       = "RequireTLS"
        Effect    = "Deny"
        Principal = "*"
        Action    = "sqs:*"
        Resource  = aws_sqs_queue.processing.arn
        Condition = { Bool = { "aws:SecureTransport" = "false" } }
      }
    ]
  })
}
resource "aws_sqs_queue_policy" "dead_letter" {
  queue_url = aws_sqs_queue.dead_letter.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid       = "RequireTLS"
      Effect    = "Deny"
      Principal = "*"
      Action    = "sqs:*"
      Resource  = aws_sqs_queue.dead_letter.arn
      Condition = { Bool = { "aws:SecureTransport" = "false" } }
    }]
  })
}
resource "aws_cloudwatch_event_target" "processing" {
  rule           = aws_cloudwatch_event_rule.created.name
  event_bus_name = "default"
  target_id      = "document-processing"
  arn            = aws_sqs_queue.processing.arn
  retry_policy {
    maximum_event_age_in_seconds = 86400
    maximum_retry_attempts       = 185
  }
  # Preserve the entire AWS envelope. Processing retries/DLQ belong to SQS.
  depends_on = [
    aws_sqs_queue_policy.processing,
    aws_sqs_queue_policy.dead_letter,
    aws_sqs_queue_redrive_allow_policy.dead_letter
  ]
}
