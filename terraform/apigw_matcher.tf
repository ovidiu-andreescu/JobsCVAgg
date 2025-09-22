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
