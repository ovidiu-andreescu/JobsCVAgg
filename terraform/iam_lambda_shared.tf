data "aws_caller_identity" "current" {}

data "aws_iam_policy_document" "assume_lambda" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

data "aws_iam_policy_document" "lambda_misc_doc" {
  statement {
    sid     = "S3AllList"
    actions = ["s3:ListAllMyBuckets"]
    resources = ["*"]
  }
}

resource "aws_iam_policy" "lambda_misc" {
  name   = var.prefix != "" ? "${var.prefix}-lambda-misc" : "lambda-misc"
  policy = data.aws_iam_policy_document.lambda_misc_doc.json
}

data "aws_iam_policy_document" "lambda_config_ro" {
  statement {
    actions   = ["ssm:GetParameter","ssm:GetParameters","ssm:GetParameterHistory"]
    resources = ["arn:aws:ssm:${var.region}:${data.aws_caller_identity.current.account_id}:parameter/${var.prefix}/*"]
  }
  statement {
    actions   = ["secretsmanager:GetSecretValue","secretsmanager:DescribeSecret"]
    resources = ["arn:aws:secretsmanager:${var.region}:${data.aws_caller_identity.current.account_id}:secret:${var.prefix}/*"]
  }
}

resource "aws_iam_policy" "lambda_config_ro" {
  name   = var.prefix != "" ? "${var.prefix}-lambda-config-ro" : "lambda-config-ro"
  policy = data.aws_iam_policy_document.lambda_config_ro.json
}
