resource "aws_cloudwatch_dashboard" "this" {
  dashboard_name = "${var.name_prefix}-operations"
  dashboard_body = jsonencode({ widgets = [
    { type = "metric", x = 0, y = 0, width = 12, height = 6, properties = {
      title   = "Committed domain facts observed at dispatch (approximate)", region = var.region, view = "timeSeries", stat = "Sum", period = 300,
      metrics = [for name in ["CasesCreated", "CasesSubmitted", "CasesApproved", "CasesRejected", "CasesNeedsInformation", "DocumentsProcessed", "DocumentValidationFailures", "ReviewTasksCreated", "WorkflowFailures"] : ["DocFlow", name, "service", "outbox-publisher"]]
    } },
    { type = "metric", x = 12, y = 0, width = 12, height = 6, properties = {
      title   = "Pending work (read-only snapshot)", region = var.region, view = "timeSeries", stat = "Maximum", period = 300,
      metrics = [for name in ["ReviewTasksPending", "OutboxPendingAgeSeconds", "WorkflowStartPendingAgeSeconds"] : ["DocFlow", name, "service", "operations-monitor"]]
    } },
    { type = "metric", x = 0, y = 6, width = 12, height = 6, properties = {
      title   = "Review duration from creation to decision", region = var.region, view = "timeSeries", stat = "Average", period = 300,
      metrics = [["DocFlow", "ReviewDurationSeconds", "service", "workflow-finalize-case"]]
    } },
    { type = "metric", x = 12, y = 6, width = 12, height = 6, properties = {
      title   = "Consumer dead letters", region = var.region, view = "timeSeries", stat = "Maximum", period = 60,
      metrics = [for name in var.dlq_names : ["AWS/SQS", "ApproximateNumberOfMessagesVisible", "QueueName", name]]
    } },
    { type = "alarm", x = 0, y = 12, width = 24, height = 6, properties = { title = "Operations alarms", alarms = concat(
      [for a in aws_cloudwatch_metric_alarm.dlq : a.arn],
      [for a in aws_cloudwatch_metric_alarm.workflow : a.arn],
      [for a in aws_cloudwatch_metric_alarm.pending : a.arn],
      [for a in aws_cloudwatch_metric_alarm.retries : a.arn],
      [for a in aws_cloudwatch_metric_alarm.lambda_errors : a.arn],
      [aws_cloudwatch_metric_alarm.heartbeat.arn],
      [for a in aws_cloudwatch_metric_alarm.target_delivery : a.arn]
    ) } }
  ] })
}
