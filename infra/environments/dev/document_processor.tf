module "document_processor" {
  source               = "../../modules/lambda"
  function_name        = "${local.name_prefix}-document-processor"
  archive_path         = "${path.module}/../../../build/cases.zip"
  handler              = "document_processor.handler.handler"
  table_name           = module.database.table_name
  table_arn            = module.database.table_arn
  access_mode          = "processor"
  document_bucket_name = module.documents.bucket_name
  document_bucket_arn  = module.documents.bucket_arn
  processing_queue_arn = module.document_pipeline.queue_arn
  log_group_arn        = module.observability.log_group_arns["/aws/lambda/${local.name_prefix}-document-processor"]
  depends_on           = [module.observability]
}
