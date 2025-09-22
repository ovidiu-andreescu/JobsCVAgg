resource "aws_iam_policy" "user_api_permissions" {
  name   = var.prefix != "" ? "${var.prefix}-user-api-permissions" : "user-api-permissions"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect   = "Allow",
        Action   = ["dynamodb:PutItem", "dynamodb:GetItem", "dynamodb:UpdateItem", "dynamodb:Query"],
        Resource = [
          aws_dynamodb_table.users.arn,
          "${aws_dynamodb_table.users.arn}/index/*"
        ]
      },
      {
        Effect   = "Allow",
        Action   = ["secretsmanager:GetSecretValue","secretsmanager:DescribeSecret"],
        Resource = "${aws_secretsmanager_secret.jwt_secret.arn}*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "user_api_permissions_attach" {
  role       = aws_iam_role.user_api.name
  policy_arn = aws_iam_policy.user_api_permissions.arn
}

