from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi import Form
from typing import Optional
import os
import uuid
import shutil
import logging
from pathlib import Path

import json
from datetime import datetime
from pydantic import BaseModel
import re

from Backend_TC_Gen.utils.config import settings
from src.utils.user_data import UserDataManager
from src.utils.file_utils import FileService
from src.utils.jira_utils import JiraService
from Backend_TC_Gen.models.state import get_processing_state, update_processing_state

# Setup logging
logger = logging.getLogger(__name__)

user_data_manager = UserDataManager()
# user_paths = user_data_manager.load_user_paths()

file_service = FileService()
jira_service = JiraService()
processing_state = get_processing_state()

router = APIRouter()

# Move existing files to history on startup
try:
    moved_files = file_service.move_folder_contents(settings.US_PATH_TO_GENERATE, settings.ARCHIVED_US_TO_GENERATE_FILES_DIRECTORY)
    logger.info(f"{moved_files} user story files moved to history folder on startup.")
except Exception as e:
    logger.warning(f"Failed to move files on startup: {str(e)}")

class FormatRequest(BaseModel):
    format: str
    user_id: str

@router.post("/selected-format/upload")
async def receive_format(data: FormatRequest):
    """
    Receive and save the selected test case format.
    """
    try:
        logger.info(f"Received test case format: {data.format}")

        # Valid formats
        valid_formats = [
            "Gherkin sans paramètres",
            "Gherkin avec paramètres", 
            "Format en steps language naturel"
        ]

        # Validation
        if data.format not in valid_formats:
            logger.warning(f"Invalid format received: {data.format}")
            raise HTTPException(
                status_code=400,
                detail=f"Invalid format. Must be one of: {valid_formats}"
            )

        # Save the format
        logger.info(f"Saving test case format: {data.format}")
        user_data_manager.save_test_case_config(tc_format=data.format, user_id=data.user_id)

        return {
            "message": f"Format '{data.format}' saved successfully",
            "format": data.format,
            "status": "success"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unexpected error while saving test case format")
        raise HTTPException(status_code=500, detail=f"Failed to save format: {str(e)}")



@router.post("/user-stories-to-generate/upload/")
async def upload_user_stories_file(
    file: Optional[UploadFile] = File(None),
    jira_project_key: Optional[str] = Form(None),
    user_id: str = Form(...),
    source_state_field_name: Optional[str] = Form(None),
    target_state_field_name: Optional[str] = Form(None),
    etiquette: Optional[str] = Form(None),
    assignee: Optional[str] = Form(None),
    sprint: Optional[str] = Form(None)
):
    """
    Upload user stories file (Excel, JSON, etc.) and/or configure Jira information.
    """
    user_paths = user_data_manager._load_data(user_id)
    if not file and not (jira_project_key and source_state_field_name and target_state_field_name):
        logger.warning("Upload request missing both file and Jira info")
        raise HTTPException(
            status_code=400,
            detail="Provide at least an Excel/JSON file or Jira information."
        )

    response_data = {"status": "success"}

    try:
        # ---- Handle file upload ----
        if file:
            logger.info(f"Received file upload request: {file.filename}")

            if not file.filename:
                logger.error("No filename provided in upload")
                raise HTTPException(status_code=400, detail="No filename provided")

            if not file.filename.lower().endswith(('.xlsx', '.xls', '.json')):
                logger.error(f"Invalid file format: {file.filename}")
                raise HTTPException(
                    status_code=400,
                    detail="Invalid file format. Only .xlsx, .xls, or .json allowed."
                )

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = str(uuid.uuid4())[:8]
            filename = f"{timestamp}_{unique_id}_{file.filename}"
            file_path = os.path.join(settings.US_PATH_TO_GENERATE, filename)

            try:
                os.makedirs(settings.US_PATH_TO_GENERATE, exist_ok=True)
                with open(file_path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)

                file_size = os.path.getsize(file_path)
                logger.info(f"User stories file saved: {filename} ({file_size} bytes)")

                response_data.update({
                    "file_saved": filename,
                    "file_size": file_size
                })

            except Exception as e:
                logger.exception(f"Failed to save uploaded file: {file.filename}")
                raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
            finally:
                file.file.close()

        # ---- Handle Jira configuration ----
        if jira_project_key:
            logger.info(f"Configuring Jira for project key: {jira_project_key}")

            if not re.match(r'^[A-Z][A-Z0-9_]+$', jira_project_key):
                logger.warning(f"Potentially invalid Jira project key: {jira_project_key}")
                response_data["jira_warning"] = "Jira project key format may be invalid."

            response_data.update({
                "jira_project_key": jira_project_key,
                "source_state_field_name": source_state_field_name,
                "target_state_field_name": target_state_field_name,
                "etiquette": etiquette,
                "assignee": assignee,
                "user_id": user_id,
                "sprint": sprint
            })

            # ✅ Create UserDataManager with user_id and project_key
            # user_data_manager = UserDataManager()

            # Update in-memory user_paths (used by Jira service)
            user_paths.update({
                "US_project_key": jira_project_key,
                "US_input_name_field": source_state_field_name,
                "US_output_name_field": target_state_field_name,
                "US_etiquette": etiquette,
                "US_assignee": assignee,
                "user_id": user_id,
                "US_sprint": sprint
            })

            # ✅ Save config to user-specific file: User_data_{user_id}_{project_key}.json
            user_data_manager.save_user_story_config(
                us_project_key=jira_project_key,
                us_output_name_field=target_state_field_name,
                us_input_name_field=source_state_field_name,
                us_etiquette=etiquette,
                us_assignee=assignee,
                us_user_id=user_id,
                us_sprint=sprint
            )

            # Optional: Save project key (if this method exists)
            # user_data_manager.save_project_key(project_key=jira_project_key, key_type="US")

            update_processing_state(jira_input=True)

            processing_state.ensemble_paths = {
                "jira_project_key": jira_project_key,
                "source_state_field_name": source_state_field_name,
                "target_state_field_name": target_state_field_name,
                "etiquette": etiquette,
                "assignee": assignee,
                "user_id": user_id,
                "sprint": sprint
            }
            processing_state.jira_input = True

            logger.info("Jira configuration saved successfully")

            # ✅ Import from Jira after configuration
            jira_service.Jira_import_Target_US(user_id, user_paths, settings.US_PATH_TO_GENERATE)
            logger.info("Jira import completed")

        response_data["message"] = "Upload processed successfully"
        return JSONResponse(status_code=200, content=response_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error processing user stories upload")
        raise HTTPException(status_code=500, detail=f"Failed to process upload: {str(e)}")
    finally:
        if file and hasattr(file, 'file'):
            try:
                file.file.close()
            except Exception:
                pass



@router.post("/user-stories-to-generate/import/{jira_project_key}/{user_id}")
async def import_and_save_user_stories(jira_project_key: str, user_id: str):
    """Import user stories from local files or Jira and save to Excel"""
    try:
        logger.info("Starting user stories import and save...")

        state = get_processing_state()

        # -------- Create the project/user folder structure --------
        base_path = Path(settings.US_PATH_TO_GENERATE) / jira_project_key / user_id
        base_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Ensured folder exists: {base_path}")

        # ------------------ Check for Jira credentials ------------------
        def check_jira_credentials():
            try:
                user_data = user_data_manager._load_data(user_id)
                has_jira = bool(
                    user_data.get('jira_url') and
                    user_data.get('jira_username') and
                    user_data.get('US_project_key') and
                    user_data.get('US_input_name_field')
                )
                logger.debug(f"Jira URL: {user_data.get('jira_url')}")
                logger.debug(f"Jira credentials available: {has_jira}")
                return has_jira, user_data
            except (FileNotFoundError, json.JSONDecodeError):
                logger.warning("Jira credentials file not found or invalid JSON.")
                return False, {}

        logger.warning("Checking Jira credentials...")
        jira_available, user_paths = check_jira_credentials()
        if jira_available and not state.jira_input:
            update_processing_state(jira_input=True)
            state = get_processing_state()

        logger.warning(f"Jira input status: {state.jira_input}")

        # ------------------ Determine data source ------------------
        if not state.jira_input:
            logger.warning("Processing user stories from local files.")
            df, _, _ = file_service.concatenate_json_files_to_text(base_path)
            logger.warning("Local US processing completed.")

            if df is None or df.empty:
                raise HTTPException(status_code=400, detail="No valid user stories found in local files")

            ids_list = df['US_ID'].tolist() if 'US_ID' in df.columns else []
            titles_list = df['Titre'].tolist() if 'Titre' in df.columns else []
            data_source = "local"
        else:
            logger.warning("Processing user stories from Jira.")
            _, ids_list, titles_list, df = jira_service.Jira_import_Target_US(
                user_id, user_paths, str(base_path)  # Pass string if Jira service expects str
            )
            logger.warning(f"Jira import successful. Retrieved {len(ids_list)} IDs.")

            if df is None or df.empty:
                raise HTTPException(status_code=400, detail="No user stories found in Jira")

            data_source = "Jira"

        # ------------------ Save DataFrame to Excel ------------------
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        us_excel_filename = f"user_stories_{timestamp}.xlsx"
        us_excel_path = base_path / us_excel_filename

        df.to_excel(us_excel_path, index=False, engine="openpyxl")
        logger.warning(f"User stories saved to: {us_excel_path}")

        update_processing_state(
            ids_list=ids_list,
            titles_list=titles_list,
            last_imported_excel_path=str(us_excel_path)
        )

        return {
            "message": f"User stories imported and saved successfully from {data_source}",
            "excel_path": str(us_excel_path),
            "total_user_stories": len(df),
            "data_source": data_source,
            "ids_count": len(ids_list),
            "titles_count": len(titles_list)
        }

    except Exception as e:
        logger.error(f"Critical error in user stories import: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/edge-functional/download/{user_id}")
async def download_test_cases(user_id: str):
    """
    Download generated test cases Excel file
    """
    try:
        user_paths = user_data_manager._load_data(user_id)
        jira_project_key = user_paths.get("us_project_key")
        if not jira_project_key:
            logger.error("Jira project key not found in user paths")
            raise HTTPException(status_code=400, detail="Jira project key is required to download test cases")
        file_path = os.path.join(settings.GENERATED_EDGE_FUNCTIONAL_TESTS, jira_project_key , f"Gen_TC_functional_non_functional_{user_id}.xlsx")
        logger.warning(f"----------------File path to download: {file_path}")

        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Test cases file not found")
        
        logger.info(f"Downloading test cases file: {file_path}")
        
        return FileResponse(
            path=file_path,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename="Gen_TC_functional_non_functional.xlsx",
            headers={"Cache-Control": "no-cache"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading test cases: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to download file: {str(e)}")

@router.get("/e2e/download")
async def download_e2e_test_cases():
    """
    Download generated E2E test cases Excel file
    """
    try:
        file_path = os.path.join(settings.GENERATED_END_TO_END_TESTS, "Gen_TC_E2E.xlsx")
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="E2E test cases file not found")
        
        logger.info(f"Downloading E2E test cases file: {file_path}")
        
        return FileResponse(
            path=file_path,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename="Gen_TC_E2E.xlsx",
            headers={"Cache-Control": "no-cache"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading E2E test cases: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to download E2E file: {str(e)}")