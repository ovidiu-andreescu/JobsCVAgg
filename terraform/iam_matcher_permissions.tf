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
