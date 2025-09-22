from fastapi import FastAPI
from .api.auth import router as auth_router
from .api.cv import router as cv_router

app = FastAPI(title="User Management")

@app.get("/")
def health():
    return {"status": "ok"}

# rutele de auth
app.include_router(auth_router)
app.include_router(cv_router)
