mock_provider "aws" {}
run "notification_disabled" {
  command = plan
  module { source = "../../modules/notifications" }
  variables {
    name_prefix     = "docflow-dev"
    domain_bus_name = "docflow-dev-domain"
    table_name      = "docflow-dev"
    table_arn       = "arn:aws:dynamodb:us-east-1:123456789012:table/docflow-dev"
    user_pool_id    = "us-east-1_example"
    user_pool_arn   = "arn:aws:cognito-idp:us-east-1:123456789012:userpool/us-east-1_example"
    log_group_arn   = "arn:aws:logs:us-east-1:123456789012:log-group:/aws/lambda/docflow-dev-notification-worker"
    archive_path    = "../../../build/cases.zip"
  }
  override_resource {
    target          = aws_sqs_queue.main
    override_during = plan
    values          = { arn = "arn:aws:sqs:us-east-1:123456789012:docflow-dev-notification" }
  }
  override_resource {
    target          = aws_sqs_queue.dlq
    override_during = plan
    values          = { arn = "arn:aws:sqs:us-east-1:123456789012:docflow-dev-notification-dlq" }
  }
  assert {
    condition     = length(aws_lambda_function.worker) == 0 && alltrue([for rule in aws_cloudwatch_event_rule.notification : rule.state == "DISABLED"])
    error_message = "No delivery without explicit approved email configuration."
  }
  assert {
    condition     = aws_sqs_queue.main.visibility_timeout_seconds == 360 && aws_sqs_queue.main.message_retention_seconds == 345600 && aws_sqs_queue.dlq.message_retention_seconds == 1209600 && aws_sqs_queue.main.sqs_managed_sse_enabled && jsondecode(aws_sqs_queue.main.redrive_policy).maxReceiveCount == 5 && jsondecode(aws_sqs_queue_redrive_allow_policy.dlq.redrive_allow_policy).redrivePermission == "byQueue"
    error_message = "Encrypted queues and bounded retry/DLQ required."
  }
}
run "notification_enabled" {
  command = plan
  module { source = "../../modules/notifications" }
  variables {
    name_prefix     = "docflow-dev"
    domain_bus_name = "docflow-dev-domain"
    table_name      = "docflow-dev"
    table_arn       = "arn:aws:dynamodb:us-east-1:123456789012:table/docflow-dev"
    user_pool_id    = "us-east-1_example"
    user_pool_arn   = "arn:aws:cognito-idp:us-east-1:123456789012:userpool/us-east-1_example"
    log_group_arn   = "arn:aws:logs:us-east-1:123456789012:log-group:/aws/lambda/docflow-dev-notification-worker"
    archive_path    = "../../../build/cases.zip"
    email_config    = { sender = "sender@example.com", reviewer = "reviewers@example.com", identity_arn = "arn:aws:ses:us-east-1:123456789012:identity/example.com" }
  }
  override_resource {
    override_during = plan
    target          = aws_sqs_queue.main
    values          = { arn = "arn:aws:sqs:us-east-1:123456789012:docflow-dev-notification" }
  }
  override_resource {
    override_during = plan
    target          = aws_cloudwatch_event_rule.notification["review_ready"]
    values          = { arn = "arn:aws:events:us-east-1:123456789012:rule/docflow-dev-domain/ready" }
  }
  override_resource {
    override_during = plan
    target          = aws_cloudwatch_event_rule.notification["requester"]
    values          = { arn = "arn:aws:events:us-east-1:123456789012:rule/docflow-dev-domain/requester" }
  }
  assert {
    condition     = alltrue([for rule in aws_cloudwatch_event_rule.notification : rule.event_bus_name == var.domain_bus_name && rule.state == "ENABLED" && jsondecode(rule.event_pattern).source == ["docflow.case"]]) && jsondecode(aws_cloudwatch_event_rule.notification["review_ready"].event_pattern)["detail-type"] == ["CaseReadyForReview"] && toset(jsondecode(aws_cloudwatch_event_rule.notification["requester"].event_pattern)["detail-type"]) == toset(["CaseApproved", "CaseRejected", "AdditionalInformationRequested"])
    error_message = "Only four approved custom-bus facts route to email."
  }
  assert {
    condition     = alltrue([for target in aws_cloudwatch_event_target.notification : target.arn == aws_sqs_queue.main.arn && target.input == null && target.input_path == null]) && toset(jsondecode(aws_sqs_queue_policy.main.policy).Statement[0].Condition.ArnEquals["aws:SourceArn"]) == toset([for rule in aws_cloudwatch_event_rule.notification : rule.arn]) && jsondecode(aws_sqs_queue_policy.main.policy).Statement[1].Effect == "Deny"
    error_message = "Preserve envelope and exact-rule queue permission with TLS."
  }
  assert {
    condition     = aws_lambda_function.worker[0].timeout == 60 && aws_lambda_function.worker[0].handler == "notification_worker.handler.handler" && aws_lambda_event_source_mapping.worker[0].batch_size == 1 && aws_lambda_event_source_mapping.worker[0].function_response_types == toset(["ReportBatchItemFailures"])
    error_message = "Worker timeout/batch contract must match visibility and leases."
  }
  assert {
    condition     = jsondecode(aws_iam_role_policy.worker[0].policy).Statement[3].Action == ["dynamodb:PutItem", "dynamodb:UpdateItem"] && jsondecode(aws_iam_role_policy.worker[0].policy).Statement[3].Condition["ForAllValues:StringEquals"]["dynamodb:LeadingKeys"] == ["IDEMPOTENCY#notification-worker"] && jsondecode(aws_iam_role_policy.worker[0].policy).Statement[4].Resource == var.user_pool_arn && jsondecode(aws_iam_role_policy.worker[0].policy).Statement[5].Resource == var.email_config.identity_arn && jsondecode(aws_iam_role_policy.worker[0].policy).Statement[5].Condition.StringEquals["ses:FromAddress"] == var.email_config.sender
    error_message = "Only private receipts are writable; exact Cognito and sender SES identity grants."
  }
}
run "notification_invalid_config" {
  command = plan
  module { source = "../../modules/notifications" }
  variables {
    name_prefix     = "docflow-dev"
    domain_bus_name = "docflow-dev-domain"
    table_name      = "docflow-dev"
    table_arn       = "arn:aws:dynamodb:us-east-1:123456789012:table/docflow-dev"
    user_pool_id    = "us-east-1_example"
    user_pool_arn   = "arn:aws:cognito-idp:us-east-1:123456789012:userpool/us-east-1_example"
    log_group_arn   = "arn:aws:logs:us-east-1:123456789012:log-group:/aws/lambda/docflow-dev-notification-worker"
    archive_path    = "../../../build/cases.zip"
    email_config    = { sender = "bad", reviewer = "reviewers@example.com", identity_arn = "*" }
  }
  expect_failures = [var.email_config]
}
run "notification_dev" {
  command = plan
  assert {
    condition     = var.notification_email_config == null
    error_message = "Dev composes notifications without enabling sends."
  }
}
