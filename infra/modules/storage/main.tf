resource "aws_s3_bucket" "documents" {
  bucket_prefix = "${var.name_prefix}-documents-"
  force_destroy = false
}
resource "aws_s3_bucket_public_access_block" "documents" {
  bucket                  = aws_s3_bucket.documents.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
resource "aws_s3_bucket_ownership_controls" "documents" {
  bucket = aws_s3_bucket.documents.id
  rule { object_ownership = "BucketOwnerEnforced" }
}
resource "aws_s3_bucket_server_side_encryption_configuration" "documents" {
  bucket = aws_s3_bucket.documents.id
  rule {
    apply_server_side_encryption_by_default { sse_algorithm = "AES256" }
  }
}
resource "aws_s3_bucket_cors_configuration" "documents" {
  bucket = aws_s3_bucket.documents.id
  cors_rule {
    allowed_origins = var.allowed_origins
    allowed_methods = ["PUT"]
    allowed_headers = ["content-type", "content-length", "if-none-match"]
    expose_headers  = ["ETag"]
    max_age_seconds = 600
  }
}
resource "aws_s3_bucket_policy" "documents" {
  bucket = aws_s3_bucket.documents.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "RequireTLS"
        Effect    = "Deny"
        Principal = "*"
        Action    = "s3:*"
        Resource  = [aws_s3_bucket.documents.arn, "${aws_s3_bucket.documents.arn}/*"]
        Condition = { Bool = { "aws:SecureTransport" = "false" } }
      },
      {
        Sid       = "RequireCreateOnly"
        Effect    = "Deny"
        Principal = "*"
        Action    = "s3:PutObject"
        Resource  = "${aws_s3_bucket.documents.arn}/cases/*/documents/*/v1/source"
        Condition = { Null = { "s3:if-none-match" = "true" } }
      },
      {
        Sid       = "BoundSignatureAge"
        Effect    = "Deny"
        Principal = "*"
        Action    = "s3:PutObject"
        Resource  = "${aws_s3_bucket.documents.arn}/*"
        Condition = { NumericGreaterThan = { "s3:signatureAge" = "600000" } }
      }
    ]
  })
  depends_on = [aws_s3_bucket_public_access_block.documents]
}
