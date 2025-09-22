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