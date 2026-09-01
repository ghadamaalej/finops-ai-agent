from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.agent import router as agent_router
from api.health import router as health_router
from api.auth import router as auth_router
from api.dashboard import router as dashboard_router
from config.settings import settings
from app.database.init_db import init_database

# Apply additive schema upgrades before request handlers can query ORM columns.
init_database()

app = FastAPI(
    title="AI FinOps Agent",
    version="1.0.0",
    description="AI Agent for Azure FinOps Optimization",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        settings.FRONTEND_ORIGIN,
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS", "PUT", "PATCH", "DELETE"],
    allow_headers=["Accept", "Authorization", "Content-Type", "Origin", "X-Requested-With"],
)

app.include_router(health_router)
app.include_router(agent_router)
app.include_router(auth_router)
app.include_router(dashboard_router)


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "AI FinOps Agent is running"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
