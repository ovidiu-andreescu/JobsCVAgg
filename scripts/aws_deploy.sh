export AWS_REGION="eu-central-1"
export ECR_REPO_NAME="job-aggregator"
export SERVICE_DIR_NAME="job_aggregator"
export IMAGE_TAG=$(git rev-parse --short HEAD)

echo "--- Building service: ${SERVICE_DIR_NAME} ---"
echo "--- Image tag will be: ${IMAGE_TAG} ---"

export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query "Account" --output text)
export ECR_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO_NAME}"

echo "--- Checking ECR repository: ${ECR_REPO_NAME} ---"
aws ecr describe-repositories --repository-names "${ECR_REPO_NAME}" --region "${AWS_REGION}" > /dev/null 2>&1 || \
    aws ecr create-repository --repository-name "${ECR_REPO_NAME}" --region "${AWS_REGION}" > /dev/null

echo "--- Logging in to ECR ---"
aws ecr get-login-password --region "${AWS_REGION}" | docker login --username AWS --password-stdin "${ECR_URI}"

echo "--- Building Docker image ---"
docker build \
  --build-arg SERVICE_NAME="${SERVICE_DIR_NAME}" \
  -t "${ECR_URI}:${IMAGE_TAG}" \
  -t "${ECR_URI}:latest" \
  -f Dockerfile .

# Step 6: Push the image
echo "--- Pushing image to ECR ---"
docker push "${ECR_URI}:${IMAGE_TAG}"
docker push "${ECR_URI}:latest"

echo
echo "--- ✅ BUILD AND PUSH COMPLETE ---"
echo "--- Your Terraform 'lambda_image_uri' is: ---"
echo "${ECR_URI}:${IMAGE_TAG}"
echo "--------------------------------------------------"