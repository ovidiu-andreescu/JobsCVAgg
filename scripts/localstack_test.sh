#!/usr/bin/env bash
set -Eeuo pipefail

# ───────────────────────────────
# A robust script to build, deploy, and test any serverless function
# locally using LocalStack and Docker.
#
# USAGE (run from project root):
#   ./scripts/localstack_test.sh <service_name>
#
# ───────────────────────────────

# 1. Configuration & Paths
# ───────────────────────────────
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SERVICE_NAME="${1:-}"

if [ -z "$SERVICE_NAME" ]; then
  echo "ERROR: Please provide a service name to deploy." >&2
  echo "Usage: $0 <service_name>" >&2
  exit 1
fi

SERVICE_DIR="$REPO_ROOT/services/$SERVICE_NAME"
[ ! -d "$SERVICE_DIR" ] && { echo "ERROR: Service directory not found: $SERVICE_DIR" >&2; exit 1; }

SRC_DIR="$SERVICE_DIR/src"
HANDLER_MODULE=$(basename "$(find "$SRC_DIR" -mindepth 1 -maxdepth 1 -type d | head -n 1)")
HANDLER="${HANDLER_MODULE}.handler.handler"

BUILD_DIR="$REPO_ROOT/.build/$SERVICE_NAME"
DIST_DIR="$REPO_ROOT/.dist"
ZIP_FILE="$DIST_DIR/$SERVICE_NAME.zip"
ROLE_ARN="arn:aws:iam::000000000000:role/lambda-exec"
COMPOSE_FILE="$REPO_ROOT/docker-compose.localstack.yml"

set -a; [ -f "$REPO_ROOT/.env.test" ] && . "$REPO_ROOT/.env.test"; set +a

ENDPT="${LOCALSTACK_URL:-http://localhost:4566}"
AWS_REGION="${AWS_DEFAULT_REGION:-eu-west-1}"
export AWS_ACCESS_KEY_ID="${AWS_ACCESS_KEY_ID:-test}"
export AWS_SECRET_ACCESS_KEY="${AWS_SECRET_ACCESS_KEY:-test}"
export AWS_DEFAULT_REGION="$AWS_REGION"
AWS="aws --endpoint-url=$ENDPT --region $AWS_REGION"

# ───────────────────────────────
# ───────────────────────────────
# 2. Helper Functions
# ───────────────────────────────
need() { command -v "$1" >/dev/null || { echo "ERROR: Command '$1' not found." >&2; exit 1; }; }
zip_dir_py() {
  local src="$1" out="$2"
  python3 - "$src" "$out" <<'PY'
import os, sys, zipfile; src, out = sys.argv[1], sys.argv[2]
os.makedirs(os.path.dirname(out), exist_ok=True)
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
    for root, _, files in os.walk(src):
        for f in files: z.write(os.path.join(root, f), os.path.relpath(os.path.join(root, f), src))
print(f"  • Created archive: {out}")
PY
}
name_q() { local n="$1"; [ -n "${SECRETS_PREFIX:-}" ] && echo "${SECRETS_PREFIX}/$n" || echo "$n"; }
ensure_secret() { $AWS secretsmanager describe-secret --secret-id "$1" &>/dev/null && $AWS secretsmanager put-secret-value --secret-id "$1" --secret-string "$2" &>/dev/null || $AWS secretsmanager create-secret --name "$1" --secret-string "$2" &>/dev/null; }

# ───────────────────────────────
# 3. Main Execution
# ───────────────────────────────
need docker; need aws; need python3

echo "▶ Starting LocalStack..."
docker compose -f "$COMPOSE_FILE" up -d localstack >/dev/null
for i in {1..30}; do
  if $AWS lambda list-functions &>/dev/null && $AWS secretsmanager list-secrets &>/dev/null; then
    echo "  • LocalStack is ready at $ENDPT."; break
  fi; sleep 1; [ $i -eq 30 ] && { echo "ERROR: LocalStack did not become ready." >&2; exit 1; }
done

