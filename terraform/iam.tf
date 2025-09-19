data "aws_iam_policy_document" "assume_lambda" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "lambda" {
  name               = var.prefix != "" ? "${var.prefix}-job-agg-lambda-role" : "job-agg-lambda-role"
  assume_role_policy = data.aws_iam_policy_document.assume_lambda.json
}
# match all versions/stages of this secret
# CloudWatch Logs
resource "aws_iam_role_policy_attachment" "cwlogs" {
  role       = aws_iam_role.lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# SecretsManager least-privilege
data "aws_iam_policy_document" "secrets" {
  statement {
    sid     = "ReadSecretsManager"
    actions = ["secretsmanager:GetSecretValue", "secretsmanager:DescribeSecret"]
    resources = local.secret_arn_patterns != [] ? local.secret_arn_patterns : ["*"]
  }

  dynamic "statement" {
    for_each = var.kms_key_id == null ? [] : [1]
    content {
      sid       = "KMSDecryptForSecrets"
      actions   = ["kms:Decrypt"]
      resources = [var.kms_key_id]
    }
  }
}

resource "aws_iam_policy" "secrets" {
  name   = var.prefix != "" ? "${var.prefix}-job-agg-secrets-read" : "job-agg-secrets-read"
  policy = data.aws_iam_policy_document.secrets.json
}

resource "aws_iam_role_policy_attachment" "attach_secrets" {
  role       = aws_iam_role.lambda.name
  policy_arn = aws_iam_policy.secrets.arn
}

data "aws_iam_policy_document" "dynamodb_jobs_write" {
  statement {
    sid = "AllowWriteToJobsTable"
    actions = [
      "dynamodb:PutItem",
      "dynamodb:UpdateItem",
      "dynamodb:BatchWriteItem"
    ]
    resources = [aws_dynamodb_table.jobs.arn]
  }
}

resource "aws_iam_policy" "dynamodb_jobs_write" {
  name   = var.prefix != "" ? "${var.prefix}-job-agg-dynamodb-write" : "job-agg-dynamodb-write"
  policy = data.aws_iam_policy_document.dynamodb_jobs_write.json
}

resource "aws_iam_role_policy_attachment" "attach_dynamodb_write" {
  role       = aws_iam_role.lambda.name
  policy_arn = aws_iam_policy.dynamodb_jobs_write.arn
}