resource "aws_lambda_function" "this" {
  function_name = var.prefix != "" ? "${var.prefix}-job-aggregator" : "job-aggregator"

  role          = aws_iam_role.lambda.arn

  package_type  = "Image"
  image_uri     = var.lambda_image_uri

  timeout       = 30
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
  name                = "${aws_lambda_function.this.function_name}-schedule"
  schedule_expression = var.schedule_expression
}

resource "aws_cloudwatch_event_target" "agg" {
  count     = var.schedule_expression != "" ? 1 : 0
  rule      = aws_cloudwatch_event_rule.agg[0].name
  target_id = "lambda"
  arn       = aws_lambda_function.this.arn
}

resource "aws_lambda_permission" "events" {
  count         = var.schedule_expression != "" ? 1 : 0
  statement_id  = "AllowEventBridgeInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.this.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.agg[0].arn
}

