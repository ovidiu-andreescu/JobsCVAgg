#!/usr/bin/env bash
set -euo pipefail

ENDPT="http://localhost:4566"
AWS="aws --endpoint-url=$ENDPT"
REGION="eu-central-1"

BUCKET="dev-cv-upload-local"
USERS_TABLE="dev-users-local"
LAMBDA_NAME="dev-cv-keywords-local"
LAMBDA_ROLE_ARN="arn:aws:iam::000000000000:role/lambda-exec-role"  # dummy for LocalStack
ZIP_PATH="./build/cv_keywords.zip"

echo "==> Resetting resources (if exist)…"
$AWS s3 rb "s3://${BUCKET}" --force 2>/dev/null || true
$AWS dynamodb delete-table --table-name "$USERS_TABLE" 2>/dev/null || true
$AWS lambda delete-function --function-name "$LAMBDA_NAME" 2>/dev/null || true

echo "==> Creating S3 bucket: ${BUCKET}"
$AWS s3 mb "s3://${BUCKET}"