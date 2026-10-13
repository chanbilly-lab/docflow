module "case_command" {
  source              = "../../modules/lambda"
  function_name       = "${local.name_prefix}-case-command-handler"
  archive_path        = "${path.module}/../../../build/cases.zip"
  handler             = "case_api.command.handler"
  table_name          = module.database.table_name
  table_arn           = module.database.table_arn
  access_mode         = "command"
  workflow_enabled    = true
  workflow_arn        = module.workflow.arn
  workflow_stream_arn = module.database.stream_arn
  log_group_arn       = module.observability.log_group_arns["/aws/lambda/${local.name_prefix}-case-command-handler"]
  depends_on          = [module.observability]
}
