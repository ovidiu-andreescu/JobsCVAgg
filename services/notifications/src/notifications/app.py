from fastapi import FastAPI
from .api.notify import router as notify_router

app = FastAPI(title="Notifications")
app.include_router(notify_router)

@app.get("/")
def health():
    return {"status": "ok"}
