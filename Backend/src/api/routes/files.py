"""
api/routes/files.py - File upload and management routes
"""
from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import List, Optional
import logging
from datetime import datetime
import uuid
import re
import os
from pathlib import Path
from pathlib import Path

from src.models.responses import JiraUploadResponse
from src.utils.config import settings
from src.utils.file_utils import FileService
from src.utils.jira_utils import JiraService
from src.utils.user_data import UserDataManager
from src.utils.ticket_history_manager_utils import TicketHistoryManager

router = APIRouter()
logger = logging.getLogger(__name__)

def get_file_service() -> FileService:
    """Dependency to get file service instance"""
    return FileService()

def get_jira_service() -> JiraService:
    """Dependency to get JIRA service instance"""
    return JiraService()

def get_user_data_manager() -> UserDataManager:
    """Dependency to get user data manager instance"""
    return UserDataManager()

def get_ticket_history_manager() -> TicketHistoryManager:
    """Dependency to get ticket history manager instance"""
    return TicketHistoryManager()



          

@router.post("/epics-features-us/upload", response_model=JiraUploadResponse)
async def upload_epics_features_us(
    file: Optional[UploadFile] = File(None),
    jira_project_key: str = Form(None),
    user_id: str = Form(...),  # Required so we can store with user ID
    file_service: FileService = Depends(get_file_service),
    jira_service: JiraService = Depends(get_jira_service),
    user_manager: UserDataManager = Depends(get_user_data_manager),
    ticket_history_manager: TicketHistoryManager = Depends(get_ticket_history_manager)
):
    """
    Upload user stories via file or JIRA import.
    
    Args:
        file: Optional Excel/JSON file
        jira_project_key: Optional JIRA project key
        user_id: The ID of the user uploading/importing
        
    Returns:
        JiraUploadResponse: Upload results
    """
    try:
        logger.info("Processing user stories upload")

        # Ensure base directory exists
        os.makedirs(settings.CURRENT_US_PATH, exist_ok=True)

        if not file and not jira_project_key:
            raise HTTPException(
                status_code=400,
                detail="Provide at least an Excel file or JIRA information."
            )

        # Build project-specific storage path
        project_dir_name = jira_project_key or "NO_KEY"
        project_repo_path = Path(settings.CURRENT_US_PATH) / f"{project_dir_name}"
        project_repo_path.mkdir(parents=True, exist_ok=True)

        response_data = {
            "status": "success",
            "project_repo_path": str(project_repo_path)  # cast to str for JSON
        }

        # --- Handle file upload ---
        if file:
            if not file.filename.endswith(('.xlsx', '.xls', '.json')):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid file format. Only .xlsx, .xls, or .json allowed."
                )

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = str(uuid.uuid4())[:8]
            filename = f"{timestamp}_{unique_id}_{file.filename}"

            try:
                saved_path = await file_service.save_file(
                    file, project_repo_path, filename
                )
                response_data["file_saved"] = filename
                response_data["file_size"] = saved_path.stat().st_size
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to save file: {str(e)}"
                )
            finally:
                file.file.close()

        # --- Handle JIRA import ---
        if jira_project_key:
            if not re.match(r'^[A-Z][A-Z0-9_]+$', jira_project_key):
                response_data["jira_warning"] = "JIRA project key format may be invalid."

            response_data["jira_project_key"] = jira_project_key

            # Save project key to user data
            user_manager.save_project_key(jira_project_key, "US", user_id)

            # Get user paths for JIRA import
            user_paths = user_manager.load_user_paths()

            try:
                _, ids_list, _, df, most_recent_date = jira_service.Jira_import_Epics_Feat_US(
                    user_paths,
                    str(project_repo_path)  # Save in project-specific folder
                )
                logger.info(f"Imported {len(ids_list)} user stories from JIRA")

                ticket_history_manager.save_ticket_history(most_recent_date, len(ids_list), "Story", jira_project_key)

            


                response_data["imported_count"] = len(ids_list)
                response_data["imported_ids"] = ids_list[:10]  # Show only first 10
            except Exception as e:
                logger.error(f"Error importing from JIRA: {str(e)}")
                response_data["jira_error"] = f"Failed to import from JIRA: {str(e)}"

        response_data["message"] = "Upload processed successfully."

        return JSONResponse(status_code=200, content=response_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading user stories: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload user stories: {str(e)}"
        )