echo "▶ Seeding secrets..."
[ -n "${ADZUNA_APP_ID:-}" ]  && ensure_secret "$(name_q adzuna_app_id)"  "$ADZUNA_APP_ID"
[ -n "${ADZUNA_APP_KEY:-}" ] && ensure_secret "$(name_q adzuna_app_key)" "$ADZUNA_APP_KEY"
echo "  • Secrets seeded."

echo "▶ Building Lambda package for '$SERVICE_NAME'..."
rm -rf "$BUILD_DIR"; mkdir -p "$BUILD_DIR" "$DIST_DIR"

REQUIREMENTS_FILES=()
SERVICE_REQ_FILE="$SERVICE_DIR/requirements.txt"
[ -f "$SERVICE_REQ_FILE" ] && REQUIREMENTS_FILES+=("$SERVICE_REQ_FILE")
while IFS= read -r -d '' lib_req; do REQUIREMENTS_FILES+=("$lib_req"); done < <(find "$REPO_ROOT/libs" -name "requirements*.txt" -print0)

echo "  • Installing dependencies via Docker..."
if [ ${#REQUIREMENTS_FILES[@]} -gt 0 ]; then
  PIP_ARGS=""; for req in "${REQUIREMENTS_FILES[@]}"; do PIP_ARGS+="-r ${req#"$REPO_ROOT/"} "; done
  # --- FIX: Run the container as the current host user to avoid permission issues ---
  docker run --rm --user "$(id -u):$(id -g)" -v "$REPO_ROOT:/app" -w /app python:3.12-slim pip install --no-cache-dir $PIP_ARGS -t ".build/$SERVICE_NAME"
fi

echo "  • Copying source code..."
cp -R "$SRC_DIR/." "$BUILD_DIR"
for lib_dir in "$REPO_ROOT"/libs/*; do
  [ -d "$lib_dir/src" ] && cp -R "$lib_dir/src/." "$BUILD_DIR";
done
zip_dir_py "$BUILD_DIR" "$ZIP_FILE"

echo "▶ Deploying Lambda '$SERVICE_NAME'..."
VARS_LIST="SECRETS_ENDPOINT_URL=$ENDPT,PYTHONPATH=/var/task"
[ -n "${SECRETS_PREFIX:-}" ] && VARS_LIST="$VARS_LIST,SECRETS_PREFIX=$SECRETS_PREFIX"
ENV_VARS="Variables={$VARS_LIST}"

if $AWS lambda get-function --function-name "$SERVICE_NAME" &>/dev/null; then
  echo "  • Function exists, updating..."
  $AWS lambda update-function-code --function-name "$SERVICE_NAME" --zip-file "fileb://$ZIP_FILE" >/dev/null
  $AWS lambda update-function-configuration --function-name "$SERVICE_NAME" --handler "$HANDLER" --timeout 30 --environment "$ENV_VARS" >/dev/null
else
  echo "  • Function not found, creating..."
  $AWS lambda create-function --function-name "$SERVICE_NAME" \
    --runtime python3.12 --handler "$HANDLER" --role "$ROLE_ARN" --timeout 30 \
    --zip-file "fileb://$ZIP_FILE" --environment "$ENV_VARS" >/dev/null
fi
echo "  • Deployment complete."

echo "▶ Invoking '$SERVICE_NAME' for a smoke test..."
PAYLOAD='{"queryStringParameters": {"q": "python developer"}}'
TMP_OUT="$(mktemp)"
$AWS lambda invoke --function-name "$SERVICE_NAME" --payload "$PAYLOAD" "$TMP_OUT" --cli-binary-format raw-in-base64-out >/dev/null

echo "  • Response from Lambda:"
python3 - "$TMP_OUT" <<'PY'
import json, sys, os
try:
    with open(sys.argv[1]) as f: response = json.load(f)
    body_data = json.loads(response.get('body', '{}'))
    print(json.dumps(body_data[:2] if isinstance(body_data, list) else body_data, indent=2))
except Exception as e:
    print(f"  • Could not parse JSON body: {e}. Raw response:")
    with open(sys.argv[1]) as f: print(f.read())
finally:
    os.remove(sys.argv[1])
PY

echo "✅ Test harness finished successfully for '$SERVICE_NAME'."

