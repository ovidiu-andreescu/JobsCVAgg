resource "aws_iam_role" "lambda" {
  name               = var.prefix != "" ? "${var.prefix}-job-agg-lambda-role" : "job-agg-lambda-role"
  assume_role_policy = jsonencode({
    Version   = "2012-10-17",
    Statement = [{
      Action    = "sts:AssumeRole",
      Effect    = "Allow",
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "cwlogs" {
  role       = aws_iam_role.lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_policy" "secrets" {
  name   = var.prefix != "" ? "${var.prefix}-job-agg-secrets-read" : "job-agg-secrets-read"
  policy = jsonencode({
    Version   = "2012-10-17",
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

resource "aws_iam_policy" "dynamodb_jobs_write" {
  name   = var.prefix != "" ? "${var.prefix}-job-agg-dynamodb-write" : "job-agg-dynamodb-write"
  policy = jsonencode({
    Version   = "2012-10-17",
    Statement = [{
      Effect    = "Allow",
      Action    = [
        "dynamodb:PutItem",
        "dynamodb:UpdateItem",
        "dynamodb:BatchWriteItem"
      ],
      # It can only write to the specific 'jobs' table.
      Resource  = aws_dynamodb_table.jobs.arn
    }]
  })
}

resource "aws_iam_role_policy_attachment" "attach_dynamodb_write" {
  role       = aws_iam_role.lambda.name
  policy_arn = aws_iam_policy.dynamodb_jobs_write.arn
}

resource "aws_iam_role" "matcher" {
  name               = var.prefix != "" ? "${var.prefix}-job-matcher-role" : "job-matcher-role"
  assume_role_policy = data.aws_iam_policy_document.assume_lambda.json
}

resource "aws_iam_role_policy_attachment" "matcher_cwlogs" {
  role       = aws_iam_role.matcher.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_policy" "matcher_dynamodb_read" {
  name   = var.prefix != "" ? "${var.prefix}-job-matcher-dynamodb-read" : "job-matcher-dynamodb-read"
  policy = jsonencode({
    Version   = "2012-10-17",
    Statement = [{
      Effect    = "Allow",
      Action    = ["dynamodb:Scan"], # Scan is needed to read all jobs
      Resource  = aws_dynamodb_table.jobs.arn
    }]
  })
}

resource "aws_iam_role_policy_attachment" "matcher_dynamodb_read_attach" {
  role       = aws_iam_role.matcher.name
  policy_arn = aws_iam_policy.matcher_dynamodb_read.arn
}

data "aws_iam_policy_document" "assume_lambda" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

