resource "aws_iam_role_policy" "review_callback" {
  count = var.access_mode == "review_command" ? 1 : 0
  role  = aws_iam_role.this.id
  name  = "deliver-persisted-review-decision"
  policy = jsonencode({
    Version   = "2012-10-17"
    Statement = [{ Effect = "Allow", Action = ["states:SendTaskSuccess"], Resource = "*" }]
  })
}
