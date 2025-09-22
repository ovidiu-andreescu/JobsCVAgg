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