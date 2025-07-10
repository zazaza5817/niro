from fastapi import FastAPI, status, Depends # type: ignore
from fastapi.middleware.cors import CORSMiddleware # type: ignore
from prometheus_fastapi_instrumentator import Instrumentator # type: ignore
import logging
import os
from routers import users, payments, internal_referrals, internal_pricing, subscription
from services.internal_auth import verify_internal_api_key


logger = logging.getLogger("my_app")
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')

os.makedirs('/app/logs', exist_ok=True)
file_handler = logging.FileHandler('/app/logs/backend.log', mode='a')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
print("Logger started")

logger.info("App started")

app = FastAPI()

# Prometheus метрики
instrumentator = Instrumentator(excluded_handlers=["/metrics"])
instrumentator.instrument(app).expose(app)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://nirovpn.com"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Роутеры ---
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(payments.router, prefix="/api/payments", tags=["Payments"])
app.include_router(internal_referrals.router, prefix="/api/referrals", tags=["Referrals_admin"])
app.include_router(internal_pricing.router, prefix="/api/pricing", tags=["Pricing"])
app.include_router(subscription.router, prefix="/api", tags=["Subscription"])


# --- Endpoints ---
@app.get("/api/health", status_code=status.HTTP_200_OK)
async def health_check():
    return {"status": "ok"}

@app.get("/api/openapi-schema", dependencies=[Depends(verify_internal_api_key)])
async def get_openapi_schema():
    """Возвращает полную OpenAPI схему"""
    return app.openapi()