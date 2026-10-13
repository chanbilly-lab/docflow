module "document_pipeline" {
  source      = "../../modules/document_pipeline"
  name_prefix = local.name_prefix
  bucket_name = module.documents.bucket_name
}
# Single owner of this bucket's complete notification configuration.
# Enabling notifications follows queue policies and the EventBridge target.
resource "aws_s3_bucket_notification" "documents" {
  bucket      = module.documents.bucket_name
  eventbridge = true
  depends_on  = [module.document_pipeline]
}
output "document_processing_queue_arn" { value = module.document_pipeline.queue_arn }
output "document_processing_queue_url" { value = module.document_pipeline.queue_url }
output "document_processing_dlq_arn" { value = module.document_pipeline.dlq_arn }
