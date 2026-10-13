module "outbox_publisher" {
  source                = "../../modules/lambda"
  function_name         = "${local.name_prefix}-outbox-publisher"
  archive_path          = "${path.module}/../../../build/cases.zip"
  handler               = "outbox_publisher.handler.handler"
  table_name            = module.database.table_name
  table_arn             = module.database.table_arn
  access_mode           = "publisher"
  outbox_stream_arn     = module.database.stream_arn
  domain_bus_arn        = module.domain_events.arn
  outbox_stream_enabled = true
  log_group_arn         = module.observability.log_group_arns["/aws/lambda/${local.name_prefix}-outbox-publisher"]
  depends_on            = [module.observability]
}
