mock_provider "aws" {}

run "review_routes" {
  command = plan
  module { source = "../../modules/api" }
  variables {
    name_prefix          = "docflow-dev"
    client_id            = "testclient"
    issuer               = "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_test"
    lambda_function_name = "docflow-dev-case-query-handler"
    lambda_invoke_arn    = "arn:aws:lambda:us-east-1:123456789012:function:case"
    review_function_name = "docflow-dev-review-query-handler"
    review_invoke_arn    = "arn:aws:lambda:us-east-1:123456789012:function:review"
    log_group_arn        = "arn:aws:logs:us-east-1:123456789012:log-group:/aws/apigateway/docflow-dev-api"
  }
  override_resource {
    target          = aws_apigatewayv2_api.this
    override_during = plan
    values          = { execution_arn = "arn:aws:execute-api:us-east-1:123456789012:testapi" }
  }
  assert {
    condition     = toset([for r in aws_apigatewayv2_route.reviews : r.route_key]) == toset(["GET /api/v1/reviews", "GET /api/v1/reviews/{taskId}"]) && alltrue([for r in aws_apigatewayv2_route.reviews : r.authorization_type == "JWT" && r.authorization_scopes == toset(["aws.cognito.signin.user.admin"])])
    error_message = "Both review queries require scoped JWT."
  }
  assert {
    condition     = aws_lambda_permission.reviews["reviews/{taskId}"].source_arn == "arn:aws:execute-api:us-east-1:123456789012:testapi/*/GET/api/v1/reviews/*" && aws_lambda_permission.reviews["reviews"].function_name == var.review_function_name
    error_message = "Review invocation must be route-specific."
  }
}
run "review_query_iam" {
  command = plan
  module { source = "../../modules/lambda" }
  variables {
    function_name = "docflow-dev-review-query-handler"
    handler       = "review_api.query.handler"
    archive_path  = "../../../build/cases.zip"
    log_group_arn = "arn:aws:logs:us-east-1:123456789012:log-group:/aws/lambda/docflow-dev-review-query-handler"
    table_name    = "docflow-dev"
    table_arn     = "arn:aws:dynamodb:us-east-1:123456789012:table/docflow-dev"
    access_mode   = "review_query"
  }
  assert {
    condition     = length(jsondecode(aws_iam_role_policy.database[0].policy).Statement) == 1 && jsondecode(aws_iam_role_policy.database[0].policy).Statement[0].Action == ["dynamodb:GetItem", "dynamodb:Query"] && jsondecode(aws_iam_role_policy.database[0].policy).Statement[0].Resource == [var.table_arn, "${var.table_arn}/index/GSI1"] && length(aws_iam_role_policy.workflow_start) == 0 && length(aws_iam_role_policy.outbox) == 0
    error_message = "Review query reads only table/GSI1 with no publish or workflow grants."
  }
}
run "review_creator_iam" {
  command = plan
  module { source = "../../modules/lambda" }
  variables {
    function_name = "docflow-dev-workflow-create-review-task"
    handler       = "workflow_create_review_task.handler.handler"
    archive_path  = "../../../build/cases.zip"
    log_group_arn = "arn:aws:logs:us-east-1:123456789012:log-group:/aws/lambda/docflow-dev-workflow-create-review-task"
    table_name    = "docflow-dev"
    table_arn     = "arn:aws:dynamodb:us-east-1:123456789012:table/docflow-dev"
    access_mode   = "review_creator"
  }
  assert {
    condition     = jsondecode(aws_iam_role_policy.database[0].policy).Statement[0].Resource == [var.table_arn] && jsondecode(aws_iam_role_policy.database[0].policy).Statement[1].Action == ["dynamodb:PutItem", "dynamodb:ConditionCheckItem", "dynamodb:UpdateItem"] && jsondecode(aws_iam_role_policy.database[0].policy).Statement[1].Condition["ForAllValues:StringLike"]["dynamodb:LeadingKeys"] == ["CASE#*"] && jsondecode(aws_iam_role_policy.database[0].policy).Statement[1].Condition["ForAnyValue:StringEquals"]["dynamodb:EnclosingOperation"] == ["TransactWriteItems"] && length(aws_iam_role_policy.workflow_start) == 0 && length(aws_iam_role_policy.outbox) == 0
    error_message = "Preparation/publication only write CASE transactions; no event or callback sending."
  }
}

