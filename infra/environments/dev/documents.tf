variable "browser_origins" {
  type    = list(string)
  default = ["http://localhost:5173", "http://127.0.0.1:5173"]
}
module "documents" {
  source          = "../../modules/storage"
  name_prefix     = local.name_prefix
  allowed_origins = var.browser_origins
}
module "document_command" {
  source               = "../../modules/lambda"
  function_name        = "${local.name_prefix}-document-command-handler"
  archive_path         = "${path.module}/../../../build/cases.zip"
  log_group_arn        = module.observability.log_group_arns["/aws/lambda/${local.name_prefix}-document-command-handler"]
  handler              = "document_api.command.handler"
  table_name           = module.database.table_name
  table_arn            = module.database.table_arn
  access_mode          = "document"
  document_bucket_name = module.documents.bucket_name
  document_bucket_arn  = module.documents.bucket_arn
  depends_on           = [module.observability]
}
