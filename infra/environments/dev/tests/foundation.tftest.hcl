# All runs use a mock AWS provider and plan only: no AWS resources or credentials.
mock_provider "aws" {}

run "dev_composition" {
  command = plan

  assert {
    condition     = output.table_name == "docflow-dev"
    error_message = "Dev composition must use the section 6 table name."
  }

  assert {
    condition = (
      length(output.log_group_names) == 15 &&
      alltrue([for suffix in [
        "case-command-handler", "case-query-handler", "document-command-handler",
        "document-processor", "outbox-publisher", "workflow-validate-case",
        "workflow-create-review-task", "review-command-handler", "review-query-handler",
        "workflow-finalize-case", "workflow-failure-handler", "notification-worker", "operations-monitor",
      ] : contains(values(output.log_group_names), "/aws/lambda/docflow-dev-${suffix}")]) &&
      contains(values(output.log_group_names), "/aws/apigateway/docflow-dev-api") &&
      contains(values(output.log_group_names), "/aws/vendedlogs/states/docflow-dev-case-review-workflow")
    )
    error_message = "All section 8 Lambda and API/workflow log destinations must be wired into dev."
  }
}

run "database_contract" {
  command = plan

  module {
    source = "../../modules/database"
  }

  variables {
    environment = "dev"
  }

  assert {
    condition = (
      aws_dynamodb_table.this.hash_key == "PK" &&
      aws_dynamodb_table.this.range_key == "SK" &&
      toset([for attr in aws_dynamodb_table.this.attribute : "${attr.name}:${attr.type}"]) ==
      toset(["PK:S", "SK:S", "GSI1PK:S", "GSI1SK:S", "GSI2PK:S", "GSI2SK:S"])
    )
    error_message = "Physical keys must preserve Technical Design section 6; non-key fields are schemaless."
  }

  assert {
    condition = toset([
      for index in aws_dynamodb_table.this.global_secondary_index :
      "${index.name}:${join(",", [for key in index.key_schema : "${key.attribute_name}:${key.key_type}"])}:${index.projection_type}"
    ]) == toset(["GSI1:GSI1PK:HASH,GSI1SK:RANGE:ALL", "GSI2:GSI2PK:HASH,GSI2SK:RANGE:ALL"])
    error_message = "Requester/reviewer and admin access paths must retain their GSI key mappings."
  }

  assert {
    condition = (
      aws_dynamodb_table.this.stream_enabled &&
      aws_dynamodb_table.this.stream_view_type == "NEW_AND_OLD_IMAGES" &&
      aws_dynamodb_table.this.ttl[0].enabled &&
      aws_dynamodb_table.this.ttl[0].attribute_name == "expiresAtEpoch"
    )
    error_message = "Outbox stream images and idempotency/outbox expiry must match the design."
  }

  assert {
    condition = (
      aws_dynamodb_table.this.billing_mode == "PAY_PER_REQUEST" &&
      aws_dynamodb_table.this.point_in_time_recovery[0].enabled &&
      aws_dynamodb_table.this.deletion_protection_enabled
    )
    error_message = "Dev must preserve on-demand billing, PITR and default deletion protection."
  }
}

run "log_retention_override" {
  command = plan

  module {
    source = "../../modules/observability"
  }

  variables {
    log_group_names   = ["/aws/lambda/docflow-dev-case-query-handler", "/aws/apigateway/docflow-dev-api"]
    retention_in_days = 30
  }

  assert {
    condition = (
      length(aws_cloudwatch_log_group.this) == 2 &&
      alltrue([for name, group in aws_cloudwatch_log_group.this :
        group.name == name && group.retention_in_days == 30
      ])
    )
    error_message = "A supported retention override must reach every supplied log group without renaming it."
  }
}

run "reject_indefinite_retention" {
  command = plan

  module {
    source = "../../modules/observability"
  }

  variables {
    log_group_names   = ["/aws/lambda/docflow-dev-case-query-handler"]
    retention_in_days = 0
  }

  expect_failures = [var.retention_in_days]
}

run "reject_unsupported_retention" {
  command = plan

  module {
    source = "../../modules/observability"
  }

  variables {
    log_group_names   = ["/aws/lambda/docflow-dev-case-query-handler"]
    retention_in_days = 15
  }

  expect_failures = [var.retention_in_days]
}

run "reject_unknown_environment" {
  command = plan

  module {
    source = "../../modules/database"
  }

  variables {
    environment = "preview"
  }

  expect_failures = [var.environment]
}
