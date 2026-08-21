from fastapi import FastAPI
from platform.admin.routes.tools import router as tools_router
from platform.admin.routes.hitl import router as hitl_router

app = FastAPI(title="Admin Platform API", version="1.0.0")

app.include_router(tools_router)
app.include_router(hitl_router)

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "admin_platform"}