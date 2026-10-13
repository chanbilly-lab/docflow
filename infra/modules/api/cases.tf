locals {
  case_routes = {
    submit   = { method = "POST", path = "cases/{caseId}/submit", target = "command" }
    resubmit = { method = "POST", path = "cases/{caseId}/resubmit", target = "command" }
    create   = { method = "POST", path = "cases", target = "command" }
    list     = { method = "GET", path = "cases", target = "query" }
    detail   = { method = "GET", path = "cases/{caseId}", target = "query" }
    activity = { method = "GET", path = "cases/{caseId}/activity", target = "query" }
  }
}

resource "aws_apigatewayv2_integration" "cases" {
  for_each               = var.command_function_name == null ? {} : { command = var.command_invoke_arn, query = var.lambda_invoke_arn }
  api_id                 = aws_apigatewayv2_api.this.id
  integration_type       = "AWS_PROXY"
  integration_uri        = each.value
  integration_method     = "POST"
  payload_format_version = "2.0"
  timeout_milliseconds   = 15000
}

resource "aws_apigatewayv2_route" "cases" {
  for_each             = var.command_function_name == null ? {} : local.case_routes
  api_id               = aws_apigatewayv2_api.this.id
  route_key            = "${each.value.method} /api/v1/${each.value.path}"
  target               = "integrations/${aws_apigatewayv2_integration.cases[each.value.target].id}"
  authorization_type   = "JWT"
  authorizer_id        = aws_apigatewayv2_authorizer.this.id
  authorization_scopes = ["aws.cognito.signin.user.admin"]
}

resource "aws_lambda_permission" "cases" {
  for_each      = var.command_function_name == null ? {} : local.case_routes
  statement_id  = "CaseApi-${each.key}"
  action        = "lambda:InvokeFunction"
  function_name = each.value.target == "command" ? var.command_function_name : var.lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.this.execution_arn}/*/${each.value.method}/api/v1/${replace(each.value.path, "{caseId}", "*")}"
}
