provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "docflow"
      Environment = "dev"
      ManagedBy   = "terraform"
    }
  }
}

locals {
  name_prefix = "docflow-dev"
  # Technical Design section 8 function names. Later Lambda modules must use
  # these names and depend on the pre-created log groups.
  lambda_names = toset([
    "case-command-handler",
    "case-query-handler",
    "document-command-handler",
    "document-processor",
    "outbox-publisher",
    "workflow-validate-case",
    "workflow-create-review-task",
    "review-command-handler",
    "review-query-handler",
    "workflow-finalize-case",
    "workflow-failure-handler",
    "notification-worker",
    "operations-monitor",
  ])
  log_group_names = setunion(
    toset([for name in local.lambda_names : "/aws/lambda/${local.name_prefix}-${name}"]),
    toset([
      "/aws/apigateway/${local.name_prefix}-api",
      "/aws/vendedlogs/states/${local.name_prefix}-case-review-workflow",
    ]),
  )
}

module "database" {
  source = "../../modules/database"

  environment                 = "dev"
  deletion_protection_enabled = var.database_deletion_protection_enabled
}

module "observability" {
  source = "../../modules/observability"

  log_group_names   = local.log_group_names
  retention_in_days = var.log_retention_in_days
}
