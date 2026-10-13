resource "aws_iam_role_policy" "database" {
  count = contains(["none", "processor", "publisher"], var.access_mode) ? 0 : 1
  name  = "case-database"
  role  = aws_iam_role.this.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = concat([
      {
        Effect   = "Allow"
        Action   = ["dynamodb:GetItem", "dynamodb:Query"]
        Resource = contains(["command", "document", "workflow", "review_creator", "review_command"], var.access_mode) ? [var.table_arn] : (var.access_mode == "review_query" ? [var.table_arn, "${var.table_arn}/index/GSI1"] : [var.table_arn, "${var.table_arn}/index/GSI1", "${var.table_arn}/index/GSI2"])
      }
      ], contains(["command", "document", "workflow", "review_creator", "review_command"], var.access_mode) ? [
      {
        Effect   = "Allow"
        Action   = contains(["document", "review_creator", "review_command"], var.access_mode) ? ["dynamodb:PutItem", "dynamodb:ConditionCheckItem", "dynamodb:UpdateItem"] : (var.access_mode == "workflow" ? ["dynamodb:PutItem", "dynamodb:UpdateItem"] : ["dynamodb:PutItem"])
        Resource = [var.table_arn]
        Condition = {
          "ForAllValues:StringLike"  = { "dynamodb:LeadingKeys" = var.access_mode == "command" ? ["CASE#*", "IDEMPOTENCY#case-submission"] : ["CASE#*"] }
          "ForAnyValue:StringEquals" = { "dynamodb:EnclosingOperation" = ["TransactWriteItems"] }
        }
      }
    ] : [])
  })
}
