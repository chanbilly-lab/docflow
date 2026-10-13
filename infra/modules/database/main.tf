resource "aws_dynamodb_table" "this" {
  name                        = "docflow-${var.environment}"
  billing_mode                = "PAY_PER_REQUEST"
  hash_key                    = "PK"
  range_key                   = "SK"
  deletion_protection_enabled = var.deletion_protection_enabled
  stream_enabled              = true
  stream_view_type            = "NEW_AND_OLD_IMAGES"

  # Only declare key attributes. Business fields and expiresAtEpoch remain
  # schemaless, as specified in Technical Design section 6.
  dynamic "attribute" {
    for_each = toset(["PK", "SK", "GSI1PK", "GSI1SK", "GSI2PK", "GSI2SK"])
    content {
      name = attribute.value
      type = "S"
    }
  }

  global_secondary_index {
    name            = "GSI1"
    projection_type = "ALL"

    key_schema {
      attribute_name = "GSI1PK"
      key_type       = "HASH"
    }

    key_schema {
      attribute_name = "GSI1SK"
      key_type       = "RANGE"
    }
  }

  global_secondary_index {
    name            = "GSI2"
    projection_type = "ALL"

    key_schema {
      attribute_name = "GSI2PK"
      key_type       = "HASH"
    }

    key_schema {
      attribute_name = "GSI2SK"
      key_type       = "RANGE"
    }
  }

  ttl {
    attribute_name = "expiresAtEpoch"
    enabled        = true
  }

  point_in_time_recovery {
    enabled = true
  }

  # Default AWS-owned encryption protects the table and indexes at rest.
  # Customer-managed KMS keys require a separate security decision.
  tags = {
    Name = "docflow-${var.environment}"
  }
}
