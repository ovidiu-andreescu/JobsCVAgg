import requests

BASE_URL = "https://nikw8v4uu1.execute-api.eu-central-1.amazonaws.com"
access_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ5b3VAZXhhbXBsZS5jb20iLCJleHAiOjE3NTg1NDY1Njh9.iIJas12cZsfMv2BJQ3TJ1dPlkJMBXS594Is6uphGVoo"

r = requests.post(
    f"{BASE_URL}/cv/presign/",
    headers={"Authorization": f"Bearer {access_token}"},
    json={"filename": "cv.pdf", "content_type": "application/pdf"},
)
r.raise_for_status()
upload_url = r.json()["upload_url"]

with open("cv.pdf", "rb") as f:
    up = requests.put(
        upload_url,
        headers={
            "Content-Type": "application/pdf",
            "x-amz-meta-user-sub": None,
        },
        data=f,
    )
    up.raise_for_status()
print("Uploaded:", up.status_code)
