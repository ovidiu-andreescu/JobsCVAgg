resource "aws_iam_policy" "user_api_permissions" {
  name = "${var.prefix}-user-api-permissions"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect   = "Allow",
        Action   = [
          "dynamodb:PutItem",
          "dynamodb:GetItem",
          "dynamodb:UpdateItem",
          "dynamodb:Query",
          "dynamodb:Scan"],
        Resource = [
          aws_dynamodb_table.users.arn,
          "${aws_dynamodb_table.users.arn}/index/*",
          aws_dynamodb_table.jobs.arn                       # ← add this
          # if Jobs has GSIs and you’ll ever Query them:
          # "${aws_dynamodb_table.jobs.arn}/index/*"
        ]
      },

      {
        Effect   = "Allow",
        Action   = ["secretsmanager:GetSecretValue","secretsmanager:DescribeSecret"],
        Resource = aws_secretsmanager_secret.jwt_secret.arn
      },

      {
        Effect    = "Allow",
        Action    = ["s3:ListBucket"],
        Resource  = aws_s3_bucket.cv_uploads.arn,
        Condition = {
          StringLike = { "s3:prefix" = [ "cv_keywords/*" ] }
        }
      },
      {
        Effect   = "Allow",
        Action   = ["s3:GetObject"],
        Resource = "${aws_s3_bucket.cv_uploads.arn}/cv_keywords/*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "user_api_permissions_attach" {
  role       = aws_iam_role.user_api.name
  policy_arn = aws_iam_policy.user_api_permissions.arn
}

resource "aws_iam_role" "user_api" {
  name               = var.prefix != "" ? "${var.prefix}-user-api-role" : "user-api-role"
  assume_role_policy = data.aws_iam_policy_document.assume_lambda.json
}

resource "aws_iam_role_policy_attachment" "user_api_cwlogs" {
  role       = aws_iam_role.user_api.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_policy" "cv_upload_putobject" {
  name        = "${var.prefix}-cv-upload-putobject"
  description = "Allow user-api to upload under uploads/ (presigned POST/MPU)"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Sid       = "ListBucketMultipart",
        Effect    = "Allow",
        Action    = ["s3:ListBucketMultipartUploads"],
        Resource  = aws_s3_bucket.cv_uploads.arn,
        Condition = { StringLike = { "s3:prefix" = [ "uploads/*" ] } }
      },
      {
        Sid     = "PutUploads",
        Effect  = "Allow",
        Action  = [
          "s3:PutObject",
          "s3:AbortMultipartUpload",
          "s3:ListMultipartUploadParts"
        ],
        Resource = "${aws_s3_bucket.cv_uploads.arn}/uploads/*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "user_api_attach_s3_put" {
  role       = aws_iam_role.user_api.name
  policy_arn = aws_iam_policy.cv_upload_putobject.arn
}