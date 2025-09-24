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

resource "aws_s3_bucket_public_access_block" "cv" {
  bucket = aws_s3_bucket.cv_uploads.id
  block_public_acls = true
  block_public_policy = true
  ignore_public_acls = true
  restrict_public_buckets = true
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

resource "aws_s3_bucket_cors_configuration" "cv_cors" {
  bucket = aws_s3_bucket.cv_uploads.id

  cors_rule {
    id              = "frontend-upload"
    allowed_methods = ["POST", "PUT", "GET", "HEAD"]
    allowed_origins = ["*"]
    allowed_headers = ["*"]
    expose_headers  = ["ETag", "Location", "x-amz-request-id", "x-amz-version-id"]
    max_age_seconds = 3000
  }
}

resource "aws_s3_bucket_notification" "cv_uploads_events" {
  bucket = aws_s3_bucket.cv_uploads.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.cv_upload.arn
    events = ["s3:ObjectCreated:*"]
    filter_prefix       = ""
    filter_suffix       = ".pdf"
  }
}
