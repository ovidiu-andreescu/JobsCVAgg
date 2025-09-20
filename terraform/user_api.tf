resource "aws_dynamodb_table" "users" {
  name         = var.prefix != "" ? "${var.prefix}-users" : "users"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "email"

  attribute {
    name = "email"
    type = "S"
  }
  tags = { Project = "JobAggregator", ManagedBy = "Terraform" }
}

resource "aws_secretsmanager_secret" "jwt_secret" {
  name        = var.prefix != "" ? "${var.prefix}/jwt-secret-key" : "jwt-secret-key"
  description = "Secret key for signing JWTs, managed by Terraform."
}

resource "random_password" "jwt_secret_value" {
  length           = 32
  special          = true
  override_special = "!#$%&*()-_=+[]{}<>:?"
}

resource "aws_secretsmanager_secret_version" "jwt_secret_initial_version" {
  secret_id     = aws_secretsmanager_secret.jwt_secret.id
  secret_string = random_password.jwt_secret_value.result
}


resource "aws_lambda_function" "user_api" {
  function_name = var.prefix != "" ? "${var.prefix}-user-api" : "user-api"
  role          = aws_iam_role.user_api.arn
  package_type  = "Image"
  image_uri     = var.lambda_user_api_image_uri
  timeout       = 15
  memory_size   = 256

  environment {
    variables = {
      USERS_TABLE_NAME = aws_dynamodb_table.users.name
      # This now correctly and safely reads the value from the version we just created.
      JWT_SECRET_KEY   = aws_secretsmanager_secret_version.jwt_secret_initial_version.secret_string
    }
  }
}



resource "aws_iam_role" "user_api" {
  name               = var.prefix != "" ? "${var.prefix}-user-api-role" : "user-api-role"
  assume_role_policy = data.aws_iam_policy_document.assume_lambda.json
}

resource "aws_iam_role_policy_attachment" "user_api_cwlogs" {
  role       = aws_iam_role.user_api.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_policy" "user_api_permissions" {
  name   = var.prefix != "" ? "${var.prefix}-user-api-permissions" : "user-api-permissions"
  policy = jsonencode({
    Version   = "2012-10-17",
    Statement = [
      {
        Effect   = "Allow",
        Action   = ["dynamodb:PutItem", "dynamodb:GetItem"],
        Resource = aws_dynamodb_table.users.arn
      },
      {
        Effect   = "Allow",
        Action   = ["secretsmanager:GetSecretValue"],
        Resource = "${aws_secretsmanager_secret.jwt_secret.arn}*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "user_api_permissions_attach" {
  role       = aws_iam_role.user_api.name
  policy_arn = aws_iam_policy.user_api_permissions.arn
}

resource "aws_apigatewayv2_api" "user_api" {
  name          = var.prefix != "" ? "${var.prefix}-user-api" : "user-api"
  protocol_type = "HTTP"
}

resource "aws_apigatewayv2_stage" "user_api" {
  api_id      = aws_apigatewayv2_api.user_api.id
  name        = "$default"
  auto_deploy = true
}

resource "aws_apigatewayv2_integration" "user_api" {
  api_id           = aws_apigatewayv2_api.user_api.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.user_api.invoke_arn
}

resource "aws_apigatewayv2_route" "user_api_proxy" {
  api_id    = aws_apigatewayv2_api.user_api.id
  route_key = "$default"
  target    = "integrations/${aws_apigatewayv2_integration.user_api.id}"
}

resource "aws_lambda_permission" "user_api_gateway_permission" {
  statement_id  = "AllowAPIGatewayInvokeUserAPI"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.user_api.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.user_api.execution_arn}/*/*"
}