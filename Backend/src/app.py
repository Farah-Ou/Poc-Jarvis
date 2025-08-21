import sys
import asyncio
import logging
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import logging 

from src.api.routes import jira, files, graphs
from src.utils.config import settings

# -----------------------
# Logging configuration
# -----------------------
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)
log_file_path = os.path.join(log_dir, "log.txt")

# FileHandler with flush
class FlushFileHandler(logging.FileHandler):
    def emit(self, record):
        super().emit(record)
        self.flush()

formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

# Root logger
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)  # Capture tout : DEBUG, INFO, WARNING, ERROR

# File handler
file_handler = FlushFileHandler(log_file_path, mode="a", encoding="utf-8")
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

# Console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(formatter)

# Add handlers to root logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# App-specific logger
app_logger = logging.getLogger(__name__)
app_logger.setLevel(logging.DEBUG)
app_logger.addHandler(file_handler)
app_logger.addHandler(console_handler)
app_logger.propagate = False

# -----------------------
# Load environment
# -----------------------
load_dotenv()

# Windows compatibility
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# -----------------------
# FastAPI app
# -----------------------
app = FastAPI(
    title="Jarvis Test Case Generator API",
    description="API for generating test cases using GraphRAG and JIRA integration",
    version="2.0.2",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(jira.router, prefix="/api/jira", tags=["JIRA"])
app.include_router(files.router, prefix="/api/files", tags=["Files"])
app.include_router(graphs.router, prefix="/api/graphs", tags=["Graphs"])

# -----------------------
# Endpoints
# -----------------------
@app.get("/")
async def root():
    app_logger.info(f"GRAPHS_FOLDER_PATH: {settings.GRAPHS_FOLDER_PATH}")
    app_logger.warning("Ceci est un warning de test")
    app_logger.error("Ceci est un error de test")
    return {
        "message": "Jarvis Test Case Generator API is running!",
        "version": "2.0.2",
        "status": "healthy"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "jarvis-api",
        "version": "2.0.2"
    }

# -----------------------
# Main
# -----------------------
if __name__ == "__main__":
    app_logger.info("🧠 Jarvis API server launching on port 8000")
    import uvicorn
    logging.debug("\n 🧠 Jarvis API server launched on port 8000 \n")
    logging.debug("path GRAPHS_FOLDER_PATH ", settings.GRAPHS_FOLDER_PATH)
    
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="debug"
    )
