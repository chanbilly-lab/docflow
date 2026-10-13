resource "aws_cognito_user_pool" "this" {
  name                = "${var.name_prefix}-users"
  user_pool_tier      = "LITE"
  deletion_protection = "ACTIVE"
  mfa_configuration   = "OFF"

  admin_create_user_config {
    allow_admin_create_user_only = true
  }

  password_policy {
    minimum_length                   = 14
    require_lowercase                = true
    require_uppercase                = true
    require_numbers                  = true
    require_symbols                  = true
    temporary_password_validity_days = 1
  }

  tags = { Name = "${var.name_prefix}-users" }
}

resource "aws_cognito_user_pool_client" "this" {
  name                          = "${var.name_prefix}-web"
  user_pool_id                  = aws_cognito_user_pool.this.id
  generate_secret               = false
  explicit_auth_flows           = ["ALLOW_USER_SRP_AUTH", "ALLOW_REFRESH_TOKEN_AUTH"]
  prevent_user_existence_errors = "ENABLED"
  enable_token_revocation       = true
  access_token_validity         = 15
  id_token_validity             = 15
  refresh_token_validity        = 1
  supported_identity_providers  = ["COGNITO"]
  read_attributes               = ["sub"]
  write_attributes              = []

  token_validity_units {
    access_token  = "minutes"
    id_token      = "minutes"
    refresh_token = "days"
  }
}

resource "aws_cognito_user_group" "this" {
  for_each     = toset(["requester", "reviewer", "admin"])
  name         = each.value
  user_pool_id = aws_cognito_user_pool.this.id
}
