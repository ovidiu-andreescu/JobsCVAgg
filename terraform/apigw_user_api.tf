
resource "aws_apigatewayv2_api" "user_api" {
  name          = var.prefix != "" ? "${var.prefix}-user-api" : "user-api"
  protocol_type = "HTTP"
}

resource "aws_apigatewayv2_integration" "user_api" {
  api_id           = aws_apigatewayv2_api.user_api.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.user_api.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "user_api_proxy" {
    api_id    = aws_apigatewayv2_api.user_api.id
  route_key = "$default"
  target    = "integrations/${aws_apigatewayv2_integration.user_api.id}"
}

resource "aws_apigatewayv2_stage" "user_default" {
  api_id      = aws_apigatewayv2_api.user_api.id
  name        = "$default"
  auto_deploy = true
}

resource "aws_lambda_permission" "user_allow_apigw" {
  statement_id  = "AllowInvokeFromUserHttpApi"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.user_api.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.user_api.execution_arn}/*/*"
}