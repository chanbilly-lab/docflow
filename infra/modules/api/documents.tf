resource "aws_apigatewayv2_integration" "documents" {
  count                  = var.document_function_name == null ? 0 : 1
  api_id                 = aws_apigatewayv2_api.this.id
  integration_type       = "AWS_PROXY"
  integration_uri        = var.document_invoke_arn
  integration_method     = "POST"
  payload_format_version = "2.0"
  timeout_milliseconds   = 15000
}
resource "aws_apigatewayv2_route" "upload" {
  count                = var.document_function_name == null ? 0 : 1
  api_id               = aws_apigatewayv2_api.this.id
  route_key            = "POST /api/v1/cases/{caseId}/documents/upload-url"
  target               = "integrations/${aws_apigatewayv2_integration.documents[0].id}"
  authorization_type   = "JWT"
  authorizer_id        = aws_apigatewayv2_authorizer.this.id
  authorization_scopes = ["aws.cognito.signin.user.admin"]
}
resource "aws_lambda_permission" "upload" {
  count         = var.document_function_name == null ? 0 : 1
  statement_id  = "DocumentUploadApi"
  action        = "lambda:InvokeFunction"
  function_name = var.document_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.this.execution_arn}/*/POST/api/v1/cases/*/documents/upload-url"
}

resource "aws_apigatewayv2_route" "delete_document" {
  count                = var.document_function_name == null ? 0 : 1
  api_id               = aws_apigatewayv2_api.this.id
  route_key            = "DELETE /api/v1/cases/{caseId}/documents/{documentId}"
  target               = "integrations/${aws_apigatewayv2_integration.documents[0].id}"
  authorization_type   = "JWT"
  authorizer_id        = aws_apigatewayv2_authorizer.this.id
  authorization_scopes = ["aws.cognito.signin.user.admin"]
}
resource "aws_lambda_permission" "delete_document" {
  count         = var.document_function_name == null ? 0 : 1
  statement_id  = "DocumentDeleteApi"
  action        = "lambda:InvokeFunction"
  function_name = var.document_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.this.execution_arn}/*/DELETE/api/v1/cases/*/documents/*"
}
