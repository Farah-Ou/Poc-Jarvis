from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional
import os
import uuid
import shutil
import logging
import re
from datetime import datetime
from pydantic import BaseModel

from Backend_TC_Gen.utils.config import settings
from src.utils.user_data import UserDataManager
from src.utils.jira_utils import JiraService


# Setup logging
logger = logging.getLogger(__name__)
# settings = get_settings()

user_manager = UserDataManager()
# Get paths
# paths = user_data_manager.load_user_paths()
user_paths = user_manager.load_user_paths()

jira_service = JiraService()

router = APIRouter()



class JiraConfigRequest(BaseModel):
    jira_project_key: str
    source_state_field_name: str
    target_state_field_name: str


class JiraUserStoryRequest(BaseModel):
    project_key: str
    jql_query: Optional[str] = None
    max_results: Optional[int] = 50


@router.post("/US-to-generate/upload")
async def upload_excel_with_jira_info(
    file: Optional[UploadFile] = File(None),
    jira_project_key: Optional[str] = Form(None),
    source_state_field_name: Optional[str] = Form(None),
    target_state_field_name: Optional[str] = Form(None)
):
    """
    Upload Excel file with Jira information or provide Jira configuration directly
    """
    try:       
        # Validate input - need either file or Jira info
        if not file and not (jira_project_key and source_state_field_name and target_state_field_name):
            raise HTTPException(
                status_code=400, 
                detail="Provide at least an Excel file or complete Jira information."
            )

        response_data = {"status": "success"}

        # Handle file upload if provided
        if file:
            if not file.filename:
                raise HTTPException(status_code=400, detail="No filename provided")
                
            # Validate file format
            allowed_extensions = ['.xlsx', '.xls', '.json']
            file_extension = os.path.splitext(file.filename)[1].lower()
            
            if file_extension not in allowed_extensions:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Invalid file format. Only {allowed_extensions} allowed."
                )

            # Generate unique filename and save
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = str(uuid.uuid4())[:8]
            filename = f"{timestamp}_{unique_id}_{file.filename}"
            file_path = os.path.join(settings.US_PATH_TO_GENERATE, filename)

            try:
                with open(file_path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)
                    
                file_size = os.path.getsize(file_path)
                response_data["file_saved"] = filename
                response_data["file_size"] = file_size
                logger.info(f"Excel file saved: {filename} ({file_size} bytes)")
                
            except Exception as e:
                logger.error(f"Failed to save file: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
            finally:
                if hasattr(file, 'file'):
                    file.file.close()

        # Handle Jira configuration if provided
        if jira_project_key:
            # Validate Jira project key format
            if not re.match(r'^[A-Z][A-Z0-9_]+$', jira_project_key):
                response_data["jira_warning"] = "Jira project key format may be invalid."
                logger.warning(f"Potentially invalid Jira project key format: {jira_project_key}")

            # Save Jira configuration to user_paths
            user_paths["US_project_key"] = jira_project_key
            user_paths["US_input_name_field"] = source_state_field_name
            user_paths["US_output_name_field"] = target_state_field_name

            user_manager.save_project_key(jira_project_key, key_type="US")
            user_manager.save_user_story_config(
                us_input_name_field=source_state_field_name,
                us_output_name_field=target_state_field_name
            )

            response_data.update({
                "jira_project_key": jira_project_key,
                "source_state_field_name": source_state_field_name,
                "target_state_field_name": target_state_field_name
            })

            logger.info("Jira configuration saved to user_paths")

        # Import user stories from Jira if configuration is complete
        if jira_project_key and source_state_field_name:
            try:
                _, _, _, df = jira_service.Jira_import_Target_US(user_paths, settings.US_PATH_TO_GENERATE)
                if df is not None and not df.empty:
                    response_data["jira_import_success"] = True
                    response_data["imported_user_stories_count"] = len(df)
                    logger.info(f"Successfully imported {len(df)} user stories from Jira")
                else:
                    response_data["jira_import_warning"] = "No user stories found in Jira"
                    logger.warning("Jira import returned empty DataFrame")
            except Exception as e:
                logger.error(f"Jira import failed: {str(e)}")
                response_data["jira_import_error"] = f"Failed to import from Jira: {str(e)}"

        response_data["message"] = "Upload and Jira configuration processed successfully."
        return JSONResponse(status_code=200, content=response_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in Jira Excel upload: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/configure-jira")
async def configure_jira(config: JiraConfigRequest):
    """
    Configure Jira connection settings
    """
    try:
        # Validate Jira project key format
        if not re.match(r'^[A-Z][A-Z0-9_]+$', config.jira_project_key):
            logger.warning(f"Potentially invalid Jira project key format: {config.jira_project_key}")

        # Save configuration
        user_paths["US_project_key"] = config.jira_project_key
        user_paths["US_input_name_field"] = config.source_state_field_name
        user_paths["US_output_name_field"] = config.target_state_field_name
        # save_user_paths()

        user_manager.save_project_key(config.jira_project_key, key_type="US")
        user_manager.save_user_story_config(
            us_input_name_field=config.source_state_field_name,
            us_output_name_field=config.target_state_field_name
        )

        logger.info(f"Jira configuration saved: {config.jira_project_key}")

        return {
            "message": "Jira configuration saved successfully",
            "project_key": config.jira_project_key,
            "source_field": config.source_state_field_name,
            "target_field": config.target_state_field_name
        }

    except Exception as e:
        logger.error(f"Error configuring Jira: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to configure Jira: {str(e)}")


@router.post("/import-user-stories")
async def import_user_stories_from_jira(request: JiraUserStoryRequest):
    """
    Import user stories from Jira using the configured settings
    """
    try:
        # Check if Jira is configured
        if not user_paths.get("US_project_key"):
            raise HTTPException(
                status_code=400, 
                detail="Jira not configured. Please configure Jira settings first."
            )

        # Update project key if provided
        if request.project_key:
            user_paths["US_project_key"] = request.project_key
            user_manager.save_project_key(request.project_key, key_type="US")

        # Import user stories
        imported_file_path, ids_list, titles_list, df = jira_service.Jira_import_Target_US(
            user_paths, settings.US_PATH_TO_GENERATE
        )

        if df is None or df.empty:
            raise HTTPException(
                status_code=404, 
                detail="No user stories found in Jira with current configuration"
            )

        logger.info(f"Successfully imported {len(df)} user stories from Jira")

        return {
            "message": "User stories imported successfully from Jira",
            "imported_file_path": imported_file_path,
            "user_stories_count": len(df),
            "user_story_ids": ids_list,
            "user_story_titles": titles_list,
            "project_key": user_paths.get("US_project_key")
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error importing user stories from Jira: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to import from Jira: {str(e)}")


@router.post("/create-jira-links")
async def create_jira_test_case_links(
    test_cases_data: dict,
    link_type: str = "Relates"
):
    """
    Create links between user stories and generated test cases in Jira
    """
    try:
        # Check if Jira is configured
        if not user_paths.get("US_project_key"):
            raise HTTPException(
                status_code=400, 
                detail="Jira not configured. Please configure Jira settings first."
            )

        # Validate link type
        valid_link_types = ["Relates", "Tests", "Blocks", "Clones", "Duplicates"]
        if link_type not in valid_link_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid link type. Must be one of: {valid_link_types}"
            )

        # Convert test cases data to DataFrame-like structure for the function
        import pandas as pd
        
        if isinstance(test_cases_data, dict):
            # Ensure we have the required columns
            required_columns = ['id_US', 'Title', 'Test Cases']
            df_data = {}
            
            for col in required_columns:
                if col not in test_cases_data:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Missing required field: {col}"
                    )
                df_data[col] = test_cases_data[col]
            
            df_test_cases = pd.DataFrame(df_data)
        else:
            raise HTTPException(
                status_code=400,
                detail="test_cases_data must be a dictionary with lists of values"
            )

        # Create Jira links
        result = jira_service.create_link_tickets(user_paths, df_test_cases, link_type=link_type)
        
        logger.info(f"Successfully created Jira links with type '{link_type}'")

        return {
            "message": f"Jira links created successfully with type '{link_type}'",
            "link_type": link_type,
            "processed_records": len(df_test_cases),
            "result": result
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating Jira links: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create Jira links: {str(e)}")


@router.get("/jira-config")
async def get_jira_configuration():
    """
    Get current Jira configuration
    """
    try:
        config = {
            "project_key": user_paths.get("US_project_key"),
            "source_field": user_paths.get("US_input_name_field"),
            "target_field": user_paths.get("US_output_name_field"),
            "is_configured": bool(
                user_paths.get("US_project_key") and 
                user_paths.get("US_input_name_field")
            )
        }

        return {
            "message": "Jira configuration retrieved successfully",
            "configuration": config
        }

    except Exception as e:
        logger.error(f"Error getting Jira configuration: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get Jira configuration: {str(e)}")


@router.delete("/clear-jira-config")
async def clear_jira_configuration():
    """
    Clear Jira configuration
    """
    try:
        # Remove Jira-related keys from user_paths
        jira_keys = ["US_project_key", "US_input_name_field", "US_output_name_field"]
        cleared_keys = []
        
        for key in jira_keys:
            if key in user_paths:
                del user_paths[key]
                cleared_keys.append(key)
        
        user_manager.save_field_config()  # Save changes to user paths
        
        logger.info(f"Cleared Jira configuration keys: {cleared_keys}")

        return {
            "message": "Jira configuration cleared successfully",
            "cleared_keys": cleared_keys
        }

    except Exception as e:
        logger.error(f"Error clearing Jira configuration: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to clear Jira configuration: {str(e)}")


@router.get("/test-jira-connection")
async def test_jira_connection():
    """
    Test the Jira connection with current configuration
    """
    try:
        # Check if Jira is configured
        if not user_paths.get("US_project_key"):
            raise HTTPException(
                status_code=400, 
                detail="Jira not configured. Please configure Jira settings first."
            )

        # Test connection by trying to import a small set of user stories
        try:
            _, _, _, df = jira_service.Jira_import_Target_US(user_paths, settings.US_PATH_TO_GENERATE)
            
            connection_status = {
                "status": "success",
                "project_key": user_paths.get("US_project_key"),
                "can_connect": True,
                "user_stories_found": len(df) if df is not None and not df.empty else 0
            }
            
        except Exception as jira_error:
            connection_status = {
                "status": "failed",
                "project_key": user_paths.get("US_project_key"),
                "can_connect": False,
                "error": str(jira_error)
            }

        return {
            "message": "Jira connection test completed",
            "connection_test": connection_status
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing Jira connection: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to test Jira connection: {str(e)}")