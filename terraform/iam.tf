data "aws_iam_policy_document" "assume_lambda" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "lambda" {
  name               = var.prefix != "" ? "${var.prefix}-job-agg-lambda-role" : "job-agg-lambda-role"
  assume_role_policy = data.aws_iam_policy_document.assume_lambda.json
}

resource "aws_iam_role_policy_attachment" "cwlogs" {
  role       = aws_iam_role.lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_policy" "secrets" {
  name   = var.prefix != "" ? "${var.prefix}-job-agg-secrets-read" : "job-agg-secrets-read"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect    = "Allow",
      Action    = ["secretsmanager:GetSecretValue", "secretsmanager:DescribeSecret"],
      Resource  = local.secret_arn_patterns
    }]
  })
}

resource "aws_iam_role_policy_attachment" "attach_secrets" {
  role       = aws_iam_role.lambda.name
  policy_arn = aws_iam_policy.secrets.arn
}

# Custom policy for writing to the DynamoDB jobs table
resource "aws_iam_policy" "dynamodb_jobs_write" {
  name   = var.prefix != "" ? "${var.prefix}-job-agg-dynamodb-write" : "job-agg-dynamodb-write"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect   = "Allow",
      Action   = [
        "dynamodb:PutItem",
        "dynamodb:UpdateItem",
        "dynamodb:BatchWriteItem"
      ],
      Resource = aws_dynamodb_table.jobs.arn
    }]
  })
}

resource "aws_iam_role_policy_attachment" "attach_dynamodb_write" {
  role       = aws_iam_role.lambda.name
  policy_arn = aws_iam_policy.dynamodb_jobs_write.arn
}

