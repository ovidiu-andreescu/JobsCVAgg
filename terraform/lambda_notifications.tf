resource "aws_cloudwatch_log_group" "notif_logs" {
  name              = "/aws/lambda/${var.prefix}-notifications"
  retention_in_days = 14
}

resource "aws_iam_role" "notif_role" {
  name               = "${var.prefix}-notifications-lambda-role"
  assume_role_policy = data.aws_iam_policy_document.assume_lambda.json
}

resource "aws_iam_role_policy_attachment" "notif_logs_attach" {
  role       = aws_iam_role.notif_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_policy" "notif_ses_policy" {
  name   = "${var.prefix}-notifications-ses-send"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect   = "Allow",
      Action   = ["ses:SendEmail","ses:SendRawEmail"],
      Resource = "*"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "notif_ses_attach" {
  role       = aws_iam_role.notif_role.name
  policy_arn = aws_iam_policy.notif_ses_policy.arn
}

resource "aws_lambda_function" "notifications" {
  function_name = "${var.prefix}-notifications"
  role          = aws_iam_role.notif_role.arn
  package_type  = "Image"
  image_uri     = var.lambda_notifications_image_uri

  timeout       = 10
  memory_size   = 512
  architectures = ["x86_64"]
  environment {
    variables = {
      NOTIFICATIONS_PROVIDER = var.notifications_provider      # "ses"
      FROM_EMAIL             = var.notifications_from_email    # e.g., noreply@yourdomain.com
      SENDGRID_API_KEY       = var.sendgrid_api_key
      SES_FROM_EMAIL         = var.notifications_from_email
    }
  }

  depends_on = [
    aws_iam_role_policy_attachment.notif_logs_attach,
    aws_iam_role_policy_attachment.notif_ses_attach
  ]
}

resource "aws_apigatewayv2_api" "notif_http" {
  name          = "${var.prefix}-notifications-api"
  protocol_type = "HTTP"
}

resource "aws_apigatewayv2_integration" "notif_integration" {
  api_id                 = aws_apigatewayv2_api.notif_http.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.notifications.invoke_arn
  payload_format_version = "2.0"
  timeout_milliseconds   = 10000
}

resource "aws_apigatewayv2_route" "notif_proxy" {
  api_id    = aws_apigatewayv2_api.notif_http.id
  route_key = "ANY /{proxy+}"
  target    = "integrations/${aws_apigatewayv2_integration.notif_integration.id}"
}

resource "aws_apigatewayv2_route" "notif_root" {
  api_id    = aws_apigatewayv2_api.notif_http.id
  route_key = "GET /"
  target    = "integrations/${aws_apigatewayv2_integration.notif_integration.id}"
}

resource "aws_apigatewayv2_stage" "notif_default" {
  api_id      = aws_apigatewayv2_api.notif_http.id
  name        = "$default"
  auto_deploy = true
}

resource "aws_lambda_permission" "notif_allow_apigw" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.notifications.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.notif_http.execution_arn}/*/*"
}

output "notifications_base_url" {
  value = aws_apigatewayv2_api.notif_http.api_endpoint
  description = "Base URL (append /notifications)"
}

output "dkim_cname_names" {
  value       = [for t in aws_ses_domain_dkim.dkim.dkim_tokens : "${t}._domainkey"]
  description = "CNAME record names to add in GoDaddy (they auto-append your domain)."
}

output "dkim_cname_values" {
  value       = [for t in aws_ses_domain_dkim.dkim.dkim_tokens : "${t}.dkim.amazonses.com"]
  description = "CNAME record targets for DKIM."
}

output "spf_record" {
  value       = "v=spf1 include:amazonses.com ~all"
  description = "TXT @ record value for SPF"
}

output "dmarc_record" {
  value       = "v=DMARC1; p=quarantine; pct=100; rua=mailto:dmarc@${var.domain_name}"
  description = "TXT _dmarc record value for DMARC"
}

resource "aws_ses_domain_identity" "ses_domain" {
  domain = var.domain_name
}

resource "aws_ses_domain_dkim" "dkim" {
  domain = aws_ses_domain_identity.ses_domain.domain
}

resource "aws_iam_policy" "ses_send" {
  name   = "${var.prefix}-ses-send"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect: "Allow",
      Action: [
        "ses:SendEmail",
        "ses:SendRawEmail"
      ],
      Resource: "*"
    }]
  })
}
resource "aws_iam_role_policy_attachment" "attach_ses_send" {
  role       = aws_iam_role.notif_role.name
  policy_arn = aws_iam_policy.ses_send.arn
}
