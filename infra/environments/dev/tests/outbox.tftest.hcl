mock_provider "aws" {}
run "publisher_contract" {
  command = plan
  module { source = "../../modules/lambda" }
  variables {
    function_name         = "docflow-dev-outbox-publisher"
    log_group_arn         = "arn:aws:logs:us-east-1:123456789012:log-group:/aws/lambda/docflow-dev-outbox-publisher"
    archive_path          = "../../../build/cases.zip"
    handler               = "outbox_publisher.handler.handler"
    table_name            = "docflow-dev"
    table_arn             = "arn:aws:dynamodb:us-east-1:123456789012:table/docflow-dev"
    access_mode           = "publisher"
    domain_bus_arn        = "arn:aws:events:us-east-1:123456789012:event-bus/docflow-dev-domain"
    outbox_stream_arn     = "arn:aws:dynamodb:us-east-1:123456789012:table/docflow-dev/stream/2026-09-16T00:00:00.000"
    outbox_stream_enabled = true
  }
  assert {
    condition     = aws_lambda_function.this.handler == "outbox_publisher.handler.handler" && aws_lambda_function.this.timeout == 60 && aws_lambda_function.this.environment[0].variables.DOMAIN_BUS_ARN == var.domain_bus_arn
    error_message = "Publisher needs its handler, bounded timeout and explicit custom bus."
  }
  assert {
    condition = jsondecode(one(aws_lambda_event_source_mapping.outbox[0].filter_criteria[0].filter).pattern) == {
      eventName = ["INSERT", "MODIFY"]
      dynamodb  = { NewImage = { entityType = { S = ["OUTBOX"] }, status = { S = ["PENDING"] } } }
    }
    error_message = "Only inserted/modified PENDING outbox rows can trigger publication."
  }
  assert {
    condition     = aws_lambda_event_source_mapping.outbox[0].starting_position == "TRIM_HORIZON" && aws_lambda_event_source_mapping.outbox[0].batch_size == 10 && aws_lambda_event_source_mapping.outbox[0].parallelization_factor == 1 && aws_lambda_event_source_mapping.outbox[0].maximum_retry_attempts == -1 && aws_lambda_event_source_mapping.outbox[0].maximum_record_age_in_seconds == -1 && aws_lambda_event_source_mapping.outbox[0].bisect_batch_on_function_error && contains(aws_lambda_event_source_mapping.outbox[0].function_response_types, "ReportBatchItemFailures") && aws_lambda_event_source_mapping.outbox[0].enabled
    error_message = "Use retained stream start and partial failures with retry until stream expiry."
  }
  assert {
    condition = length(aws_iam_role_policy.database) == 0 && length(aws_iam_role_policy.storage) == 0 && length(aws_iam_role_policy.processor) == 0 && jsondecode(aws_iam_role_policy.outbox[0].policy).Statement == [
      { Effect = "Allow", Action = ["dynamodb:DescribeStream", "dynamodb:GetRecords", "dynamodb:GetShardIterator"], Resource = var.outbox_stream_arn },
      { Effect = "Allow", Action = ["dynamodb:GetItem", "dynamodb:UpdateItem"], Resource = var.table_arn, Condition = { "ForAllValues:StringLike" = { "dynamodb:LeadingKeys" = ["CASE#*"] } } },
      { Effect = "Allow", Action = ["events:PutEvents", "events:DescribeEventBus"], Resource = var.domain_bus_arn },
      { Effect = "Allow", Action = ["dynamodb:ListStreams"], Resource = "*" }
    ]
    error_message = "Publisher must have only exact stream/table/bus grants, no command or S3 grants."
  }
}
run "publisher_dev_wiring" {
  command = plan
  assert {
    condition     = module.outbox_publisher.function_name == "docflow-dev-outbox-publisher" && module.outbox_publisher.outbox_stream_enabled
    error_message = "Dev publisher ingestion is enabled after TASK-012 bus wiring."
  }
}
