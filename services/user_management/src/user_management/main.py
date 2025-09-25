from .api.auth import router as auth_router
from .api.cv import router as cv_router
from .api.match import router as match_router
from .api.jobs import router as jobs_router
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

app = FastAPI(
    title="User Management",
    openapi_url="/openapi.json",
    docs_url="/docs",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://d1a51zxxl9gg7n.cloudfront.net",
        "https://nqa4hzzjff.execute-api.eu-central-1.amazonaws.com",
        "*"
    ],
    allow_credentials=False,                  # don’t set to True unless you need cookies
    allow_methods=["GET", "POST", "OPTIONS"], # or ["*"]
    allow_headers=["Content-Type", "Authorization", "*"],
    max_age=600,
)

@app.get("/")
def health():
    return {"status": "ok"}

# ------------------ ENDPOINTS ------------------
app.include_router(auth_router)

app.include_router(cv_router)

app.include_router(match_router)

app.include_router(jobs_router)

# ---------- lambda handler ----------
handler = Mangum(app)