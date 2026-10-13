mock_provider "aws" {}

run "private_document_bucket" {
  command = plan
  module { source = "../../modules/storage" }
  variables {
    name_prefix     = "docflow-dev"
    allowed_origins = ["http://localhost:5173"]
  }
  override_resource {
    override_during = plan
    target          = aws_s3_bucket.documents
    values          = { id = "docflow-dev-documents-test", arn = "arn:aws:s3:::docflow-dev-documents-test" }
  }
  assert {
    condition = (
      aws_s3_bucket_public_access_block.documents.block_public_acls &&
      aws_s3_bucket_public_access_block.documents.block_public_policy &&
      aws_s3_bucket_public_access_block.documents.ignore_public_acls &&
      aws_s3_bucket_public_access_block.documents.restrict_public_buckets &&
      !aws_s3_bucket.documents.force_destroy &&
      aws_s3_bucket.documents.bucket_prefix == "docflow-dev-documents-"
    )
    error_message = "Document bucket must remain private with no force destroy."
  }
  assert {
    condition = (
      one(aws_s3_bucket_ownership_controls.documents.rule).object_ownership == "BucketOwnerEnforced" &&
      one(one(aws_s3_bucket_server_side_encryption_configuration.documents.rule).apply_server_side_encryption_by_default).sse_algorithm == "AES256"
    )
    error_message = "Disable ACLs and enable SSE-S3."
  }
  assert {
    condition = (
      one(aws_s3_bucket_cors_configuration.documents.cors_rule).allowed_methods == toset(["PUT"]) &&
      one(aws_s3_bucket_cors_configuration.documents.cors_rule).allowed_origins == toset(["http://localhost:5173"]) &&
      one(aws_s3_bucket_cors_configuration.documents.cors_rule).allowed_headers == toset(["content-type", "content-length", "if-none-match"])
    )
    error_message = "Browser uploads need exact origins and signed headers only."
  }
  assert {
    condition = (
      jsondecode(aws_s3_bucket_policy.documents.policy).Statement[0].Effect == "Deny" &&
      jsondecode(aws_s3_bucket_policy.documents.policy).Statement[0].Condition.Bool["aws:SecureTransport"] == "false" &&
      jsondecode(aws_s3_bucket_policy.documents.policy).Statement[1].Condition.Null["s3:if-none-match"] == "true" &&
      jsondecode(aws_s3_bucket_policy.documents.policy).Statement[2].Condition.NumericGreaterThan["s3:signatureAge"] == "600000"
    )
    error_message = "Enforce TLS, conditional creation and bounded signature age."
  }
}

run "reject_wildcard_origin" {
  command = plan
  module { source = "../../modules/storage" }
  variables {
    name_prefix     = "docflow-dev"
    allowed_origins = ["*"]
  }
  expect_failures = [var.allowed_origins]
}

