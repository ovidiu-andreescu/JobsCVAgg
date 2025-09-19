resource "aws_cloudwatch_event_rule" "agg" {
  count               = var.schedule_expression != "" ? 1 : 0
  name                = local.lambda_name
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
