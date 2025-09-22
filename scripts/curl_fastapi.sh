# Login -> get access & refresh
curl -X POST https://nikw8v4uu1.execute-api.eu-central-1.amazonaws.com/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"email":"you@example.com","password":"password"}'

curl -X POST https://nikw8v4uu1.execute-api.eu-central-1.amazonaws.com/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"you@example.com","password":"password"}'

# Use the access token to call protected routes
curl https://nikw8v4uu1.execute-api.eu-central-1.amazonaws.com/auth/me \
  -H "Authorization: Bearer $ACCESS_TOKEN"

curl https://nikw8v4uu1.execute-api.eu-central-1.amazonaws.com/cv \
  -H "Authorization: Bearer $ACCESS_TOKEN"

{"access_token":"
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ5b3VAZXhhbXBsZS5jb20iLCJleHAiOjE3NTg1NTc1Mjl9.S-vz0-5gZHRPoNz1S9g6tYRBNbpz4vcQ_wwqUztfSqE
"
,"token_type":"bearer"}