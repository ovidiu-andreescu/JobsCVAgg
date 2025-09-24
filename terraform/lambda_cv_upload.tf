resource "aws_lambda_function" "cv_upload" {
  function_name = var.prefix != "" ? "${var.prefix}-cv-upload" : "cv-upload"
  role          = aws_iam_role.cv_keywords.arn
  package_type  = "Image"
  image_uri     = var.lambda_cv_upload_image_uri
  timeout       = 60
  memory_size   = 512
  architectures = ["x86_64"]

  environment {
    variables = {
      CV_S3_BUCKET           = aws_s3_bucket.cv_uploads.bucket
      USERS_TABLE_NAME       = aws_dynamodb_table.users.name
    }
  }
}

resource "aws_lambda_permission" "cv_keywords_allow_s3" {
  statement_id  = "AllowS3InvokeCvKeywords"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.cv_upload.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.cv_uploads.arn
}
