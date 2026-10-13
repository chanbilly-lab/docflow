resource "aws_iam_role" "worker" {
  count = var.email_config == null ? 0 : 1
  name  = "${var.name_prefix}-notification-worker"
  assume_role_policy = jsonencode({ Version = "2012-10-17", Statement = [
    { Effect = "Allow", Principal = { Service = "lambda.amazonaws.com" }, Action = "sts:AssumeRole" }
  ] })
}
resource "aws_iam_role_policy" "worker" {
  count = var.email_config == null ? 0 : 1
  name  = "notification-delivery"
  role  = aws_iam_role.worker[0].id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      { Effect = "Allow", Action = ["logs:CreateLogStream", "logs:PutLogEvents"], Resource = "${var.log_group_arn}:*" },
      { Effect = "Allow", Action = ["sqs:ReceiveMessage", "sqs:DeleteMessage", "sqs:GetQueueAttributes"], Resource = aws_sqs_queue.main.arn },
      { Effect = "Allow", Action = ["dynamodb:GetItem"], Resource = var.table_arn,
      Condition = { "ForAllValues:StringLike" = { "dynamodb:LeadingKeys" = ["CASE#*", "IDEMPOTENCY#notification-worker"] } } },
      { Effect = "Allow", Action = ["dynamodb:PutItem", "dynamodb:UpdateItem"], Resource = var.table_arn,
      Condition = { "ForAllValues:StringEquals" = { "dynamodb:LeadingKeys" = ["IDEMPOTENCY#notification-worker"] } } },
      { Effect = "Allow", Action = ["cognito-idp:ListUsers"], Resource = var.user_pool_arn },
      { Effect = "Allow", Action = ["ses:SendEmail"], Resource = var.email_config.identity_arn,
      Condition = { StringEquals = { "ses:FromAddress" = var.email_config.sender } } }
    ]
  })
}
resource "aws_lambda_function" "worker" {
  tracing_config { mode = "Active" }
  count            = var.email_config == null ? 0 : 1
  function_name    = "${var.name_prefix}-notification-worker"
  role             = aws_iam_role.worker[0].arn
  runtime          = "python3.13"
  architectures    = ["arm64"]
  handler          = "notification_worker.handler.handler"
  filename         = var.archive_path
  source_code_hash = filebase64sha256(var.archive_path)
  timeout          = 60
  memory_size      = 128
  environment {
    variables = { TABLE_NAME = var.table_name, USER_POOL_ID = var.user_pool_id,
    SENDER_EMAIL = var.email_config.sender, REVIEWER_EMAIL = var.email_config.reviewer }
  }
  depends_on = [aws_iam_role_policy.worker, aws_iam_role_policy.tracing]
}
resource "aws_lambda_event_source_mapping" "worker" {
  count                   = var.email_config == null ? 0 : 1
  event_source_arn        = aws_sqs_queue.main.arn
  function_name           = aws_lambda_function.worker[0].arn
  batch_size              = 1
  function_response_types = ["ReportBatchItemFailures"]
  enabled                 = true
}

resource "aws_iam_role_policy" "tracing" {
  count  = var.email_config == null ? 0 : 1
  role   = aws_iam_role.worker[0].id
  name   = "trace-telemetry"
  policy = jsonencode({ Version = "2012-10-17", Statement = [{ Effect = "Allow", Action = ["xray:PutTraceSegments", "xray:PutTelemetryRecords"], Resource = "*" }] })
}
