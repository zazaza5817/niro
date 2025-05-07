from fastapi import FastAPI, status # type: ignore
from fastapi.middleware.cors import CORSMiddleware # type: ignore
import logging
import os

logger = logging.getLogger("my_app")
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')

os.makedirs('/app/logs', exist_ok=True)
file_handler = logging.FileHandler('/app/logs/main2.log', mode='a')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
print("Logger started")
 
logger.info("App started")
from routers import users, payments
from config import settings


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://nirovpn.com"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router, prefix="/api")
app.include_router(payments.router, prefix="/api")


@app.get("/api/health", status_code=status.HTTP_200_OK)
async def health_check():
    return {"status": "ok"}
