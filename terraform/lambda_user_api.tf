resource "aws_lambda_function" "user_api" {
  function_name = var.prefix != "" ? "${var.prefix}-user-api" : "user-api"
  role          = aws_iam_role.user_api.arn
  package_type  = "Image"
  image_uri     = var.lambda_user_api_image_uri
  timeout       = 15
  memory_size   = 256

  environment {
    variables = merge({
      JOBS_TABLE_NAME = aws_dynamodb_table.jobs.name
      USERS_TABLE_NAME = aws_dynamodb_table.users.name
      CV_S3_BUCKET     = aws_s3_bucket.cv_uploads.bucket
      JWT_SECRET_KEY   = aws_secretsmanager_secret_version.jwt_secret_initial_version.secret_string
    },
      var.lambda_env
    )
  }
}