@router.post("/documents/upload", response_model=dict)
async def upload_documents(
    jira_project_key: str = Form(None), 
    user_id: str = Form(None),         
    spec_files: List[UploadFile] = File(None),
    business_domain_files: List[UploadFile] = File(None),
    company_guidelines_files: List[UploadFile] = File(None),
    file_service: FileService = Depends(get_file_service)
):
    """
    Upload files for specifications, business domain, and/or company guidelines.
    Attach metadata: jira_project_key and user_id.
    
    Args:
        jira_project_key: Associated Jira project (optional)
        user_id: Uploader ID
        spec_files: Specification files (PDF, TXT, DOCX, etc.)
        business_domain_files: Business domain documents
        company_guidelines_files: Company guidelines
        
    Returns:
        dict: Upload results for all categories
    """
    try:
        # Validate: at least one file category
        if not any([spec_files, business_domain_files, company_guidelines_files]):
            raise HTTPException(
                status_code=400,
                detail="No files provided in any category"
            )

        result = {
            "status": "complete",
            "message": "Files processed successfully",
            "results": {}
        }

        total_files = 0
        total_successful = 0

        # Process specification files
        if spec_files:
            logger.info(f"Uploading {len(spec_files)} specification files")
            spec_result = await file_service.upload_files(
                files=spec_files,
                upload_dir= Path(settings.PROJECT_SPEC_PATH) / f"{jira_project_key}",
                allowed_extensions=['.pdf', '.txt', '.docx', '.doc', '.pptx', '.ppt'],
                category="specifications",
                jira_project_key=jira_project_key,
                user_id=user_id
            )
            result["results"]["specifications"] = {
                "saved_files": spec_result["saved_files"],
                "errors": spec_result["invalid_files"],
                "total": len(spec_files),
                "successful": len(spec_result["saved_files"])
            }
            total_files += len(spec_files)
            total_successful += len(spec_result["saved_files"])

        # Process business domain files
        if business_domain_files:
            logger.info(f"Uploading {len(business_domain_files)} business domain files")
            os.makedirs(settings.BUSINESS_DOMAIN_PATH, exist_ok=True)

            business_result = await file_service.upload_files(
                files=business_domain_files,
                upload_dir=Path(settings.BUSINESS_DOMAIN_PATH) / f"{jira_project_key}",
                allowed_extensions=['.pdf', '.txt'],
                category="business_domain",
                jira_project_key=jira_project_key,
                user_id=user_id
            )
            result["results"]["business_domain"] = {
                "saved_files": business_result["saved_files"],
                "errors": business_result["invalid_files"],
                "total": len(business_domain_files),
                "successful": len(business_result["saved_files"])
            }
            total_files += len(business_domain_files)
            total_successful += len(business_result["saved_files"])

        # Process company guidelines files
        if company_guidelines_files:
            logger.info(f"Uploading {len(company_guidelines_files)} company guidelines files")
            os.makedirs(settings.INTERNAL_COMPANY_GUIDELINES_PATH, exist_ok=True)

            guidelines_result = await file_service.upload_files(
                files=company_guidelines_files,
                upload_dir=Path(settings.INTERNAL_COMPANY_GUIDELINES_PATH) / f"{jira_project_key}",
                allowed_extensions=['.pdf', '.txt', '.docx', '.doc', '.pptx', '.ppt'],
                category="company_guidelines",
                jira_project_key=jira_project_key,
                user_id=user_id
            )
            result["results"]["company_guidelines"] = {
                "saved_files": guidelines_result["saved_files"],
                "errors": guidelines_result["invalid_files"],
                "total": len(company_guidelines_files),
                "successful": len(guidelines_result["saved_files"])
            }
            total_files += len(company_guidelines_files)
            total_successful += len(guidelines_result["saved_files"])

        # Summary
        result["summary"] = {
            "total_files": total_files,
            "total_successful": total_successful,
            "total_failed": total_files - total_successful,
            "categories_processed": len(result["results"])
        }

        if total_successful == total_files:
            result["message"] = f"All {total_files} files uploaded successfully"
        elif total_successful > 0:
            result["message"] = f"{total_successful}/{total_files} files uploaded with some errors"
        else:
            result["status"] = "failed"
            result["message"] = "Failed to upload any files"

        return result

    except Exception as e:
        logger.error(f"Error uploading files: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload files: {str(e)}"
        )
    
