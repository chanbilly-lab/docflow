variable "notification_email_config" {
  type        = object({ sender = string, reviewer = string, identity_arn = string })
  default     = null
  description = "Configure approved addresses/existing SES identity only for the authorized cloud session."
}
module "notifications" {
  source          = "../../modules/notifications"
  name_prefix     = local.name_prefix
  domain_bus_name = module.domain_events.name
  table_name      = module.database.table_name
  table_arn       = module.database.table_arn
  user_pool_id    = module.auth.user_pool_id
  user_pool_arn   = module.auth.user_pool_arn
  log_group_arn   = module.observability.log_group_arns["/aws/lambda/${local.name_prefix}-notification-worker"]
  archive_path    = "${path.module}/../../../build/cases.zip"
  email_config    = var.notification_email_config
  depends_on      = [module.observability]
}
