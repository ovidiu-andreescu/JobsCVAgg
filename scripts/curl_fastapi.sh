# Login -> get access & refresh
curl -X POST https://nqa4hzzjff.execute-api.eu-central-1.amazonaws.com/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"email":"you@example.com","password":"password"}'

curl -X POST https://nqa4hzzjff.execute-api.eu-central-1.amazonaws.com/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"you@example.com","password":"password"}'

# Use the access token to call protected routes
curl https://nqa4hzzjff.execute-api.eu-central-1.amazonaws.com/auth/me \
  -H "Authorization: Bearer $ACCESS_TOKEN"

curl https://nqa4hzzjff.execute-api.eu-central-1.amazonaws.com/cv \
  -H "Authorization: Bearer $ACCESS_TOKEN"

{"access_token":"
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ5b3VAZXhhbXBsZS5jb20iLCJpYXQiOjE3NTg2OTk4NzksImV4cCI6MTc1ODcwMzQ3OSwidHlwZSI6ImFjY2VzcyJ9.au9T9xFkIdMu7ohgNYxJcQ-6gqo_bEvYbZtrZMT66vU
"
curl -i -X POST "https://nqa4hzzjff.execute-api.eu-central-1.amazonaws.com/cv/presign" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"filename":"cv.pdf","content_type":"application/pdf"}'

  curl -sS -X POST \
  "https://nqa4hzzjff.execute-api.eu-central-1.amazonaws.com/me/cv/presign" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"filename":"cv.pdf","content_type":"application/pdf"}'

curl -X POST https://nqa4hzzjff.execute-api.eu-central-1.amazonaws.com/auth/_debug/mark-verified \
  -H 'Content-Type: application/json' \
  -d '{"email":"test@example.com"}'


