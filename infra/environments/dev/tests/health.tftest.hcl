mock_provider "aws" {}

run "authentication_contract" {
  command = plan
  module { source = "../../modules/auth" }
  variables { name_prefix = "docflow-dev" }

  assert {
    condition = (
      !aws_cognito_user_pool_client.this.generate_secret &&
      toset(aws_cognito_user_pool_client.this.explicit_auth_flows) == toset(["ALLOW_USER_SRP_AUTH", "ALLOW_REFRESH_TOKEN_AUTH"]) &&
      aws_cognito_user_pool.this.admin_create_user_config[0].allow_admin_create_user_only &&
      aws_cognito_user_pool.this.user_pool_tier == "LITE" &&
      toset(keys(aws_cognito_user_group.this)) == toset(["requester", "reviewer", "admin"])
    )
    error_message = "Use an invite-only Lite pool, public SRP client and the three approved groups."
  }
}

run "api_security_contract" {
  command = plan
  module { source = "../../modules/api" }
  variables {
    name_prefix          = "docflow-dev"
    client_id            = "testclient"
    issuer               = "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_test"
    lambda_invoke_arn    = "arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/arn:aws:lambda:us-east-1:123456789012:function:docflow-dev-case-query-handler/invocations"
    lambda_function_name = "docflow-dev-case-query-handler"
    log_group_arn        = "arn:aws:logs:us-east-1:123456789012:log-group:/aws/apigateway/docflow-dev-api"
  }
  assert {
    condition = (
      aws_apigatewayv2_route.health.authorization_type == "JWT" &&
      aws_apigatewayv2_route.health.route_key == "GET /api/v1/health" &&
      aws_apigatewayv2_route.health.authorization_scopes == toset(["aws.cognito.signin.user.admin"]) &&
      aws_apigatewayv2_authorizer.this.jwt_configuration[0].audience == toset(["testclient"]) &&
      aws_apigatewayv2_authorizer.this.jwt_configuration[0].issuer == var.issuer &&
      aws_apigatewayv2_integration.health.payload_format_version == "2.0"
    )
    error_message = "Health requires a scoped Cognito JWT for the intended issuer/client and v2 payload."
  }
  assert {
    condition = (
      aws_apigatewayv2_stage.this.default_route_settings[0].throttling_rate_limit == 2 &&
      !strcontains(aws_apigatewayv2_stage.this.access_log_settings[0].format, "Authorization")
    )
    error_message = "Dev API must have bounded request throttling and no credential logging."
  }
}

run "lambda_permissions" {
  command = plan
  module { source = "../../modules/lambda" }
  variables {
    function_name = "docflow-dev-case-query-handler"
    archive_path  = "../../../build/health.zip"
    log_group_arn = "arn:aws:logs:us-east-1:123456789012:log-group:/aws/lambda/docflow-dev-case-query-handler"
  }
  override_resource {
    target = aws_iam_role.this
    values = { arn = "arn:aws:iam::123456789012:role/docflow-dev-case-query-handler-execution" }
  }
  assert {
    condition = (
      toset(jsondecode(aws_iam_role_policy.logs.policy).Statement[0].Action) == toset(["logs:CreateLogStream", "logs:PutLogEvents"]) &&
      jsondecode(aws_iam_role_policy.logs.policy).Statement[0].Resource == "${var.log_group_arn}:*" &&
      aws_lambda_function.this.runtime == "python3.13"
    )
    error_message = "The health Lambda must only write to its own log streams, without domain permissions."
  }
}
