from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import os
import sys

from Backend_TC_Gen.utils.config import settings 
from Backend_TC_Gen.api import generate_func_edge_tests, generate_end_to_end_tests, files, jira

# -----------------------
# Setup logging with immediate flush
# -----------------------
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)
log_file_path = os.path.join(log_dir, "log.txt")

# Custom FileHandler that flushes immediately
class FlushFileHandler(logging.FileHandler):
    def emit(self, record):
        super().emit(record)
        self.flush()

# Formatter
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

# File handler
file_handler = FlushFileHandler(log_file_path, mode="a", encoding="utf-8")
file_handler.setLevel(logging.DEBUG)  # Capture tout : DEBUG, INFO, WARNING, ERROR
file_handler.setFormatter(formatter)

# Console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(formatter)

# Root logger
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# App-specific logger
app_logger = logging.getLogger(__name__)
app_logger.setLevel(logging.DEBUG)
app_logger.addHandler(file_handler)
app_logger.addHandler(console_handler)
app_logger.propagate = False

# -----------------------
# FastAPI lifespan
# -----------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.create_directories()
    app_logger.info("🧠 TC Generation server launched on port 8003")
    yield
    app_logger.info("Shutting down TC Generation server")

# -----------------------
# Create FastAPI app
# -----------------------
app = FastAPI(
    title="Test Case Generation API",
    description="API for generating test cases from user stories",
    version="2.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------
# Global exception handler
# -----------------------
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    app_logger.error(f"Global exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

# -----------------------
# Endpoints
# -----------------------
@app.get("/health")
async def health_check():
    app_logger.info("Health check requested")
    return {
        "status": "healthy",
        "version": "2.0.0",
        "service": "Test Case Generation API"
    }

@app.get("/")
async def root():
    app_logger.info("Root endpoint accessed")
    return {
        "message": "Test Case Generation API is running",
        "version": "2.0.0",
        "docs": "/docs",
        "health": "/health"
    }

# -----------------------
# Include routers
# -----------------------
app.include_router(generate_func_edge_tests.router, prefix="/edge_functional_tests", tags=["edge_functional_tests"])
app.include_router(generate_end_to_end_tests.router, prefix="/e2e_tests", tags=["e2e_tests"])
app.include_router(files.router, prefix="/files", tags=["files"])
app.include_router(jira.router, tags=["jira"])

# -----------------------
# Main
# -----------------------
if __name__ == "__main__":
    import uvicorn
    app_logger.info("Starting TC Generation FastAPI server...")
    uvicorn.run(
        app, 
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="debug"
    )
