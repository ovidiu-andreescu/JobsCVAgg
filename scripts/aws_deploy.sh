#!/usr/bin/env bash
set -Eeuo pipefail

# --- A script to build a Docker image and push it to AWS ECR ---
#
# USAGE:
#   ./scripts/build_and_push_ecr.sh <service-name> <aws-region>
#
# EXAMPLE:
#   ./scripts/build_and_push_ecr.sh job-aggregator eu-central-1
#
# -----------------------------------------------------------------

# 1. Validate input
SERVICE_NAME="${1:-}"
AWS_REGION="${2:-}"

if [ -z "$SERVICE_NAME" ] || [ -z "$AWS_REGION" ]; then
  echo "ERROR: Missing required arguments." >&2
  echo "Usage: $0 <service-name> <aws-region>" >&2
  exit 1
fi

# 2. Get AWS Account ID and define ECR repository URI
echo "▶ Fetching AWS Account ID..."
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query "Account" --output text)
if [ -z "$AWS_ACCOUNT_ID" ]; then
  echo "ERROR: Failed to get AWS Account ID. Is the AWS CLI configured?" >&2
  exit 1
fi

ECR_REPOSITORY_NAME="$SERVICE_NAME"
ECR_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY_NAME}"
IMAGE_TAG=$(git rev-parse --short HEAD) # Use the short git commit hash as a unique tag

echo "  • ECR Repository URI: $ECR_URI"
echo "  • Image Tag: $IMAGE_TAG"

# 3. Create ECR repository if it doesn't exist
echo "▶ Checking for ECR repository '$ECR_REPOSITORY_NAME'..."
if ! aws ecr describe-repositories --repository-names "$ECR_REPOSITORY_NAME" --region "$AWS_REGION" &>/dev/null; then
  echo "  • Repository not found. Creating..."
  aws ecr create-repository \
    --repository-name "$ECR_REPOSITORY_NAME" \
    --image-scanning-configuration scanOnPush=true \
    --region "$AWS_REGION" >/dev/null
  echo "  • Repository created successfully."
else
  echo "  • Repository already exists."
fi

# 4. Log in Docker to the ECR registry
echo "▶ Logging in to Amazon ECR..."
aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

# 5. Build the Docker image
echo "▶ Building Docker image..."
docker build -t "$ECR_URI:$IMAGE_TAG" -t "$ECR_URI:latest" .

# 6. Push the Docker image to ECR
echo "▶ Pushing image to ECR..."
docker push "$ECR_URI:$IMAGE_TAG"
docker push "$ECR_URI:latest"

echo "Image pushed successfully!"
echo "--------------------------------------------------"
echo "Terraform 'lambda_image_uri' value:"
echo "${ECR_URI}:${IMAGE_TAG}"
echo "--------------------------------------------------"
