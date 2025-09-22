resource "aws_lambda_function" "aggregator" {
  function_name = var.prefix != "" ? "${var.prefix}-job-aggregator" : "job-aggregator"

  role          = aws_iam_role.lambda.arn

  package_type  = "Image"
  image_uri     = var.lambda_jobs_agg_image_uri

  timeout       = 60
  memory_size   = 512
  architectures = ["x86_64"]

  environment {
    variables = merge(
      {
        SECRETS_PREFIX  = var.prefix
        JOBS_TABLE_NAME = aws_dynamodb_table.jobs.name
      },
      var.lambda_env
    )
  }

}

resource "aws_cloudwatch_event_rule" "agg" {
  count               = var.schedule_expression != "" ? 1 : 0
  name                = "${aws_lambda_function.aggregator.function_name}-schedule"
  schedule_expression = var.schedule_expression
}

resource "aws_cloudwatch_event_target" "agg" {
  count     = var.schedule_expression != "" ? 1 : 0
  rule      = aws_cloudwatch_event_rule.agg[0].name
  target_id = "lambda"
  arn       = aws_lambda_function.aggregator.arn
}