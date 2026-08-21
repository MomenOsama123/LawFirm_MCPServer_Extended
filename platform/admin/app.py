import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from admin.routes.tools import router as tools_router
from admin.routes.hitl import router as hitl_router

app = FastAPI(title="Admin Platform API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("LAW_FIRM_UI_ORIGIN", "http://localhost:3000")],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

app.include_router(tools_router)
app.include_router(hitl_router)

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "admin_platform"}