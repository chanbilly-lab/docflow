locals {
  gauges = {
    OutboxPendingAgeSeconds        = 900
    WorkflowStartPendingAgeSeconds = 300
  }
  failures = {
    OutboxPublishFailures      = "outbox-publisher"
    NotificationFailures       = "notification-worker"
    DocumentProcessingFailures = "document-processor"
    WorkflowFailures           = "outbox-publisher"
  }
}
resource "aws_cloudwatch_metric_alarm" "dlq" {
  for_each            = var.dlq_names
  alarm_name          = "${each.value}-not-empty"
  namespace           = "AWS/SQS"
  metric_name         = "ApproximateNumberOfMessagesVisible"
  dimensions          = { QueueName = each.value }
  statistic           = "Maximum"
  period              = 60
  evaluation_periods  = 1
  comparison_operator = "GreaterThanThreshold"
  threshold           = 0
  treat_missing_data  = "notBreaching"
  alarm_actions       = var.alarm_action_arns
}
resource "aws_cloudwatch_metric_alarm" "workflow" {
  for_each            = toset(["ExecutionsFailed", "ExecutionsTimedOut", "ExecutionsAborted"])
  alarm_name          = "${var.name_prefix}-${each.value}"
  namespace           = "AWS/States"
  metric_name         = each.value
  dimensions          = { StateMachineArn = var.workflow_arn }
  statistic           = "Sum"
  period              = 60
  evaluation_periods  = 1
  comparison_operator = "GreaterThanThreshold"
  threshold           = 0
  treat_missing_data  = "notBreaching"
  alarm_actions       = var.alarm_action_arns
}
resource "aws_cloudwatch_metric_alarm" "pending" {
  for_each            = local.gauges
  alarm_name          = "${var.name_prefix}-${each.key}"
  namespace           = "DocFlow"
  metric_name         = each.key
  dimensions          = { service = "operations-monitor" }
  statistic           = "Maximum"
  period              = 300
  evaluation_periods  = 1
  comparison_operator = "GreaterThanThreshold"
  threshold           = each.value
  treat_missing_data  = "missing"
  alarm_actions       = var.alarm_action_arns
}
resource "aws_cloudwatch_metric_alarm" "heartbeat" {
  alarm_name          = "${var.name_prefix}-monitor-missing"
  namespace           = "DocFlow"
  metric_name         = "MonitorSuccess"
  dimensions          = { service = "operations-monitor" }
  statistic           = "Sum"
  period              = 300
  evaluation_periods  = 3
  comparison_operator = "LessThanThreshold"
  threshold           = 1
  treat_missing_data  = "breaching"
  alarm_actions       = var.alarm_action_arns
}
resource "aws_cloudwatch_metric_alarm" "retries" {
  for_each            = local.failures
  alarm_name          = "${var.name_prefix}-${each.key}"
  namespace           = "DocFlow"
  metric_name         = each.key
  dimensions          = { service = each.value }
  statistic           = "Sum"
  period              = 300
  evaluation_periods  = 1
  comparison_operator = "GreaterThanThreshold"
  threshold           = 0
  treat_missing_data  = "notBreaching"
  alarm_actions       = var.alarm_action_arns
}
resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  for_each            = var.function_names
  alarm_name          = "${each.value}-error-rate"
  comparison_operator = "GreaterThanThreshold"
  threshold           = 5
  evaluation_periods  = 1
  treat_missing_data  = "notBreaching"
  alarm_actions       = var.alarm_action_arns
  metric_query {
    id          = "rate"
    expression  = "IF(invocations>=10,100*errors/invocations,0)"
    label       = "Error percentage (minimum 10 invocations)"
    return_data = true
  }
  metric_query {
    id = "errors"
    metric {
      namespace   = "AWS/Lambda"
      metric_name = "Errors"
      period      = 300
      stat        = "Sum"
      dimensions  = { FunctionName = each.value }
    }
  }
  metric_query {
    id = "invocations"
    metric {
      namespace   = "AWS/Lambda"
      metric_name = "Invocations"
      period      = 300
      stat        = "Sum"
      dimensions  = { FunctionName = each.value }
    }
  }
}
resource "aws_cloudwatch_metric_alarm" "target_delivery" {
  for_each            = merge(var.event_rule_dimensions, { monitor = { RuleName = aws_cloudwatch_event_rule.monitor.name } })
  dimensions          = each.value
  alarm_name          = "${var.name_prefix}-${each.key}-event-target-failures"
  namespace           = "AWS/Events"
  metric_name         = "FailedInvocations"
  statistic           = "Sum"
  period              = 300
  evaluation_periods  = 1
  comparison_operator = "GreaterThanThreshold"
  threshold           = 0
  treat_missing_data  = "notBreaching"
  alarm_actions       = var.alarm_action_arns
}
