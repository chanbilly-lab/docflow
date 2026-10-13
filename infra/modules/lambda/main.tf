resource "aws_iam_role" "this" {
  name = "${var.function_name}-execution"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "logs" {
  name = "write-own-logs"
  role = aws_iam_role.this.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["logs:CreateLogStream", "logs:PutLogEvents"]
      Resource = "${var.log_group_arn}:*"
    }]
  })
}

resource "aws_lambda_function" "this" {
  tracing_config { mode = "Active" }
  function_name    = var.function_name
  role             = aws_iam_role.this.arn
  runtime          = "python3.13"
  handler          = var.handler
  architectures    = ["arm64"]
  filename         = var.archive_path
  source_code_hash = filebase64sha256(var.archive_path)
  memory_size      = 128
  timeout          = contains(["processor", "publisher", "command", "review_creator"], var.access_mode) ? 60 : (var.access_mode == "none" ? 3 : 10)
  publish          = false
  depends_on       = [aws_iam_role_policy.tracing, aws_iam_role_policy.logs, aws_iam_role_policy.database, aws_iam_role_policy.storage, aws_iam_role_policy.processor, aws_iam_role_policy.outbox, aws_iam_role_policy.workflow_start, aws_iam_role_policy.review_callback]
  environment {
    variables = merge(var.access_mode == "none" ? {} : { TABLE_NAME = var.table_name }, contains(["document", "processor"], var.access_mode) ? { DOCUMENT_BUCKET = var.document_bucket_name } : {}, var.access_mode == "publisher" ? { DOMAIN_BUS_ARN = var.domain_bus_arn } : {}, var.workflow_enabled ? { WORKFLOW_ARN = var.workflow_arn } : {})
  }
}

resource "aws_iam_role_policy" "tracing" {
  role   = aws_iam_role.this.id
  name   = "trace-telemetry"
  policy = jsonencode({ Version = "2012-10-17", Statement = [{ Effect = "Allow", Action = ["xray:PutTraceSegments", "xray:PutTelemetryRecords"], Resource = "*" }] })
}
