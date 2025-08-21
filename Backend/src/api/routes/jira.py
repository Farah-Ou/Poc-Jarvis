"""
api/routes/jira.py - JIRA related routes
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
import logging

from src.models.jira import JiraCredentials
from src.models.responses import JiraCredentialsResponse
from src.utils.config import settings
from src.utils.jira_utils import JiraService
from src.utils.user_data import UserDataManager
# from src.utils.file_utils import FileService

router = APIRouter()
logger = logging.getLogger(__name__)

def get_jira_service() -> JiraService:
    """Dependency to get JIRA service instance with API token from config"""
    return JiraService(api_token=settings.JIRA_TOKEN)

def get_user_data_manager() -> UserDataManager:
    """Dependency to get user data manager instance"""
    return UserDataManager()

# @router.post("/upload-jira-credentials", response_model=JiraCredentialsResponse)
# async def upload_jira_credentials(
#     credentials: JiraCredentials,
#     jira_service: JiraService = Depends(get_jira_service),
#     user_manager: UserDataManager = Depends(get_user_data_manager)
# ):
#     """
#     Upload and validate JIRA credentials.
    
#     Args:
#         credentials: JIRA server URL and username
        
#     Returns:
#         JiraCredentialsResponse: Validation result
#     """
#     try:
#         logger.info(f"Validating JIRA credentials for {credentials.jira_username}")
        
#         # Test connection
#         if not jira_service.test_connection(credentials):
#             raise HTTPException(
#                 status_code=400,
#                 detail="Invalid JIRA credentials. Please check your server URL, username, and API token."
#             )
        
#         # Save credentials to user data
#         user_manager.save_jira_credentials(
#             credentials.jira_server_url,
#             credentials.jira_username
#         )
        
#         logger.info("JIRA credentials validated successfully")
        
#         return JiraCredentialsResponse(
#             status="success",
#             message="JIRA credentials validated successfully",
#             jira_url=credentials.jira_server_url,
#             username=credentials.jira_username
#         )
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"Error validating JIRA credentials: {str(e)}")
#         raise HTTPException(
#             status_code=500,
#             detail=f"Internal server error: {str(e)}"
#         )

@router.post("/upload-jira-credentials", response_model=JiraCredentialsResponse)
async def upload_jira_credentials(
    credentials: JiraCredentials,
    jira_service: JiraService = Depends(get_jira_service),
    user_manager: UserDataManager = Depends(get_user_data_manager)
):
    try:
        logger.info(f"Validating JIRA credentials for {credentials.jira_username}")

        # 1. Test connection
        if not jira_service.test_connection(credentials):
            raise HTTPException(
                status_code=400,
                detail="Failed to connect. Check URL, username, or API token."
            )

        # 2. Test project access
        if not jira_service.test_project_access(credentials):
            raise HTTPException(
                status_code=400,
                detail=f"Project '{credentials.jira_project_key}' not found or not accessible."
            )

        # 3. Save credentials (pass user_id)
        user_manager.save_jira_credentials(
            jira_url=credentials.jira_server_url,
            jira_username=credentials.jira_username,
            us_user_id=credentials.user_id
        )

        return JiraCredentialsResponse(
            status="success",
            message="Connected and validated successfully",
            jira_url=credentials.jira_server_url,
            username=credentials.jira_username,
            project_key=credentials.jira_project_key
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/connection/test")
async def test_jira_connection(
    jira_service: JiraService = Depends(get_jira_service),
    user_manager: UserDataManager = Depends(get_user_data_manager)
):
    """
    Test JIRA connection with saved credentials.
    
    Returns:
        Dict: Connection test result
    """
    try:
        user_paths = user_manager.load_user_paths()
        
        if not user_paths.get("jira_url") or not user_paths.get("jira_username"):
            raise HTTPException(
                status_code=400,
                detail="No JIRA credentials found. Please upload credentials first."
            )
        
        # Create credentials object for testing
        credentials = JiraCredentials(
            jira_server_url=user_paths["jira_url"],
            jira_username=user_paths["jira_username"]
        )
        
        is_connected = jira_service.test_connection(credentials)
        
        return {
            "status": "success" if is_connected else "failed",
            "message": "Connection successful" if is_connected else "Connection failed",
            "connected": is_connected
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing JIRA connection: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )