variable "alarm_action_arns" {
  description = "Existing approved SNS topics; empty means console/dashboard alarms only."
  type        = list(string)
  default     = []
}
module "operations" {
  source            = "../../modules/operations"
  name_prefix       = local.name_prefix
  region            = var.aws_region
  table_name        = module.database.table_name
  table_arn         = module.database.table_arn
  workflow_arn      = module.workflow.arn
  log_group_arn     = module.observability.log_group_arns["/aws/lambda/${local.name_prefix}-operations-monitor"]
  archive_path      = "${path.module}/../../../build/cases.zip"
  function_names    = toset([for name in local.lambda_names : "${local.name_prefix}-${name}" if name != "notification-worker" || var.notification_email_config != null])
  dlq_names         = toset([module.document_pipeline.dlq_name, module.notifications.dlq_name])
  alarm_action_arns = var.alarm_action_arns
  event_rule_dimensions = {
    documents    = { RuleName = "${local.name_prefix}-s3-document-created" }
    review_ready = { RuleName = "${local.name_prefix}-notification-review_ready", EventBusName = module.domain_events.name }
    requester    = { RuleName = "${local.name_prefix}-notification-requester", EventBusName = module.domain_events.name }
  }
  depends_on = [module.observability]
}
