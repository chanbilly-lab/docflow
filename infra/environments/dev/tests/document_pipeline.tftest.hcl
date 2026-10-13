mock_provider "aws" {}

run "pipeline_contract" {
  command = plan
  module { source = "../../modules/document_pipeline" }
  variables {
    name_prefix = "docflow-dev"
    bucket_name = "docflow-dev-documents-test"
  }
  override_resource {
    target          = aws_sqs_queue.processing
    override_during = plan
    values = {
      id  = "https://sqs.us-east-1.amazonaws.com/123456789012/docflow-dev-document-processing"
      arn = "arn:aws:sqs:us-east-1:123456789012:docflow-dev-document-processing"
    }
  }
  override_resource {
    target          = aws_sqs_queue.dead_letter
    override_during = plan
    values = {
      id  = "https://sqs.us-east-1.amazonaws.com/123456789012/docflow-dev-document-processing-dlq"
      arn = "arn:aws:sqs:us-east-1:123456789012:docflow-dev-document-processing-dlq"
    }
  }
  override_resource {
    target          = aws_cloudwatch_event_rule.created
    override_during = plan
    values          = { arn = "arn:aws:events:us-east-1:123456789012:rule/docflow-dev-s3-document-created" }
  }
  assert {
    condition = (
      aws_cloudwatch_event_rule.created.event_bus_name == "default" &&
      aws_cloudwatch_event_rule.created.state == "ENABLED" &&
      jsondecode(aws_cloudwatch_event_rule.created.event_pattern) == {
        source      = ["aws.s3"]
        detail-type = ["Object Created"]
        detail = {
          bucket = { name = ["docflow-dev-documents-test"] }
          object = { key = [{ prefix = "cases/" }] }
        }
      }
    )
    error_message = "Only the configured bucket's cases/ Object Created facts may match on the default bus."
  }
  assert {
    condition = (
      aws_sqs_queue.processing.name == "docflow-dev-document-processing" &&
      aws_sqs_queue.dead_letter.name == "docflow-dev-document-processing-dlq" &&
      !aws_sqs_queue.processing.fifo_queue && !aws_sqs_queue.dead_letter.fifo_queue &&
      aws_sqs_queue.processing.sqs_managed_sse_enabled && aws_sqs_queue.dead_letter.sqs_managed_sse_enabled &&
      aws_sqs_queue.processing.visibility_timeout_seconds == 360 &&
      aws_sqs_queue.processing.message_retention_seconds == 345600 &&
      aws_sqs_queue.dead_letter.message_retention_seconds == 1209600 &&
      aws_sqs_queue.processing.receive_wait_time_seconds == 20
    )
    error_message = "Queue type, encryption, visibility, retention and polling must match the design."
  }
  assert {
    condition = (
      jsondecode(aws_sqs_queue.processing.redrive_policy) == {
        deadLetterTargetArn = aws_sqs_queue.dead_letter.arn, maxReceiveCount = 5
      } &&
      jsondecode(aws_sqs_queue_redrive_allow_policy.dead_letter.redrive_allow_policy) == {
        redrivePermission = "byQueue", sourceQueueArns = [aws_sqs_queue.processing.arn]
      }
    )
    error_message = "Only this source queue may redrive to the processing DLQ after five receives."
  }
  assert {
    condition = (
      length(jsondecode(aws_sqs_queue_policy.processing.policy).Statement) == 2 &&
      jsondecode(aws_sqs_queue_policy.processing.policy).Statement[0] == {
        Sid       = "AllowDocumentRule"
        Effect    = "Allow"
        Principal = { Service = "events.amazonaws.com" }
        Action    = "sqs:SendMessage"
        Resource  = aws_sqs_queue.processing.arn
        Condition = { ArnEquals = { "aws:SourceArn" = aws_cloudwatch_event_rule.created.arn } }
      } &&
      jsondecode(aws_sqs_queue_policy.processing.policy).Statement[1].Effect == "Deny" &&
      jsondecode(aws_sqs_queue_policy.processing.policy).Statement[1].Condition.Bool["aws:SecureTransport"] == "false" &&
      length(jsondecode(aws_sqs_queue_policy.dead_letter.policy).Statement) == 1 &&
      jsondecode(aws_sqs_queue_policy.dead_letter.policy).Statement[0].Effect == "Deny" &&
      jsondecode(aws_sqs_queue_policy.dead_letter.policy).Statement[0].Condition.Bool["aws:SecureTransport"] == "false"
    )
    error_message = "Only the exact EventBridge rule receives SendMessage permission; require TLS."
  }
  assert {
    condition = (
      aws_cloudwatch_event_target.processing.arn == aws_sqs_queue.processing.arn &&
      aws_cloudwatch_event_target.processing.rule == aws_cloudwatch_event_rule.created.name &&
      aws_cloudwatch_event_target.processing.event_bus_name == "default" &&
      aws_cloudwatch_event_target.processing.input == null &&
      aws_cloudwatch_event_target.processing.input_path == null &&
      length(aws_cloudwatch_event_target.processing.input_transformer) == 0 &&
      length(aws_cloudwatch_event_target.processing.dead_letter_config) == 0 &&
      aws_cloudwatch_event_target.processing.retry_policy[0].maximum_event_age_in_seconds == 86400 &&
      aws_cloudwatch_event_target.processing.retry_policy[0].maximum_retry_attempts == 185
    )
    error_message = "Preserve full raw events; delivery retry and SQS processing redrive are separate."
  }
}

run "dev_notification_wiring" {
  command = plan
  override_module {
    target  = module.documents
    outputs = { bucket_name = "docflow-dev-documents-test", bucket_arn = "arn:aws:s3:::docflow-dev-documents-test" }
  }
  assert {
    condition = (
      aws_s3_bucket_notification.documents.bucket == "docflow-dev-documents-test" &&
      aws_s3_bucket_notification.documents.eventbridge &&
      length(aws_s3_bucket_notification.documents.queue) == 0 &&
      length(aws_s3_bucket_notification.documents.topic) == 0 &&
      length(aws_s3_bucket_notification.documents.lambda_function) == 0 &&
      module.document_pipeline.queue_name == "docflow-dev-document-processing" &&
      module.document_pipeline.visibility_timeout_seconds == 360
    )
    error_message = "Enable EventBridge on the actual document bucket, without bypassing it with direct notifications."
  }
}
