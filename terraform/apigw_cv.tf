resource "aws_apigatewayv2_api" "cv_api" {
  name          = "${var.prefix}-cv-api"
  protocol_type = "HTTP"
  cors_configuration {
    allow_origins = ["*"]
    allow_methods = ["GET","POST","PUT","OPTIONS"]
    allow_headers = ["authorization","content-type"]
    expose_headers = ["etag"]
    max_age = 3600
  }
}

resource "aws_cloudwatch_log_group" "apigw_cv" {
  name = "/aws/apigw/${var.prefix}-cv"
  retention_in_days = 14
}

resource "aws_apigatewayv2_stage" "cv" {
  api_id      = aws_apigatewayv2_api.cv_api.id
  name        = "$default"
  auto_deploy = true

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.apigw_cv.arn
    format = jsonencode({
      requestId         = "$context.requestId"
      ip                = "$context.identity.sourceIp"
      requestTime       = "$context.requestTime"
      httpMethod        = "$context.httpMethod"
      routeKey          = "$context.routeKey"
      status            = "$context.status"
      protocol          = "$context.protocol"
      responseLength    = "$context.responseLength"
      integrationError  = "$context.integrationErrorMessage"
    })
  }
}

resource "aws_apigatewayv2_integration" "cv_lambda" {
  api_id                 = aws_apigatewayv2_api.cv_api.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.cv_upload.invoke_arn
  payload_format_version = "2.0"
}

# proxy everything to FastAPI
resource "aws_apigatewayv2_route" "cv_proxy" {
  api_id    = aws_apigatewayv2_api.cv_api.id
  route_key = "$default"
  target    = "integrations/${aws_apigatewayv2_integration.cv_lambda.id}"
}

resource "aws_lambda_permission" "cv_allow_apigw" {
  statement_id  = "AllowInvokeFromCvHttpApi"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.cv_upload.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.cv_api.execution_arn}/*/*"
}
