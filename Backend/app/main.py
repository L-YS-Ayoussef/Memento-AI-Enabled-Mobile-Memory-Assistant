from fastapi import FastAPI
from app.api.routers.agents import router as agent_router
from app.api.routers.auth import router as auth_router
from app.models.models import Base
from app.db.business_db import engine
from app.settings import settings
import logging
# from langsmith import Client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

Base.metadata.create_all(bind=engine)

logger.info("=============================================================")
logger.info(settings.CHAT_MODEL)
logger.info("=============================================================")


# Client(
#     api_key=settings.LANGSMITH_API_KEY,
#     api_url=settings.LANGSMITH_ENDPOINT,
# )

app = FastAPI()
app.include_router(agent_router, tags=["Agents"])
app.include_router(auth_router, tags=["Authentication"])