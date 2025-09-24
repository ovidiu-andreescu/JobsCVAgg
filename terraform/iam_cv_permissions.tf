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

resource "aws_iam_role" "cv_keywords" {
  name               = var.prefix != "" ? "${var.prefix}-cv-keywords-role" : "cv-keywords-role"
  assume_role_policy = data.aws_iam_policy_document.assume_lambda.json
}

resource "aws_iam_role_policy_attachment" "cv_keywords_cwlogs" {
  role       = aws_iam_role.cv_keywords.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

data "aws_iam_policy_document" "cv_keywords_s3_doc" {
  statement {
    actions   = ["s3:GetObject", "s3:HeadObject", "s3:PutObject", "s3:DeleteObject"]
    resources = ["${aws_s3_bucket.cv_uploads.arn}/*"]
  }
}

resource "aws_iam_policy" "cv_keywords_s3" {
  name   = var.prefix != "" ? "${var.prefix}-cv-keywords-s3" : "cv-keywords-s3"
  policy = data.aws_iam_policy_document.cv_keywords_s3_doc.json
}

resource "aws_iam_role_policy_attachment" "cv_keywords_s3_attach" {
  role       = aws_iam_role.cv_keywords.name
  policy_arn = aws_iam_policy.cv_keywords_s3.arn
}

data "aws_iam_policy_document" "cv_keywords_ddb_doc" {
  statement {
    actions   = ["dynamodb:Query", "dynamodb:Scan", "dynamodb:UpdateItem", "dynamodb:GetItem"]
    resources = [
      aws_dynamodb_table.users.arn,
      "${aws_dynamodb_table.users.arn}/index/*"
    ]
  }
}

resource "aws_iam_policy" "cv_keywords_ddb" {
  name   = var.prefix != "" ? "${var.prefix}-cv-keywords-ddb" : "cv-keywords-ddb"
  policy = data.aws_iam_policy_document.cv_keywords_ddb_doc.json
}


resource "aws_iam_role_policy_attachment" "cv_keywords_ddb_attach" {
  role       = aws_iam_role.cv_keywords.name
  policy_arn = aws_iam_policy.cv_keywords_ddb.arn
}