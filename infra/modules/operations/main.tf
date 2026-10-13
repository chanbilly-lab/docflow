resource "aws_iam_role" "monitor" {
  name               = "${var.name_prefix}-operations-monitor"
  assume_role_policy = jsonencode({ Version = "2012-10-17", Statement = [{ Effect = "Allow", Principal = { Service = "lambda.amazonaws.com" }, Action = "sts:AssumeRole" }] })
}
resource "aws_iam_role_policy" "monitor" {
  role = aws_iam_role.monitor.id
  policy = jsonencode({ Version = "2012-10-17", Statement = [
    { Effect = "Allow", Action = ["logs:CreateLogStream", "logs:PutLogEvents"], Resource = "${var.log_group_arn}:*" },
    { Effect = "Allow", Action = ["dynamodb:Scan"], Resource = var.table_arn, Condition = {
      "ForAllValues:StringEquals" = { "dynamodb:Attributes" = ["entityType", "status", "createdAt", "workflowStartStatus", "workflowSubmittedAt", "updatedAt"] },
      StringEquals                = { "dynamodb:Select" = "SPECIFIC_ATTRIBUTES" }
    } },
    { Effect = "Allow", Action = ["xray:PutTraceSegments", "xray:PutTelemetryRecords"], Resource = "*" }
  ] })
}
resource "aws_lambda_function" "monitor" {
  function_name                  = "${var.name_prefix}-operations-monitor"
  role                           = aws_iam_role.monitor.arn
  runtime                        = "python3.13"
  architectures                  = ["arm64"]
  handler                        = "operations_monitor.handler.handler"
  filename                       = var.archive_path
  source_code_hash               = filebase64sha256(var.archive_path)
  timeout                        = 60
  memory_size                    = 128
  reserved_concurrent_executions = 1
  tracing_config { mode = "Active" }
  environment { variables = { TABLE_NAME = var.table_name } }
  depends_on = [aws_iam_role_policy.monitor]
}
resource "aws_cloudwatch_event_rule" "monitor" {
  name                = "${var.name_prefix}-operations-monitor"
  schedule_expression = "rate(5 minutes)"
}
resource "aws_cloudwatch_event_target" "monitor" {
  rule = aws_cloudwatch_event_rule.monitor.name
  arn  = aws_lambda_function.monitor.arn
  retry_policy {
    maximum_event_age_in_seconds = 300
    maximum_retry_attempts       = 2
  }
}
resource "aws_lambda_permission" "monitor" {
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.monitor.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.monitor.arn
}
