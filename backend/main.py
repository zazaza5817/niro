from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
import logging
from routers import users, payments
from config import settings


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Роутеры ---
app.include_router(users.router, prefix="/api")
app.include_router(payments.router, prefix="/api")


# --- Эндпоинт ---

@app.get("/api/health", status_code=status.HTTP_200_OK)
async def health_check():
    return {"status": "ok"}