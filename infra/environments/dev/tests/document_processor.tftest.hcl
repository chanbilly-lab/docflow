mock_provider "aws" {}
run "processor_contract" {
  command = plan
  module { source = "../../modules/lambda" }
  variables {
    function_name        = "docflow-dev-document-processor"
    log_group_arn        = "arn:aws:logs:us-east-1:123456789012:log-group:/aws/lambda/docflow-dev-document-processor"
    archive_path         = "../../../build/cases.zip"
    handler              = "document_processor.handler.handler"
    table_name           = "docflow-dev"
    table_arn            = "arn:aws:dynamodb:us-east-1:123456789012:table/docflow-dev"
    access_mode          = "processor"
    document_bucket_name = "docflow-dev-documents-test"
    document_bucket_arn  = "arn:aws:s3:::docflow-dev-documents-test"
    processing_queue_arn = "arn:aws:sqs:us-east-1:123456789012:docflow-dev-document-processing"
  }
  assert {
    condition     = aws_lambda_function.this.timeout == 60 && aws_lambda_function.this.handler == "document_processor.handler.handler" && aws_lambda_function.this.environment[0].variables.DOCUMENT_BUCKET == "docflow-dev-documents-test"
    error_message = "Processor requires its entry point, bucket and 60-second timeout."
  }
  assert {
    condition     = aws_lambda_event_source_mapping.processor[0].batch_size == 5 && aws_lambda_event_source_mapping.processor[0].maximum_batching_window_in_seconds == 0 && length(aws_lambda_event_source_mapping.processor[0].function_response_types) == 1 && contains(aws_lambda_event_source_mapping.processor[0].function_response_types, "ReportBatchItemFailures") && aws_lambda_event_source_mapping.processor[0].event_source_arn == var.processing_queue_arn
    error_message = "Use bounded SQS batches with partial failure responses."
  }
  assert {
    condition     = length(aws_iam_role_policy.database) == 0 && length(aws_iam_role_policy.storage) == 0 && jsondecode(aws_iam_role_policy.processor[0].policy).Statement[0].Resource == var.processing_queue_arn && jsondecode(aws_iam_role_policy.processor[0].policy).Statement[1].Resource == "${var.document_bucket_arn}/cases/*/documents/*/v*/source" && jsondecode(aws_iam_role_policy.processor[0].policy).Statement[3].Condition["ForAnyValue:StringEquals"]["dynamodb:EnclosingOperation"][0] == "TransactWriteItems"
    error_message = "No command grants; scope polling, reads and transactional writes."
  }
  assert {
    condition     = jsondecode(aws_iam_role_policy.processor[0].policy).Statement[4].Action == ["dynamodb:UpdateItem"] && jsondecode(aws_iam_role_policy.processor[0].policy).Statement[4].Condition["ForAllValues:StringLike"]["dynamodb:LeadingKeys"] == ["CASE#*"] && jsondecode(aws_iam_role_policy.processor[0].policy).Statement[4].Condition["ForAnyValue:StringEquals"]["dynamodb:EnclosingOperation"] == ["TransactWriteItems"]
    error_message = "Revision increments must be transactional and CASE-only."
  }
}
run "processor_dev_wiring" {
  command = plan
  assert {
    condition     = module.document_processor.function_name == "docflow-dev-document-processor"
    error_message = "Dev must instantiate processor with centralized logs."
  }
}
