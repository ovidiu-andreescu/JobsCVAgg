#!/usr/bin/env bash
set -Eeuo pipefail

SERVICE_NAME="${1:-}"
AWS_REGION="${2:-}"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

if [ -z "$SERVICE_NAME" ] || [ -z "$AWS_REGION" ]; then
  echo "ERROR: Missing required arguments." >&2
  echo "Usage: $0 <service-name> <aws-region>" >&2
  exit 1
fi

SERVICE_DIR="$REPO_ROOT/services/$SERVICE_NAME"
[ ! -d "$SERVICE_DIR" ] && { echo "ERROR: Service directory not found: $SERVICE_DIR" >&2; exit 1; }

echo "▶ Fetching AWS Account ID..."
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query "Account" --output text)
if [ -z "$AWS_ACCOUNT_ID" ]; then
  echo "ERROR: Failed to get AWS Account ID. Is the AWS CLI configured?" >&2
  exit 1
fi

ECR_REPOSITORY_NAME="$SERVICE_NAME"
ECR_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY_NAME}"
IMAGE_TAG=$(git rev-parse --short HEAD)

echo "Service to build: $SERVICE_NAME"
echo "ECR Repository URI: $ECR_URI"
echo "Image Tag: $IMAGE_TAG"

# 3. --- Ensure ECR Repository Exists ---
echo "Checking for ECR repository '$ECR_REPOSITORY_NAME'..."
if ! aws ecr describe-repositories --repository-names "$ECR_REPOSITORY_NAME" --region "$AWS_REGION" &>/dev/null; then
  echo "Repository not found. Creating..."
  aws ecr create-repository \
    --repository-name "$ECR_REPOSITORY_NAME" \
    --image-scanning-configuration scanOnPush=true \
    --region "$AWS_REGION" >/dev/null
  echo "Repository created successfully."
else
  echo "Repository already exists."
fi

echo "Logging in to Amazon ECR..."
aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

echo "Building Docker image for '$SERVICE_NAME'..."
docker build \
  --build-arg SERVICE_NAME="$SERVICE_NAME" \
  -t "$ECR_URI:$IMAGE_TAG" \
  -t "$ECR_URI:latest" \
  -f "$REPO_ROOT/Dockerfile" \
  "$REPO_ROOT"

echo "Pushing image to ECR..."
docker push "$ECR_URI:$IMAGE_TAG"
docker push "$ECR_URI:latest"

echo
echo "Image pushed successfully!"
echo "--------------------------------------------------"
echo "Terraform 'lambda_image_uri' value:"
echo "${ECR_URI}:${IMAGE_TAG}"
echo "--------------------------------------------------"

