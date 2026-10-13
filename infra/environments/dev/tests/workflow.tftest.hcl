mock_provider "aws" {}

run "standard_definition" {
  command = plan
  module { source = "../../modules/workflow" }
  variables {
    name          = "docflow-dev-case-review-workflow"
    validate_arn  = "arn:aws:lambda:us-east-1:123456789012:function:validate"
    failure_arn   = "arn:aws:lambda:us-east-1:123456789012:function:failure"
    review_arn    = "arn:aws:lambda:us-east-1:123456789012:function:review"
    finalize_arn  = "arn:aws:lambda:us-east-1:123456789012:function:finalize"
    log_group_arn = "arn:aws:logs:us-east-1:123456789012:log-group:/aws/vendedlogs/states/docflow-dev-case-review-workflow"
  }
  assert {
    condition     = aws_sfn_state_machine.this.tracing_configuration[0].enabled && length(jsondecode(aws_iam_role.this.assume_role_policy).Statement) == 1 && contains(jsondecode(aws_iam_role_policy.this.policy).Statement[2].Action, "xray:PutTraceSegments") && aws_sfn_state_machine.this.type == "STANDARD" && aws_sfn_state_machine.this.logging_configuration[0].include_execution_data == false
    error_message = "Use Standard, with no payload logging."
  }
  assert {
    condition     = jsondecode(aws_sfn_state_machine.this.definition).States.ValidateCase.Parameters.FunctionName == var.validate_arn && jsondecode(aws_sfn_state_machine.this.definition).States.MarkWorkflowFailed.Parameters.FunctionName == var.failure_arn && jsondecode(aws_sfn_state_machine.this.definition).States.MarkWorkflowFailed.Parameters.Payload["submission.$"] == "$$.Execution.Input"
    error_message = "Invoke real workers and retain original identity on Catch."
  }
  assert {
    condition     = jsondecode(aws_iam_role_policy.this.policy).Statement[0].Resource == [var.validate_arn, var.failure_arn, var.review_arn, var.finalize_arn] && jsondecode(aws_sfn_state_machine.this.definition).States.Failed.Type == "Fail"
    error_message = "Exact task IAM and technical failure terminal required."
  }
  assert {
    condition     = jsondecode(aws_sfn_state_machine.this.definition).States.CreateReviewTaskAndWait.Resource == "arn:aws:states:::lambda:invoke.waitForTaskToken" && jsondecode(aws_sfn_state_machine.this.definition).States.CreateReviewTaskAndWait.Parameters.FunctionName == var.review_arn && jsondecode(aws_sfn_state_machine.this.definition).States.CreateReviewTaskAndWait.Parameters.Payload["taskToken.$"] == "$$.Task.Token" && jsondecode(aws_sfn_state_machine.this.definition).States.CreateReviewTaskAndWait.TimeoutSeconds == 1209600 && jsondecode(aws_sfn_state_machine.this.definition).States.CreateReviewTaskAndWait.Retry[0].ErrorEquals == ["States.TaskFailed"] && jsondecode(aws_sfn_state_machine.this.definition).States.CreateReviewTaskAndWait.Catch[0].Next == "MarkWorkflowFailed"
    error_message = "Trusted callback, bounded non-timeout retry and technical timeout recovery required."
  }

  assert {
    condition     = jsondecode(aws_sfn_state_machine.this.definition).States.CreateReviewTaskAndWait.Next == "DecisionChoice" && length(jsondecode(aws_sfn_state_machine.this.definition).States.DecisionChoice.Choices) == 3 && alltrue([for name in ["FinalizeApproved", "FinalizeRejected", "FinalizeNeedsInformation"] : jsondecode(aws_sfn_state_machine.this.definition).States[name].Parameters.FunctionName == var.finalize_arn && jsondecode(aws_sfn_state_machine.this.definition).States[name].Parameters.Payload["submission.$"] == "$$.Execution.Input" && jsondecode(aws_sfn_state_machine.this.definition).States[name].Catch[0].Next == "MarkWorkflowFailed"])
    error_message = "All decisions must finalize with original attempt context and technical failure recovery."
  }
}
run "starter_scope" {
  command = plan
  module { source = "../../modules/lambda" }
  variables {
    function_name       = "docflow-dev-case-command-handler"
    archive_path        = "../../../build/cases.zip"
    handler             = "case_api.command.handler"
    log_group_arn       = "arn:aws:logs:us-east-1:123456789012:log-group:/aws/lambda/docflow-dev-case-command-handler"
    table_name          = "docflow-dev"
    table_arn           = "arn:aws:dynamodb:us-east-1:123456789012:table/docflow-dev"
    access_mode         = "command"
    workflow_enabled    = true
    workflow_arn        = "arn:aws:states:us-east-1:123456789012:stateMachine:docflow-dev-case-review-workflow"
    workflow_stream_arn = "arn:aws:dynamodb:us-east-1:123456789012:table/docflow-dev/stream/test"
  }
  assert {
    condition     = aws_lambda_function.this.environment[0].variables.WORKFLOW_ARN == var.workflow_arn && jsondecode(aws_iam_role_policy.workflow_start[0].policy).Statement[0].Resource == var.workflow_arn && jsondecode(aws_iam_role_policy.workflow_start[0].policy).Statement[1].Resource == "arn:aws:states:us-east-1:123456789012:execution:docflow-dev-case-review-workflow:case-*"
    error_message = "Start/describe must target only the configured workflow."
  }
  assert {
    condition     = aws_lambda_event_source_mapping.workflow_start[0].event_source_arn == var.workflow_stream_arn && aws_lambda_event_source_mapping.workflow_start[0].function_response_types == toset(["ReportBatchItemFailures"]) && jsondecode(one(aws_lambda_event_source_mapping.workflow_start[0].filter_criteria[0].filter).pattern).dynamodb.NewImage.workflowStartStatus.S == ["PENDING"]
    error_message = "Recover pending intents with partial stream checkpoints."
  }
}
run "worker_scope" {
  command = plan
  module { source = "../../modules/lambda" }
  variables {
    function_name = "docflow-dev-workflow-validate-case"
    archive_path  = "../../../build/cases.zip"
    handler       = "workflow_validate_case.handler.handler"
    log_group_arn = "arn:aws:logs:us-east-1:123456789012:log-group:/aws/lambda/docflow-dev-workflow-validate-case"
    table_name    = "docflow-dev"
    table_arn     = "arn:aws:dynamodb:us-east-1:123456789012:table/docflow-dev"
    access_mode   = "workflow"
  }
  assert {
    condition     = length(aws_iam_role_policy.workflow_start) == 0 && length(aws_iam_role_policy.outbox) == 0 && jsondecode(aws_iam_role_policy.database[0].policy).Statement[1].Action == ["dynamodb:PutItem", "dynamodb:UpdateItem"] && jsondecode(aws_iam_role_policy.database[0].policy).Statement[1].Condition["ForAnyValue:StringEquals"]["dynamodb:EnclosingOperation"] == ["TransactWriteItems"] && jsondecode(aws_iam_role_policy.database[0].policy).Statement[1].Condition["ForAllValues:StringLike"]["dynamodb:LeadingKeys"] == ["CASE#*"]
    error_message = "Workers only mutate CASE transactions and never publish or callback."
  }
}
run "dev_workflow" {
  command = plan
  assert {
    condition     = module.workflow_validate.function_name == "docflow-dev-workflow-validate-case" && module.workflow_failure.function_name == "docflow-dev-workflow-failure-handler" && module.workflow_create_review.function_name == "docflow-dev-workflow-create-review-task" && module.review_query.function_name == "docflow-dev-review-query-handler"
    error_message = "Dev must wire the planned workers and review query."
  }
}
