locals {
  # This boolean makes our conditional logic much clearer and less error-prone.
  is_image_package = var.lambda_image_uri != ""
  lambda_name      = var.prefix != "" ? "${var.prefix}-job-aggregator" : "job-aggregator"
}

resource "aws_lambda_function" "this" {
  function_name = local.lambda_name
  role          = aws_iam_role.lambda.arn
  timeout       = 30
  memory_size   = 512
  architectures = ["x86_64"]

  package_type = local.is_image_package ? "Image" : "Zip"

  image_uri = local.is_image_package ? var.lambda_image_uri : null

  s3_bucket = !local.is_image_package ? var.lambda_zip_s3_bucket : null
  s3_key    = !local.is_image_package ? var.lambda_zip_s3_key : null
  handler   = !local.is_image_package ? "job_aggregator.handler.handler" : null
  runtime   = !local.is_image_package ? "python3.12" : null

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

