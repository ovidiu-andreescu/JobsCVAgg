#!/usr/bin/env bash
set -Eeuo pipefail

err(){ printf "ERROR: %s\n" "$*" >&2; }
info(){ printf "▶ %s\n" "$*"; }
note(){ printf " • %s\n" "$*"; }

SERVICE_NAME="${1:-}"
AWS_REGION="${2:-}"
AWS_PROFILE="${AWS_PROFILE:-}"

if [ -z "$SERVICE_NAME" ] || [ -z "$AWS_REGION" ]; then
  err "Usage: $0 <service-name> <aws-region>"
  exit 1
fi

for cmd in aws docker git; do
  if ! command -v "$cmd" &>/dev/null; then
    err "Missing required command: $cmd"
    exit 1
  fi
done

AWS_CLI_ARGS=("--region" "$AWS_REGION")
if [ -n "$AWS_PROFILE" ]; then
  AWS_CLI_ARGS+=("--profile" "$AWS_PROFILE")
fi

info "Fetching AWS Account ID..."
AWS_ACCOUNT_ID=$(aws sts get-caller-identity "${AWS_CLI_ARGS[@]}" --query "Account" --output text 2>/dev/null || true)
if [ -z "$AWS_ACCOUNT_ID" ]; then
  err "Failed to get AWS Account ID. Check AWS CLI config/credentials."
  exit 1
fi

ECR_REPOSITORY_NAME="$SERVICE_NAME"
ECR_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY_NAME}"

if git rev-parse --is-inside-work-tree &>/dev/null; then
  IMAGE_TAG="$(git rev-parse --short HEAD | tr -d '[:space:]')"
else
  IMAGE_TAG="$(date -u +"%Y%m%d%H%M%S")"
fi

if [ -z "${IMAGE_TAG:-}" ]; then
  err "Computed IMAGE_TAG is empty. Aborting."
  exit 1
fi

info "ECR URI: $ECR_URI"
note "Tag: $IMAGE_TAG"

info "Checking for ECR repository..."
if ! aws ecr describe-repositories "${AWS_CLI_ARGS[@]}" --repository-names "$ECR_REPOSITORY_NAME" &>/dev/null; then
  note "Creating repository..."
  aws ecr create-repository --repository-name "$ECR_REPOSITORY_NAME" --image-scanning-configuration scanOnPush=true "${AWS_CLI_ARGS[@]}" >/dev/null
  cat > /tmp/ecr-lifecycle.json <<'EOF'
{"rules":[{"rulePriority":1,"description":"Keep last 30 tagged","selection":{"tagStatus":"tagged","countType":"imageCountMoreThan","countNumber":30},"action":{"type":"expire"}}]}
EOF
  aws ecr put-lifecycle-policy --repository-name "$ECR_REPOSITORY_NAME" --lifecycle-policy-text "file:///tmp/ecr-lifecycle.json" "${AWS_CLI_ARGS[@]}" >/dev/null || true
  rm -f /tmp/ecr-lifecycle.json
else
  note "Repository exists."
fi

info "Logging in to ECR..."
aws ecr get-login-password "${AWS_CLI_ARGS[@]}" | docker login --username AWS --password-stdin "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

info "Building Docker image..."
echo "  docker build --pull -t \"${ECR_URI}:${IMAGE_TAG}\" -t \"${ECR_URI}:latest\" ."
docker build --pull -t "${ECR_URI}:${IMAGE_TAG}" -t "${ECR_URI}:latest" .

info "Pushing images..."
push_with_retries(){
  local tag=$1
  local attempts=0
  local max=3
  until docker push "$tag"; do
    attempts=$((attempts+1))
    if [ "$attempts" -ge "$max" ]; then
      err "Failed to push $tag"
      return 1
    fi
    note "Retrying push ($attempts/$max) in 3s..."
    sleep 3
  done
  return 0
}

push_with_retries "${ECR_URI}:${IMAGE_TAG}"
push_with_retries "${ECR_URI}:latest"

info "Done."
echo '--------------------------------------------------\n'
echo "Terraform 'lambda_image_uri': %s\n" "${ECR_URI}:${IMAGE_TAG}"
echo '--------------------------------------------------\n'
