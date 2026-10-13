resource "aws_apigatewayv2_api" "this" {
  dynamic "cors_configuration" {
    for_each = length(var.browser_origins) > 0 ? [1] : []
    content {
      allow_origins  = var.browser_origins
      allow_methods  = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
      allow_headers  = ["authorization", "content-type", "x-correlation-id", "idempotency-key"]
      expose_headers = ["x-correlation-id"]
      max_age        = 600
    }
  }

  name          = "${var.name_prefix}-api"
  protocol_type = "HTTP"
}

resource "aws_apigatewayv2_authorizer" "this" {
  api_id           = aws_apigatewayv2_api.this.id
  name             = "cognito"
  authorizer_type  = "JWT"
  identity_sources = ["$request.header.Authorization"]
  jwt_configuration {
    audience = [var.client_id]
    issuer   = var.issuer
  }
}

resource "aws_apigatewayv2_integration" "health" {
  api_id                 = aws_apigatewayv2_api.this.id
  integration_type       = "AWS_PROXY"
  integration_uri        = var.lambda_invoke_arn
  integration_method     = "POST"
  payload_format_version = "2.0"
  timeout_milliseconds   = 5000
}

resource "aws_apigatewayv2_route" "health" {
  api_id               = aws_apigatewayv2_api.this.id
  route_key            = "GET /api/v1/health"
  target               = "integrations/${aws_apigatewayv2_integration.health.id}"
  authorization_type   = "JWT"
  authorizer_id        = aws_apigatewayv2_authorizer.this.id
  authorization_scopes = ["aws.cognito.signin.user.admin"]
}

resource "aws_apigatewayv2_stage" "this" {
  api_id      = aws_apigatewayv2_api.this.id
  name        = "$default"
  auto_deploy = true

  default_route_settings {
    throttling_burst_limit = 5
    throttling_rate_limit  = 2
  }

  access_log_settings {
    destination_arn = var.log_group_arn
    format = jsonencode({
      requestId = "$context.requestId"
      routeKey  = "$context.routeKey"
      status    = "$context.status"
    })
  }
}

resource "aws_lambda_permission" "api" {
  statement_id  = "HealthApiOnly"
  action        = "lambda:InvokeFunction"
  function_name = var.lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.this.execution_arn}/*/GET/api/v1/health"
}

output "endpoint" {
  value = "${aws_apigatewayv2_api.this.api_endpoint}/api/v1/health"
}
