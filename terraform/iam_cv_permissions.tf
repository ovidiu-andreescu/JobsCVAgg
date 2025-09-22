# Role for CV upload Lambda
resource "aws_iam_role" "cv_upload" {
  name               = var.prefix != "" ? "${var.prefix}-cv-upload-role" : "cv-upload-role"
  assume_role_policy = data.aws_iam_policy_document.assume_lambda.json
}

# Basic logs
resource "aws_iam_role_policy_attachment" "cv_upload_cwlogs" {
  role       = aws_iam_role.cv_upload.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

data "aws_iam_policy_document" "cv_bucket_rw_doc" {
  statement {
    actions = ["s3:PutObject","s3:GetObject","s3:HeadObject","s3:DeleteObject"]
    resources = ["${aws_s3_bucket.cv_uploads.arn}/*"]
  }
  statement {
    actions = ["s3:ListBucket"]
    resources = [aws_s3_bucket.cv_uploads.arn]
  }
}

resource "aws_iam_policy" "cv_bucket_rw" {
  name   = var.prefix != "" ? "${var.prefix}-cv-bucket-rw" : "cv-bucket-rw"
  policy = data.aws_iam_policy_document.cv_bucket_rw_doc.json
}

resource "aws_iam_role_policy_attachment" "cv_bucket_rw_attach" {
  role       = aws_iam_role.cv_upload.name
  policy_arn = aws_iam_policy.cv_bucket_rw.arn
}

data "aws_iam_policy_document" "cv_secrets_doc" {
  statement {
    actions   = ["secretsmanager:GetSecretValue","secretsmanager:DescribeSecret"]
    resources = [aws_secretsmanager_secret.cv_s3_bucket.arn]
  }
}

resource "aws_iam_policy" "cv_secrets" {
  name   = var.prefix != "" ? "${var.prefix}-cv-secrets-ro" : "cv-secrets-ro"
  policy = data.aws_iam_policy_document.cv_secrets_doc.json
}

resource "aws_iam_role_policy_attachment" "cv_secrets_attach" {
  role       = aws_iam_role.cv_upload.name
  policy_arn = aws_iam_policy.cv_secrets.arn
}