run "review_command_routes" {
  command = plan
  module { source = "../../modules/api" }
  variables {
    name_prefix                  = "docflow-dev"
    client_id                    = "testclient"
    issuer                       = "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_test"
    lambda_function_name         = "docflow-dev-case-query-handler"
    lambda_invoke_arn            = "arn:aws:lambda:us-east-1:123456789012:function:case"
    review_command_function_name = "docflow-dev-review-command-handler"
    review_command_invoke_arn    = "arn:aws:lambda:us-east-1:123456789012:function:review-command"
    browser_origins              = ["http://localhost:5173"]
    log_group_arn                = "arn:aws:logs:us-east-1:123456789012:log-group:/aws/apigateway/docflow-dev-api"
  }
  override_resource {
    target          = aws_apigatewayv2_api.this
    override_during = plan
    values          = { execution_arn = "arn:aws:execute-api:us-east-1:123456789012:testapi" }
  }
  assert {
    condition     = toset([for r in aws_apigatewayv2_route.review_commands : r.route_key]) == toset(["POST /api/v1/reviews/{taskId}/decision", "POST /api/v1/reviews/{taskId}/claim", "POST /api/v1/reviews/{taskId}/start", "PUT /api/v1/reviews/{taskId}/checks/{checkId}"]) && alltrue([for r in aws_apigatewayv2_route.review_commands : r.authorization_type == "JWT" && r.authorization_scopes == toset(["aws.cognito.signin.user.admin"])])
    error_message = "Only the four task-owned commands use scoped JWT."
  }
  assert {
    condition     = contains(aws_apigatewayv2_api.this.cors_configuration[0].allow_methods, "PUT") && aws_lambda_permission.review_commands["check"].source_arn == "arn:aws:execute-api:us-east-1:123456789012:testapi/*/PUT/api/v1/reviews/*/checks/*" && aws_lambda_permission.review_commands["claim"].function_name == var.review_command_function_name && endswith(aws_lambda_permission.review_commands["start"].source_arn, "/POST/api/v1/reviews/*/start") && endswith(aws_lambda_permission.review_commands["decision"].source_arn, "/POST/api/v1/reviews/*/decision")
    error_message = "PUT CORS and route-specific command invocation required."
  }
}
run "review_command_iam" {
  command = plan
  module { source = "../../modules/lambda" }
  variables {
    function_name = "docflow-dev-review-command-handler"
    handler       = "review_api.command.handler"
    archive_path  = "../../../build/cases.zip"
    log_group_arn = "arn:aws:logs:us-east-1:123456789012:log-group:/aws/lambda/docflow-dev-review-command-handler"
    table_name    = "docflow-dev"
    table_arn     = "arn:aws:dynamodb:us-east-1:123456789012:table/docflow-dev"
    access_mode   = "review_command"
  }
  assert {
    condition     = jsondecode(aws_iam_role_policy.database[0].policy).Statement[0].Action == ["dynamodb:GetItem", "dynamodb:Query"] && jsondecode(aws_iam_role_policy.database[0].policy).Statement[0].Resource == [var.table_arn] && jsondecode(aws_iam_role_policy.database[0].policy).Statement[1].Action == ["dynamodb:PutItem", "dynamodb:ConditionCheckItem", "dynamodb:UpdateItem"] && jsondecode(aws_iam_role_policy.database[0].policy).Statement[1].Condition["ForAllValues:StringLike"]["dynamodb:LeadingKeys"] == ["CASE#*"] && jsondecode(aws_iam_role_policy.database[0].policy).Statement[1].Condition["ForAnyValue:StringEquals"]["dynamodb:EnclosingOperation"] == ["TransactWriteItems"] && length(aws_iam_role_policy.workflow_start) == 0 && length(aws_iam_role_policy.outbox) == 0 && length(aws_iam_role_policy.storage) == 0
    error_message = "Commands write only CASE transactions with no event or storage permission."
  }
  assert {
    condition     = jsondecode(aws_iam_role_policy.review_callback[0].policy).Statement == [{ Effect = "Allow", Action = ["states:SendTaskSuccess"], Resource = "*" }]
    error_message = "Only SendTaskSuccess is authorized; AWS does not support resource-level ARN for this action."
  }
}
run "review_command_dev" {
  command = plan
  assert {
    condition     = module.review_command.function_name == "docflow-dev-review-command-handler"
    error_message = "Dev must wire the planned command function to centralized logs."
  }
}
