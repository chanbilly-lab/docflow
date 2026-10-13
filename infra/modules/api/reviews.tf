resource "aws_apigatewayv2_integration" "reviews" {
  count                  = var.review_function_name == null ? 0 : 1
  api_id                 = aws_apigatewayv2_api.this.id
  integration_type       = "AWS_PROXY"
  integration_uri        = var.review_invoke_arn
  integration_method     = "POST"
  payload_format_version = "2.0"
  timeout_milliseconds   = 15000
}
resource "aws_apigatewayv2_route" "reviews" {
  for_each             = var.review_function_name == null ? toset([]) : toset(["reviews", "reviews/{taskId}"])
  api_id               = aws_apigatewayv2_api.this.id
  route_key            = "GET /api/v1/${each.value}"
  target               = "integrations/${aws_apigatewayv2_integration.reviews[0].id}"
  authorization_type   = "JWT"
  authorizer_id        = aws_apigatewayv2_authorizer.this.id
  authorization_scopes = ["aws.cognito.signin.user.admin"]
}
resource "aws_lambda_permission" "reviews" {
  for_each      = aws_apigatewayv2_route.reviews
  statement_id  = each.key == "reviews" ? "ReviewList" : "ReviewDetail"
  action        = "lambda:InvokeFunction"
  function_name = var.review_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.this.execution_arn}/*/GET/api/v1/${replace(each.key, "{taskId}", "*")}"
}
