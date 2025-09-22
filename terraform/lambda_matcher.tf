resource "aws_lambda_function" "matcher" {
  function_name = var.prefix != "" ? "${var.prefix}-job-matcher" : "job-matcher"
  role          = aws_iam_role.matcher.arn
  package_type  = "Image"
  image_uri     = var.lambda_matcher_image_uri
  timeout       = 20
  memory_size   = 512

  environment {
    variables = {
      JOBS_TABLE_NAME = aws_dynamodb_table.jobs.name
    }
  }
}



