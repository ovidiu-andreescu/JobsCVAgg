resource "aws_s3_bucket" "cv_uploads" {
  bucket = var.prefix != "" ? "${var.prefix}-cv-upload" : "cv-upload"

  tags = {
    Project   = "CVHandling"
    ManagedBy = "Terraform"
  }
}
resource "aws_s3_bucket_versioning" "cv" {
  bucket = aws_s3_bucket.cv_uploads.id
  versioning_configuration { status = "Enabled" }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "cv" {
  bucket = aws_s3_bucket.cv_uploads.id
  rule {
    apply_server_side_encryption_by_default { sse_algorithm = "AES256" }
  }
}

resource "aws_iam_role_policy_attachment" "cv_upload_cwlogs" {
  role       = aws_iam_role.cv_upload.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_s3_bucket_public_access_block" "cv" {
  bucket = aws_s3_bucket.cv_uploads.id
  block_public_acls = true
  block_public_policy = true
  ignore_public_acls = true
  restrict_public_buckets = true
}

resource "aws_iam_role_policy_attachment" "cv_upload_misc_attach" {
  role       = aws_iam_role.cv_upload.name
  policy_arn = aws_iam_policy.lambda_misc.arn
}

resource "aws_s3_bucket_lifecycle_configuration" "cv" {
  bucket = aws_s3_bucket.cv_uploads.id
  rule {
    id = "expire-tmp"
    status = "Enabled"
    filter {}
    expiration { days = 365 }
  }
}

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