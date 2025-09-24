#!/usr/bin/env bash
set -euo pipefail

API="${API:-https://nqa4hzzjff.execute-api.eu-central-1.amazonaws.com}"
EMAIL="${EMAIL:-you@example.com}"
PASSWORD="${PASSWORD:-password}"
FILE="${FILE:-cv.pdf}"

command -v jq >/dev/null || { echo "Error: jq is required"; exit 1; }
[[ -f "$FILE" ]] || { echo "Error: file not found: $FILE"; exit 1; }

if command -v file >/dev/null; then
  CONTENT_TYPE="$(file -b --mime-type "$FILE" || echo application/pdf)"
else
  CONTENT_TYPE="application/pdf"
fi

LOGIN_PAYLOAD=$(jq -n --arg e "$EMAIL" --arg p "$PASSWORD" '{email:$e, password:$p}')
LOGIN_RESP=$(curl -sS -X POST "$API/auth/login" \
  -H 'Content-Type: application/json' \
  -d "$LOGIN_PAYLOAD") || { echo "Login request failed"; exit 1; }

TOKEN=$(jq -r '.access_token // empty' <<<"$LOGIN_RESP")
if [[ -z "${TOKEN}" || "${TOKEN}" == "null" ]]; then
  echo "Error: could not extract access_token from /auth/login response:"
  echo "$LOGIN_RESP"
  exit 1
fi
echo "Got token."

PRESIGN_PAYLOAD=$(jq -n --arg fn "$(basename "$FILE")" --arg ct "$CONTENT_TYPE" \
  '{filename:$fn, content_type:$ct}')

PRESIGN=$(curl -sS -X POST "$API/me/cv/presign" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "$PRESIGN_PAYLOAD") || { echo "Presign request failed"; exit 1; }

URL=$(jq -r '.url // empty' <<<"$PRESIGN")
[[ -n "$URL" ]] || { echo "Error: presign response missing .url"; echo "$PRESIGN"; exit 1; }

ARGS=()
while IFS= read -r row; do
  k=$(echo "$row" | base64 -d | jq -r .key)
  v=$(echo "$row" | base64 -d | jq -r .value)
  ARGS+=(-F "$k=$v")
done < <(jq -r '.fields | to_entries[] | @base64' <<<"$PRESIGN")

ARGS+=(-F "file=@${FILE};type=${CONTENT_TYPE}")

echo "Uploading $(basename "$FILE") to S3..."
HTTP_CODE=$(curl -sS -o /dev/stderr -w "%{http_code}" -X POST "$URL" "${ARGS[@]}")
if [[ "$HTTP_CODE" -lt 200 || "$HTTP_CODE" -ge 300 ]]; then
  echo "Upload failed with HTTP $HTTP_CODE"
  exit 1
fi
echo "Upload complete (HTTP $HTTP_CODE)."