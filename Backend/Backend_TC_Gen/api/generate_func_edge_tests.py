# ## Functional / Non-functional Test Case Generation

import os
import json
import time
import random
import logging
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks
from Backend_TC_Gen.utils.config import settings  # Not used yet, but imported for future use
from Backend_TC_Gen.utils.functional_edge_generation_utils import FuncEdgeGeneration

func_edge_generation = FuncEdgeGeneration()

# ------------------ Logging Setup ------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ------------------ Constants ------------------
JOBS_FILE = "data/tc_jobs.json"

# ------------------ FastAPI Router ------------------
router = APIRouter()

# ------------------ Helper Functions ------------------
def load_jobs() -> dict:
    """Load all jobs from the JSON file."""
    if os.path.exists(JOBS_FILE):
        with open(JOBS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_job(job_id: str, data: dict):
    """Save a job status to the JSON file."""
    jobs = load_jobs()
    jobs[job_id] = data
    os.makedirs("data", exist_ok=True)
    with open(JOBS_FILE, 'w') as f:
        json.dump(jobs, f, indent=2)


# Updated job execution function for your FastAPI
async def run_generation_job(job_id: str, started_at: str, user_id: str):
    """
    Async generation job that processes user stories and generates test cases.
    """
    try:
        logger.info(f"Starting test case generation for {job_id}")
        
        # Call the actual async generation function
        result = await func_edge_generation.generate_functional_test_cases(user_id=user_id)
        
        # Save successful job result
        save_job(job_id, {
            "status": "completed",
            "started_at": started_at,
            "finished_at": datetime.now().isoformat(),
            "result": result
        })
        logger.info(f"Test case generation completed for {job_id}")
        
    except Exception as e:
        logger.error(f"Error in job {job_id}: {str(e)}")
        save_job(job_id, {
            "status": "failed",
            "started_at": started_at,
            "finished_at": datetime.now().isoformat(),
            "result": {"error": str(e)}
        })



# ------------------ API Endpoints ------------------
@router.post("/edge_func_TC/generate/{user_id}")
async def generate_functional_test_cases(user_id: str, background_tasks: BackgroundTasks):
    """
    Start functional test case generation in the background.
    """
    job_id = f"job_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
    started_at = datetime.now().isoformat()

    # Save initial job status
    save_job(job_id, {
        "status": "running",
        "started_at": started_at,
        "finished_at": None,
        "result": None
    })

    # Run job in the background
    background_tasks.add_task(run_generation_job, job_id, started_at, user_id)

    return {
        "message": "Test case generation started in background",
        "job_id": job_id,
        "started_at": started_at,
        "status": "accepted"
    }

@router.get("/edge_func_TC/latest_completed_job")
async def get_latest_completed_job():
    """
    Retrieve the most recently completed or failed job.
    """
    jobs = load_jobs()
    completed_jobs = [
        job for job in jobs.values()
        if job.get("status") in ["completed", "failed"]
    ]

    if completed_jobs:
        latest = max(completed_jobs, key=lambda x: x["started_at"])
        return latest

    return {"status": "idle"}
