resource "aws_iam_role_policy" "outbox" {
  count = var.access_mode == "publisher" ? 1 : 0
  name  = "publish-committed-outbox"
  role  = aws_iam_role.this.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      { Effect = "Allow", Action = ["dynamodb:DescribeStream", "dynamodb:GetRecords", "dynamodb:GetShardIterator"], Resource = var.outbox_stream_arn },
      { Effect = "Allow", Action = ["dynamodb:GetItem", "dynamodb:UpdateItem"], Resource = var.table_arn,
      Condition = { "ForAllValues:StringLike" = { "dynamodb:LeadingKeys" = ["CASE#*"] } } },
      { Effect = "Allow", Action = ["events:PutEvents", "events:DescribeEventBus"], Resource = var.domain_bus_arn },
      { Effect = "Allow", Action = ["dynamodb:ListStreams"], Resource = "*" }
    ]
  })
}
resource "aws_lambda_event_source_mapping" "outbox" {
  count                              = var.access_mode == "publisher" ? 1 : 0
  event_source_arn                   = var.outbox_stream_arn
  function_name                      = aws_lambda_function.this.arn
  starting_position                  = "TRIM_HORIZON"
  batch_size                         = 10
  maximum_batching_window_in_seconds = 0
  parallelization_factor             = 1
  maximum_retry_attempts             = -1
  maximum_record_age_in_seconds      = -1
  bisect_batch_on_function_error     = true
  function_response_types            = ["ReportBatchItemFailures"]
  enabled                            = var.outbox_stream_enabled
  filter_criteria {
    filter {
      pattern = jsonencode({
        eventName = ["INSERT", "MODIFY"]
        dynamodb  = { NewImage = { entityType = { S = ["OUTBOX"] }, status = { S = ["PENDING"] } } }
      })
    }
  }
  depends_on = [aws_iam_role_policy.outbox]
}
