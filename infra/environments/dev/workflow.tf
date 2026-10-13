module "workflow_validate" {
  source        = "../../modules/lambda"
  function_name = "${local.name_prefix}-workflow-validate-case"
  archive_path  = "${path.module}/../../../build/cases.zip"
  handler       = "workflow_validate_case.handler.handler"
  table_name    = module.database.table_name
  table_arn     = module.database.table_arn
  access_mode   = "workflow"
  log_group_arn = module.observability.log_group_arns["/aws/lambda/${local.name_prefix}-workflow-validate-case"]
  depends_on    = [module.observability]
}
module "workflow_failure" {
  source        = "../../modules/lambda"
  function_name = "${local.name_prefix}-workflow-failure-handler"
  archive_path  = "${path.module}/../../../build/cases.zip"
  handler       = "workflow_failure_handler.handler.handler"
  table_name    = module.database.table_name
  table_arn     = module.database.table_arn
  access_mode   = "workflow"
  log_group_arn = module.observability.log_group_arns["/aws/lambda/${local.name_prefix}-workflow-failure-handler"]
  depends_on    = [module.observability]
}
module "workflow" {
  source        = "../../modules/workflow"
  name          = "${local.name_prefix}-case-review-workflow"
  validate_arn  = module.workflow_validate.function_arn
  failure_arn   = module.workflow_failure.function_arn
  review_arn    = module.workflow_create_review.function_arn
  finalize_arn  = module.workflow_finalize.function_arn
  log_group_arn = module.observability.log_group_arns["/aws/vendedlogs/states/${local.name_prefix}-case-review-workflow"]
}
output "workflow_arn" { value = module.workflow.arn }

module "workflow_create_review" {
  source        = "../../modules/lambda"
  function_name = "${local.name_prefix}-workflow-create-review-task"
  archive_path  = "${path.module}/../../../build/cases.zip"
  handler       = "workflow_create_review_task.handler.handler"
  table_name    = module.database.table_name
  table_arn     = module.database.table_arn
  access_mode   = "review_creator"
  log_group_arn = module.observability.log_group_arns["/aws/lambda/${local.name_prefix}-workflow-create-review-task"]
  depends_on    = [module.observability]
}

module "review_query" {
  source        = "../../modules/lambda"
  function_name = "${local.name_prefix}-review-query-handler"
  archive_path  = "${path.module}/../../../build/cases.zip"
  handler       = "review_api.query.handler"
  table_name    = module.database.table_name
  table_arn     = module.database.table_arn
  access_mode   = "review_query"
  log_group_arn = module.observability.log_group_arns["/aws/lambda/${local.name_prefix}-review-query-handler"]
  depends_on    = [module.observability]
}

module "review_command" {
  source        = "../../modules/lambda"
  function_name = "${local.name_prefix}-review-command-handler"
  archive_path  = "${path.module}/../../../build/cases.zip"
  handler       = "review_api.command.handler"
  table_name    = module.database.table_name
  table_arn     = module.database.table_arn
  access_mode   = "review_command"
  log_group_arn = module.observability.log_group_arns["/aws/lambda/${local.name_prefix}-review-command-handler"]
  depends_on    = [module.observability]
}

module "workflow_finalize" {
  source        = "../../modules/lambda"
  function_name = "${local.name_prefix}-workflow-finalize-case"
  archive_path  = "${path.module}/../../../build/cases.zip"
  handler       = "workflow_finalize_case.handler.handler"
  table_name    = module.database.table_name
  table_arn     = module.database.table_arn
  access_mode   = "workflow"
  log_group_arn = module.observability.log_group_arns["/aws/lambda/${local.name_prefix}-workflow-finalize-case"]
  depends_on    = [module.observability]
}
