resource "aws_iam_role_policy" "storage" {
  count = var.access_mode == "document" ? 1 : 0
  name  = "document-upload-only"
  role  = aws_iam_role.this.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["s3:PutObject"]
      Resource = "${var.document_bucket_arn}/cases/*/documents/*/v1/source"
    }]
  })
}
