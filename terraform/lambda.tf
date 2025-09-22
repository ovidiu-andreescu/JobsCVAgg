resource "aws_lambda_function" "aggregator" {
  function_name = var.prefix != "" ? "${var.prefix}-job-aggregator" : "job-aggregator"

  role          = aws_iam_role.lambda.arn

  package_type  = "Image"
  image_uri     = var.lambda_image_uri

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

resource "aws_lambda_permission" "events" {
  count         = var.schedule_expression != "" ? 1 : 0
  statement_id  = "AllowEventBridgeInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.aggregator.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.agg[0].arn
}

resource "aws_apigatewayv2_api" "matcher" {
  name          = var.prefix != "" ? "${var.prefix}-job-matcher-api" : "job-matcher-api"
  protocol_type = "HTTP"
}

resource "aws_apigatewayv2_stage" "matcher" {
  api_id      = aws_apigatewayv2_api.matcher.id
  name        = "$default"
  auto_deploy = true
}

resource "aws_apigatewayv2_integration" "matcher" {
  api_id           = aws_apigatewayv2_api.matcher.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.matcher.invoke_arn
}

resource "aws_apigatewayv2_route" "matcher" {
  api_id    = aws_apigatewayv2_api.matcher.id
  # We use POST to send a JSON body with the keywords
  route_key = "POST /match"
  target    = "integrations/${aws_apigatewayv2_integration.matcher.id}"
}

resource "aws_lambda_permission" "matcher_api_gateway" {
  statement_id  = "AllowAPIGatewayInvokeMatcher"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.matcher.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.matcher.execution_arn}/*/*"
}