@router.post("/test-cases/upload")
async def upload_test_cases(
    file: Optional[UploadFile] = File(None),
    jira_project_key: Optional[str] = Form(None),
    user_id: Optional[str] = Form(None),
    file_service: FileService = Depends(get_file_service),
    jira_service: JiraService = Depends(get_jira_service),
    user_manager: UserDataManager = Depends(get_user_data_manager),
    ticket_history_manager: TicketHistoryManager = Depends(get_ticket_history_manager)
):
    """
    Upload test cases via file or JIRA import.
    
    Args:
        file: Optional Excel/JSON file
        jira_project_key: Optional JIRA project key
        
    Returns:
        JSONResponse: Upload results
    """
    try:
        logger.info("Processing test cases upload")
        
        # Ensure directory exists
        if not os.path.exists(settings.HISTORY_TC_PATH / jira_project_key):
            os.makedirs(settings.HISTORY_TC_PATH / jira_project_key, exist_ok=True)

        if not file and not jira_project_key:
            raise HTTPException(
                status_code=400,
                detail="Provide at least an Excel file or JIRA information."
            )
        
        response_data = {"status": "success"}
        
        # Handle file upload
        if file:
            if not file.filename.endswith(('.xlsx', '.xls', '.json')):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid file format. Only .xlsx, .xls, or .json allowed."
                )
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = str(uuid.uuid4())[:8]
            filename = f"{timestamp}_{unique_id}_{file.filename}"
            
            try:
                saved_path = await file_service.save_file(
                    file, settings.HISTORY_TC_PATH / jira_project_key, filename
                )                
                response_data["file_saved"] = filename
                response_data["file_size"] = saved_path.stat().st_size
            except Exception as e:
                raise HTTPException(
                    status_code=500, 
                    detail=f"Failed to save file: {str(e)}"
                )
            finally:
                file.file.close()
        
        # Handle JIRA import
        if jira_project_key:
            # Validate JIRA project key format
            if not re.match(r'^[A-Z][A-Z0-9_]+$', jira_project_key):
                response_data["jira_warning"] = "JIRA project key format may be invalid."
            
            response_data["jira_project_key"] = jira_project_key
            
            # Save project key to user data (using same key as US for consistency)
            user_manager.save_project_key(jira_project_key, "US", user_id)
            
            # Get user paths for JIRA import
            user_paths = user_manager._load_data(user_id)

            # Import test cases from JIRA
            try:
                import_path = settings.HISTORY_TC_PATH / jira_project_key
                imported_tc, ids_list, titles_list, df, most_recent_date = jira_service.Jira_import_Test_Case_Cucumber(
                    user_paths, str(import_path)
                )
                logger.info(f"Imported {len(ids_list)} test cases from JIRA")
                
                # Save ticket history
                ticket_history_manager.save_ticket_history(most_recent_date, len(ids_list), "Test", jira_project_key)

                # Add import results to response
                response_data["imported_count"] = len(ids_list)
                response_data["imported_ids"] = ids_list[:10]  # First 10 IDs as sample
                response_data["most_recent_date"] = most_recent_date.isoformat() if most_recent_date else None
                
            except Exception as e:
                logger.error(f"Error importing test cases from JIRA: {str(e)}")
                response_data["jira_error"] = f"Failed to import from JIRA: {str(e)}"
        
        response_data["message"] = "Upload processed successfully."
        
        return JSONResponse(status_code=200, content=response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading test cases: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload test cases: {str(e)}"
        )