run "document_iam" {
  command = plan
  module { source = "../../modules/lambda" }
  variables {
    function_name        = "docflow-dev-document-command-handler"
    archive_path         = "../../../build/cases.zip"
    log_group_arn        = "arn:aws:logs:us-east-1:123456789012:log-group:/aws/lambda/docflow-dev-document-command-handler"
    table_arn            = "arn:aws:dynamodb:us-east-1:123456789012:table/docflow-dev"
    table_name           = "docflow-dev"
    access_mode          = "document"
    handler              = "document_api.command.handler"
    document_bucket_name = "docflow-test-documents"
    document_bucket_arn  = "arn:aws:s3:::docflow-test-documents"
  }
  override_resource {
    override_during = plan
    target          = aws_iam_role.this
    values          = { arn = "arn:aws:iam::123456789012:role/docflow-dev-document-command-handler-execution" }
  }
  assert {
    condition = (
      length(jsondecode(aws_iam_role_policy.database[0].policy).Statement) == 2 &&
      jsondecode(aws_iam_role_policy.database[0].policy).Statement[0].Resource == ["arn:aws:dynamodb:us-east-1:123456789012:table/docflow-dev"] &&
      toset(jsondecode(aws_iam_role_policy.database[0].policy).Statement[1].Action) == toset(["dynamodb:PutItem", "dynamodb:ConditionCheckItem", "dynamodb:UpdateItem"]) &&
      jsondecode(aws_iam_role_policy.database[0].policy).Statement[1].Condition["ForAnyValue:StringEquals"]["dynamodb:EnclosingOperation"] == ["TransactWriteItems"] &&
      jsondecode(aws_iam_role_policy.database[0].policy).Statement[1].Condition["ForAllValues:StringLike"]["dynamodb:LeadingKeys"] == ["CASE#*"]
    )
    error_message = "Document reservation must use Case-scoped transactional writes and condition checks."
  }
  assert {
    condition = (
      length(jsondecode(aws_iam_role_policy.storage[0].policy).Statement) == 1 &&
      jsondecode(aws_iam_role_policy.storage[0].policy).Statement[0].Action == ["s3:PutObject"] &&
      jsondecode(aws_iam_role_policy.storage[0].policy).Statement[0].Resource == "arn:aws:s3:::docflow-test-documents/cases/*/documents/*/v1/source" &&
      aws_lambda_function.this.environment[0].variables.DOCUMENT_BUCKET == "docflow-test-documents" &&
      aws_lambda_function.this.handler == "document_api.command.handler"
    )
    error_message = "Upload signer has only scoped PutObject, never read/delete/list or bucket administration."
  }
  assert {
    condition     = length(aws_iam_role_policy.outbox) == 0
    error_message = "Document command role must not receive domain publication grants."
  }
}

run "document_route" {
  command = plan
  module { source = "../../modules/api" }
  variables {
    name_prefix            = "docflow-dev"
    client_id              = "testclient"
    issuer                 = "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_test"
    lambda_invoke_arn      = "arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/arn:aws:lambda:us-east-1:123456789012:function:docflow-dev-case-query-handler/invocations"
    lambda_function_name   = "docflow-dev-case-query-handler"
    document_function_name = "docflow-dev-document-command-handler"
    document_invoke_arn    = "arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/arn:aws:lambda:us-east-1:123456789012:function:docflow-dev-document-command-handler/invocations"
    log_group_arn          = "arn:aws:logs:us-east-1:123456789012:log-group:/aws/apigateway/docflow-dev-api"
    browser_origins        = ["http://localhost:5173"]
  }
  override_resource {
    override_during = plan
    target          = aws_apigatewayv2_api.this
    values          = { execution_arn = "arn:aws:execute-api:us-east-1:123456789012:testapi" }
  }
  assert {
    condition = (
      aws_apigatewayv2_route.delete_document[0].route_key == "DELETE /api/v1/cases/{caseId}/documents/{documentId}" &&
      aws_apigatewayv2_route.delete_document[0].authorization_type == "JWT" &&
      aws_apigatewayv2_route.delete_document[0].authorization_scopes == toset(["aws.cognito.signin.user.admin"]) &&
      aws_lambda_permission.delete_document[0].source_arn == "arn:aws:execute-api:us-east-1:123456789012:testapi/*/DELETE/api/v1/cases/*/documents/*" &&
      contains(aws_apigatewayv2_api.this.cors_configuration[0].allow_methods, "DELETE") &&
      aws_apigatewayv2_route.upload[0].route_key == "POST /api/v1/cases/{caseId}/documents/upload-url" &&
      aws_apigatewayv2_route.upload[0].authorization_type == "JWT" &&
      aws_apigatewayv2_route.upload[0].authorization_scopes == toset(["aws.cognito.signin.user.admin"]) &&
      aws_apigatewayv2_integration.documents[0].integration_uri == var.document_invoke_arn &&
      aws_lambda_permission.upload[0].source_arn == "arn:aws:execute-api:us-east-1:123456789012:testapi/*/POST/api/v1/cases/*/documents/upload-url" &&
      aws_apigatewayv2_api.this.cors_configuration[0].allow_origins == toset(["http://localhost:5173"])
    )
    error_message = "The metadata route must require JWT and invoke only the document function."
  }
}
