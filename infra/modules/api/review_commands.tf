locals {
  review_commands = {
    decision = { method = "POST", path = "reviews/{taskId}/decision" }
    claim    = { method = "POST", path = "reviews/{taskId}/claim" }
    start    = { method = "POST", path = "reviews/{taskId}/start" }
    check    = { method = "PUT", path = "reviews/{taskId}/checks/{checkId}" }
  }
}
resource "aws_apigatewayv2_integration" "review_commands" {
  count                  = var.review_command_function_name == null ? 0 : 1
  api_id                 = aws_apigatewayv2_api.this.id
  integration_type       = "AWS_PROXY"
  integration_uri        = var.review_command_invoke_arn
  integration_method     = "POST"
  payload_format_version = "2.0"
  timeout_milliseconds   = 15000
}
resource "aws_apigatewayv2_route" "review_commands" {
  for_each             = var.review_command_function_name == null ? {} : local.review_commands
  api_id               = aws_apigatewayv2_api.this.id
  route_key            = "${each.value.method} /api/v1/${each.value.path}"
  target               = "integrations/${aws_apigatewayv2_integration.review_commands[0].id}"
  authorization_type   = "JWT"
  authorizer_id        = aws_apigatewayv2_authorizer.this.id
  authorization_scopes = ["aws.cognito.signin.user.admin"]
}
resource "aws_lambda_permission" "review_commands" {
  for_each      = aws_apigatewayv2_route.review_commands
  statement_id  = "ReviewCommand-${each.key}"
  action        = "lambda:InvokeFunction"
  function_name = var.review_command_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.this.execution_arn}/*/${local.review_commands[each.key].method}/api/v1/${replace(replace(local.review_commands[each.key].path, "{taskId}", "*"), "{checkId}", "*")}"
}
