mock_provider "aws" {}

run "case_routes" {
  command = plan
  module { source = "../../modules/api" }
  variables {
    browser_origins       = ["http://localhost:5173"]
    name_prefix           = "docflow-dev"
    client_id             = "testclient"
    issuer                = "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_test"
    lambda_invoke_arn     = "arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/arn:aws:lambda:us-east-1:123456789012:function:docflow-dev-case-query-handler/invocations"
    lambda_function_name  = "docflow-dev-case-query-handler"
    command_invoke_arn    = "arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/arn:aws:lambda:us-east-1:123456789012:function:docflow-dev-case-command-handler/invocations"
    command_function_name = "docflow-dev-case-command-handler"
    log_group_arn         = "arn:aws:logs:us-east-1:123456789012:log-group:/aws/apigateway/docflow-dev-api"
  }
  override_resource {
    target          = aws_apigatewayv2_api.this
    override_during = plan
    values          = { execution_arn = "arn:aws:execute-api:us-east-1:123456789012:testapi" }
  }
  assert {
    condition = (
      toset([for route in aws_apigatewayv2_route.cases : route.route_key]) == toset([
        "POST /api/v1/cases/{caseId}/submit", "POST /api/v1/cases/{caseId}/resubmit", "POST /api/v1/cases", "GET /api/v1/cases", "GET /api/v1/cases/{caseId}", "GET /api/v1/cases/{caseId}/activity"
      ]) &&
      alltrue([for route in aws_apigatewayv2_route.cases : route.authorization_type == "JWT" &&
      route.authorization_scopes == toset(["aws.cognito.signin.user.admin"])])
    )
    error_message = "All six Case routes require scoped JWTs."
  }
  assert {
    condition     = contains(aws_apigatewayv2_api.this.cors_configuration[0].allow_headers, "idempotency-key") && aws_lambda_permission.cases["submit"].function_name == var.command_function_name && endswith(aws_lambda_permission.cases["resubmit"].source_arn, "/POST/api/v1/cases/*/resubmit")
    error_message = "Submission CORS and invoke scope must match the command boundary."
  }
}

run "command_iam" {
  command = plan
  module { source = "../../modules/lambda" }
  variables {
    function_name = "docflow-dev-case-command-handler"
    archive_path  = "../../../build/cases.zip"
    log_group_arn = "arn:aws:logs:us-east-1:123456789012:log-group:/aws/lambda/docflow-dev-case-command-handler"
    table_arn     = "arn:aws:dynamodb:us-east-1:123456789012:table/docflow-dev"
    table_name    = "docflow-dev"
    handler       = "case_api.command.handler"
    access_mode   = "command"
  }
  override_resource {
    target = aws_iam_role.this
    values = { arn = "arn:aws:iam::123456789012:role/docflow-dev-case-command-handler-execution" }
  }
  assert {
    condition = (
      length(aws_iam_role_policy.outbox) == 0 &&
      length(jsondecode(aws_iam_role_policy.database[0].policy).Statement) == 2 &&
      jsondecode(aws_iam_role_policy.database[0].policy).Statement[1].Action == ["dynamodb:PutItem"] &&
      jsondecode(aws_iam_role_policy.database[0].policy).Statement[1].Condition["ForAnyValue:StringEquals"]["dynamodb:EnclosingOperation"] == ["TransactWriteItems"] &&
      jsondecode(aws_iam_role_policy.database[0].policy).Statement[1].Condition["ForAllValues:StringLike"]["dynamodb:LeadingKeys"] == ["CASE#*", "IDEMPOTENCY#case-submission"]
    )
    error_message = "Command writes must be transactional and restricted to Case partitions."
  }
}

run "query_iam" {
  command = plan
  module { source = "../../modules/lambda" }
  variables {
    function_name = "docflow-dev-case-query-handler"
    archive_path  = "../../../build/cases.zip"
    log_group_arn = "arn:aws:logs:us-east-1:123456789012:log-group:/aws/lambda/docflow-dev-case-query-handler"
    table_arn     = "arn:aws:dynamodb:us-east-1:123456789012:table/docflow-dev"
    table_name    = "docflow-dev"
    handler       = "case_api.query.handler"
    access_mode   = "query"
  }
  override_resource {
    target = aws_iam_role.this
    values = { arn = "arn:aws:iam::123456789012:role/docflow-dev-case-query-handler-execution" }
  }
  assert {
    condition = (
      length(jsondecode(aws_iam_role_policy.database[0].policy).Statement) == 1 &&
      toset(jsondecode(aws_iam_role_policy.database[0].policy).Statement[0].Action) == toset(["dynamodb:GetItem", "dynamodb:Query"]) &&
      length(jsondecode(aws_iam_role_policy.database[0].policy).Statement[0].Resource) == 3
    )
    error_message = "Query role must be read-only for the table and two indexes."
  }
}
