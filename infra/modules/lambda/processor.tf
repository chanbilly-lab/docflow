resource "aws_iam_role_policy" "processor" {
  count = var.access_mode == "processor" ? 1 : 0
  name  = "document-processing"
  role  = aws_iam_role.this.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      { Effect = "Allow", Action = ["sqs:ReceiveMessage", "sqs:DeleteMessage", "sqs:GetQueueAttributes"], Resource = var.processing_queue_arn },
      { Effect = "Allow", Action = ["s3:GetObject", "s3:GetObjectVersion"], Resource = "${var.document_bucket_arn}/cases/*/documents/*/v*/source" },
      { Effect = "Allow", Action = ["dynamodb:GetItem"], Resource = var.table_arn,
      Condition = { "ForAllValues:StringLike" = { "dynamodb:LeadingKeys" = ["CASE#*", "IDEMPOTENCY#document-processor"] } } },
      { Effect = "Allow", Action = ["dynamodb:PutItem", "dynamodb:ConditionCheckItem"], Resource = var.table_arn,
        Condition = {
          "ForAllValues:StringLike"  = { "dynamodb:LeadingKeys" = ["CASE#*", "IDEMPOTENCY#document-processor"] }
          "ForAnyValue:StringEquals" = { "dynamodb:EnclosingOperation" = ["TransactWriteItems"] }
        }
      },
      { Effect = "Allow", Action = ["dynamodb:UpdateItem"], Resource = var.table_arn,
        Condition = {
          "ForAllValues:StringLike"  = { "dynamodb:LeadingKeys" = ["CASE#*"] }
          "ForAnyValue:StringEquals" = { "dynamodb:EnclosingOperation" = ["TransactWriteItems"] }
        }
      }
    ]
  })
}
resource "aws_lambda_event_source_mapping" "processor" {
  count                              = var.access_mode == "processor" ? 1 : 0
  event_source_arn                   = var.processing_queue_arn
  function_name                      = aws_lambda_function.this.arn
  batch_size                         = 5
  maximum_batching_window_in_seconds = 0
  function_response_types            = ["ReportBatchItemFailures"]
  enabled                            = true
  depends_on                         = [aws_iam_role_policy.processor]
}
