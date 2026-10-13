resource "aws_iam_role" "this" {
  name = "${var.name}-execution"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
    { Effect = "Allow", Principal = { Service = "states.amazonaws.com" }, Action = "sts:AssumeRole" }]
  })
}
resource "aws_iam_role_policy" "this" {
  role = aws_iam_role.this.id
  name = "workflow-tasks-and-logs"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      { Effect = "Allow", Action = ["lambda:InvokeFunction"], Resource = [var.validate_arn, var.failure_arn, var.review_arn, var.finalize_arn] },
      { Effect = "Allow", Action = ["logs:CreateLogDelivery", "logs:GetLogDelivery", "logs:UpdateLogDelivery", "logs:DeleteLogDelivery", "logs:ListLogDeliveries", "logs:PutResourcePolicy", "logs:DescribeResourcePolicies", "logs:DescribeLogGroups"], Resource = "*" },
      { Effect = "Allow", Action = ["xray:PutTraceSegments", "xray:PutTelemetryRecords", "xray:GetSamplingRules", "xray:GetSamplingTargets"], Resource = "*" }
    ]
  })
}
resource "aws_sfn_state_machine" "this" {
  tracing_configuration { enabled = true }
  name       = var.name
  role_arn   = aws_iam_role.this.arn
  type       = "STANDARD"
  definition = templatefile("${path.module}/definition.asl.json", { validate_arn = var.validate_arn, failure_arn = var.failure_arn, review_arn = var.review_arn, finalize_arn = var.finalize_arn })
  logging_configuration {
    log_destination        = "${var.log_group_arn}:*"
    include_execution_data = false
    level                  = "ERROR"
  }
  depends_on = [aws_iam_role_policy.this]
}
output "arn" { value = aws_sfn_state_machine.this.arn }
output "definition" { value = aws_sfn_state_machine.this.definition }
