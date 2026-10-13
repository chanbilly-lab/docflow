module "auth" {
  source      = "../../modules/auth"
  name_prefix = local.name_prefix
}

module "health" {
  source        = "../../modules/lambda"
  function_name = "${local.name_prefix}-case-query-handler"
  archive_path  = "${path.module}/../../../build/cases.zip"
  log_group_arn = module.observability.log_group_arns["/aws/lambda/${local.name_prefix}-case-query-handler"]
  handler       = "case_api.query.handler"
  table_name    = module.database.table_name
  table_arn     = module.database.table_arn
  access_mode   = "query"
  depends_on    = [module.observability]
}

module "api" {
  review_command_function_name = module.review_command.function_name
  review_command_invoke_arn    = module.review_command.invoke_arn
  review_function_name         = module.review_query.function_name
  review_invoke_arn            = module.review_query.invoke_arn
  document_function_name       = module.document_command.function_name
  document_invoke_arn          = module.document_command.invoke_arn
  browser_origins              = var.browser_origins
  source                       = "../../modules/api"
  command_function_name        = module.case_command.function_name
  command_invoke_arn           = module.case_command.invoke_arn
  name_prefix                  = local.name_prefix
  client_id                    = module.auth.client_id
  issuer                       = module.auth.issuer
  lambda_invoke_arn            = module.health.invoke_arn
  lambda_function_name         = module.health.function_name
  log_group_arn                = module.observability.log_group_arns["/aws/apigateway/${local.name_prefix}-api"]
  depends_on                   = [module.observability]
}

output "user_pool_id" { value = module.auth.user_pool_id }
output "user_pool_client_id" { value = module.auth.client_id }
output "health_endpoint" { value = module.api.endpoint }
