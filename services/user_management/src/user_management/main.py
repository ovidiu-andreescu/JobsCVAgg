from .api.auth import router as auth_router
from .api.cv import router as cv_router
from .api.match import router as match_router
from fastapi import FastAPI
from mangum import Mangum

app = FastAPI(
    title="User Management",
    openapi_url="/openapi.json",
    docs_url="/docs",
)

@app.get("/")
def health():
    return {"status": "ok"}

# ------------------ ENDPOINTS ------------------
app.include_router(auth_router)

app.include_router(cv_router)

app.include_router(match_router)

# ---------- lambda handler ----------
handler = Mangum(app)