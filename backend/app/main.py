import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth, metrics, notifications, products, tracking
from app.tasks.scheduler import start_scheduler, stop_scheduler

# Configure logging for the entire application
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Wardrop application")
    start_scheduler()
    yield
    stop_scheduler()
    logger.info("Wardrop application shutdown complete")


app = FastAPI(title="Wardrop", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(products.router, prefix="/api/products", tags=["products"])
app.include_router(tracking.router, prefix="/api/tracking", tags=["tracking"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["notifications"])
app.include_router(metrics.router, prefix="/api/metrics", tags=["metrics"])


@app.get("/api/health")
def health():
    return {"status": "ok"}
