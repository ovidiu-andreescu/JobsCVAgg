resource "aws_lambda_function" "cv_upload" {
  function_name = var.prefix != "" ? "${var.prefix}-cv-upload" : "cv-upload"
  role          = aws_iam_role.cv_upload.arn
  package_type  = "Image"
  image_uri     = var.lambda_cv_upload_image_uri
  timeout       = 30
  memory_size   = 512
  architectures = ["x86_64"]

  environment {
    variables = {
      CV_S3_BUCKET = aws_s3_bucket.cv_uploads.bucket
    }
  }
}
