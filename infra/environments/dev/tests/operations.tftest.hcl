mock_provider "aws" {}
run "operations_contract" {
  command = plan
  module { source = "../../modules/operations" }
  variables {
    name_prefix           = "docflow-dev"
    region                = "us-east-1"
    table_name            = "docflow-dev"
    table_arn             = "arn:aws:dynamodb:us-east-1:123456789012:table/docflow-dev"
    log_group_arn         = "arn:aws:logs:us-east-1:123456789012:log-group:/aws/lambda/docflow-dev-operations-monitor"
    archive_path          = "../../../build/cases.zip"
    workflow_arn          = "arn:aws:states:us-east-1:123456789012:stateMachine:docflow-dev-case-review-workflow"
    function_names        = ["docflow-dev-case-command-handler", "docflow-dev-operations-monitor"]
    dlq_names             = ["docflow-dev-document-processing-dlq", "docflow-dev-notification-dlq"]
    event_rule_dimensions = { notification = { RuleName = "notification", EventBusName = "docflow-dev-domain" } }
  }
  assert {
    condition     = aws_cloudwatch_metric_alarm.target_delivery["monitor"].dimensions.RuleName == aws_cloudwatch_event_rule.monitor.name && aws_cloudwatch_metric_alarm.target_delivery["notification"].dimensions == tomap({ RuleName = "notification", EventBusName = "docflow-dev-domain" })
    error_message = "FailedInvocations requires exact RuleName dimensions."
  }
  assert {
    condition     = length(aws_cloudwatch_metric_alarm.dlq) == 2 && alltrue([for a in aws_cloudwatch_metric_alarm.dlq : a.threshold == 0 && a.statistic == "Maximum" && a.treat_missing_data == "notBreaching"])
    error_message = "Both consumer DLQs must alarm on visible messages."
  }
  assert {
    condition     = length(aws_cloudwatch_metric_alarm.workflow) == 3 && alltrue([for a in aws_cloudwatch_metric_alarm.workflow : a.dimensions.StateMachineArn == var.workflow_arn]) && aws_cloudwatch_metric_alarm.heartbeat.treat_missing_data == "breaching" && aws_cloudwatch_metric_alarm.heartbeat.evaluation_periods == 3
    error_message = "Workflow failures/timeouts/aborts and a missing monitor need alarms."
  }
  assert {
    condition     = aws_cloudwatch_metric_alarm.pending["OutboxPendingAgeSeconds"].threshold == 900 && aws_cloudwatch_metric_alarm.pending["WorkflowStartPendingAgeSeconds"].threshold == 300 && length(aws_cloudwatch_metric_alarm.retries) == 4
    error_message = "Durable pending age and partial-batch failures must be observable."
  }
  assert {
    condition     = aws_cloudwatch_event_rule.monitor.schedule_expression == "rate(5 minutes)" && aws_lambda_function.monitor.reserved_concurrent_executions == 1 && aws_lambda_function.monitor.tracing_config[0].mode == "Active"
    error_message = "Bound monitor cost/concurrency and enable platform tracing."
  }
  assert {
    condition     = jsondecode(aws_iam_role_policy.monitor.policy).Statement[1].Action == ["dynamodb:Scan"] && jsondecode(aws_iam_role_policy.monitor.policy).Statement[1].Resource == var.table_arn && jsondecode(aws_iam_role_policy.monitor.policy).Statement[1].Condition.StringEquals["dynamodb:Select"] == "SPECIFIC_ATTRIBUTES" && !contains(jsondecode(aws_iam_role_policy.monitor.policy).Statement[1].Condition["ForAllValues:StringEquals"]["dynamodb:Attributes"], "workflowTaskToken")
    error_message = "Monitor must have read-only, projected table access without sensitive payloads."
  }
  assert {
    condition     = alltrue([for a in aws_cloudwatch_metric_alarm.lambda_errors : a.threshold == 5 && anytrue([for q in a.metric_query : q.expression == "IF(invocations>=10,100*errors/invocations,0)"])]) && length(var.alarm_action_arns) == 0
    error_message = "Use per-function error rate and do not invent notification recipients."
  }
}
run "lambda_tracing" {
  command = plan
  module { source = "../../modules/lambda" }
  variables {
    function_name = "docflow-dev-case-query-handler"
    archive_path  = "../../../build/cases.zip"
    log_group_arn = "arn:aws:logs:us-east-1:123456789012:log-group:/aws/lambda/docflow-dev-case-query-handler"
  }
  assert {
    condition     = aws_lambda_function.this.tracing_config[0].mode == "Active" && jsondecode(aws_iam_role_policy.tracing.policy).Statement[0].Action == ["xray:PutTraceSegments", "xray:PutTelemetryRecords"]
    error_message = "Shared Lambda module must enable tracing and telemetry permissions."
  }
}
