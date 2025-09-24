API="https://nqa4hzzjff.execute-api.eu-central-1.amazonaws.com"
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ5b3VAZXhhbXBsZS5jb20iLCJpYXQiOjE3NTg2NjYyOTgsImV4cCI6MTc1ODY2OTg5OCwidHlwZSI6ImFjY2VzcyJ9.KxlBwi3F_oTf9pF_47Wky0od_11V-LcJ3cYjQW_bgkc"
FILE="cv.pdf"

# 1) Get presign
PRESIGN=$(curl -sS -X POST "$API/me/cv/presign" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"filename":"cv.pdf","content_type":"application/pdf"}')

# 2) Upload — DO NOT hand-pick fields; send them all exactly as given
URL=$(jq -r .url <<<"$PRESIGN")
ARGS=()
while IFS= read -r row; do
  k=$(echo "$row" | base64 -d | jq -r .key)
  v=$(echo "$row" | base64 -d | jq -r .value)
  ARGS+=(-F "$k=$v")
done < <(jq -r '.fields | to_entries[] | @base64' <<<"$PRESIGN")
ARGS+=(-F "file=@${FILE}")
curl -i -X POST "$URL" "${ARGS[@]}"
