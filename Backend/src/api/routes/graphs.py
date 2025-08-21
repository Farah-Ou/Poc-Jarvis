"""
api/routes/graphs.py - Graph creation and management routes
"""
from fastapi import APIRouter, HTTPException, Depends, File, UploadFile, Form
from typing import Optional
import logging
from pathlib import Path
import os
import pandas as pd

from src.models.responses import GraphCreationResponse, GraphUpdateResponse
from src.utils.config import settings
from src.utils.graph_utils import GraphService
from src.utils.file_utils import FileService
from src.utils.jira_utils import JiraService
from src.utils.user_data import UserDataManager
from src.utils.ticket_history_manager_utils import TicketHistoryManager

router = APIRouter()
logger = logging.getLogger(__name__)

def get_graph_service() -> GraphService:
    """Dependency to get graph service instance"""
    return GraphService()

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

@router.post("/user-stories/create", response_model=GraphCreationResponse)
async def create_user_stories_graph(
    jira_project_key: str = Form(...),
    user_id: str = Form(...),
    graph_service: GraphService = Depends(get_graph_service)
):
    try:
        logger.info("Starting user stories graph creation")

        # 1. Input directory: CURRENT_US_PATH/jira_project_key_user_id
        project_repo_path = Path(settings.CURRENT_US_PATH) / f"{jira_project_key}"
        project_repo_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Ensured input directory exists: {project_repo_path}")

        # Warn if empty
        if not any(project_repo_path.iterdir()):
            logger.warning(
                f"Input directory is empty: {project_repo_path}. "
                "Proceeding — expecting files to be uploaded separately."
            )

        # 2. Output graph directory: US_GRAPH_PATH/us_graph_{jira_project_key}
        specific_graph_path = Path(settings.US_GRAPH_PATH) / f"{jira_project_key}"
        specific_graph_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Graph output directory: {specific_graph_path}")

        # 3. ✅ Artifacts path: US_VISUAL_GRAPH_PATH / ARTIFACTS_DIR / jira_project_key / us_graph
        artifacts_target_visual_graph_folder = (
            Path(settings.US_VISUAL_GRAPH_PATH) /
            settings.ARTIFACTS_GRAPH_VISUALIZER_PATH /
            jira_project_key /
            "us_graph"
        )
        # Ensure directory exists
        artifacts_target_visual_graph_folder.mkdir(parents=True, exist_ok=True)
        logger.info(f"Artifacts will be saved to: {artifacts_target_visual_graph_folder}")

        # 4. Other paths
        actual_graph_name = str(settings.GRAPH_US)
        Path(settings.GRAPHS_FOLDER_PATH).mkdir(parents=True, exist_ok=True)

        # 5. ✅ Call the service — ensure all paths are strings
        success = graph_service.create_graph(
            graph_folder_path=str(settings.GRAPHS_FOLDER_PATH),
            graphs_specific_folder_path=str(specific_graph_path),  
            graph_name=actual_graph_name,
            input_folder_path=str(project_repo_path),  
            output_folder=str(settings.OUTPUT_FOLDER),
            artifacts_graph_visualizer_path=str(artifacts_target_visual_graph_folder)  
        )

        if success:
            return GraphCreationResponse(
                status="success",
                message="User stories graph created successfully",
                graph_name=actual_graph_name
            )
        else:
            return GraphCreationResponse(
                status="warning",
                message="Graph creation completed with warnings - check logs",
                graph_name=actual_graph_name
            )

    except Exception as e:
        logger.error(f"Unexpected error during graph creation: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Graph creation failed: {str(e)}")

@router.post("/spec/create/{jira_project_key}", response_model=GraphCreationResponse)
async def create_spec_graph(
    jira_project_key: str,
    graph_service: GraphService = Depends(get_graph_service)
):
    """
    Create a specification graph from uploaded project specification files.

    Args:
        jira_project_key (str): The project key to scope the input and output directories.

    Returns:
        GraphCreationResponse: Result of the graph creation operation
    """
    try:
        # 1. Input files directory: PROJECT_SPEC_PATH/jira_project_key
        user_input_files_path = Path(settings.PROJECT_SPEC_PATH) / jira_project_key
        user_input_files_path_str = str(user_input_files_path)

        # Ensure input directory exists (even if empty at this point)
        user_input_files_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Ensured input directory exists: {user_input_files_path_str}")

        # 2. Output graph directory: SPEC_GRAPH_PATH/us_graph_{jira_project_key}
        specific_graph_path = Path(settings.SPEC_GRAPH_PATH) / f"{jira_project_key}"
        specific_graph_path_str = str(specific_graph_path)

        # Ensure output directory exists
        specific_graph_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created or confirmed graph output directory: {specific_graph_path_str}")

        # 3. ✅ Artifacts path: US_VISUAL_GRAPH_PATH / ARTIFACTS_DIR / jira_project_key / spec_graph
        artifacts_target_visual_graph_folder = (
            Path(settings.US_VISUAL_GRAPH_PATH) /
            settings.ARTIFACTS_GRAPH_VISUALIZER_PATH /
            jira_project_key /
            "spec_graph"
        )
        # Ensure directory exists
        artifacts_target_visual_graph_folder.mkdir(parents=True, exist_ok=True)
        logger.info(f"Artifacts will be saved to: {artifacts_target_visual_graph_folder}")

        # 4. Graph name
        actual_graph_name = str(settings.GRAPH_CONTEXT)

        # 5. Validate: Check if any files exist in the input directory
        if not user_input_files_path.exists():
            logger.error(f"Input path does not exist: {user_input_files_path}")
            raise HTTPException(status_code=400, detail="Input directory does not exist")

        if not any(user_input_files_path.iterdir()):
            logger.warning(f"No files found in input directory: {user_input_files_path}")
            raise HTTPException(
                status_code=400,
                detail=f"No specification files have been uploaded for project '{jira_project_key}'"
            )

        # 6. Call the service to create the graph
        # Ensure all paths passed as strings (if expected by create_graph)
        success = graph_service.create_graph(
            graph_folder_path=str(settings.GRAPHS_FOLDER_PATH),
            graphs_specific_folder_path=specific_graph_path_str, 
            graph_name=actual_graph_name,
            input_folder_path=user_input_files_path_str,       
            output_folder=str(settings.OUTPUT_FOLDER),
            artifacts_graph_visualizer_path=artifacts_target_visual_graph_folder
        )

        if success:
            return GraphCreationResponse(
                status="success",
                message="Specification graph created successfully",
                graph_name=actual_graph_name
            )
        else:
            return GraphCreationResponse(
                status="warning",
                message="Graph creation completed with warnings — check logs for details",
                graph_name=actual_graph_name
            )

    except HTTPException:
        # Re-raise known HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Unexpected error in create_spec_graph: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Graph creation failed: {str(e)}"
        )


@router.post("/guidelines/create/{jira_project_key}", response_model=GraphCreationResponse)
async def create_guidelines_graph(jira_project_key: str, graph_service: GraphService = Depends(get_graph_service)):
    """
    Create a specification graph from uploaded project specification files.
    
    Returns:
        GraphCreationResponse: Result of the graph creation operation
    """
    try:        
        # 1. Input files directory: PROJECT_SPEC_PATH/jira_project_key
        user_input_files_path = Path(settings.INTERNAL_COMPANY_GUIDELINES_PATH) / jira_project_key
        user_input_files_path_str = str(user_input_files_path)

        # Ensure input directory exists (even if empty at this point)
        user_input_files_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Ensured input directory exists: {user_input_files_path_str}")

        # 2. Output graph directory: SPEC_GRAPH_PATH/us_graph_{jira_project_key}
        specific_graph_path = Path(settings.GUIDELINES_GRAPH_PATH) / f"{jira_project_key}"
        specific_graph_path_str = str(specific_graph_path)

        # Ensure output directory exists
        specific_graph_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created or confirmed graph output directory: {specific_graph_path_str}")

        # 3. ✅ Artifacts path: US_VISUAL_GRAPH_PATH / ARTIFACTS_DIR / jira_project_key / guideline_graph
        artifacts_target_visual_graph_folder = (
            Path(settings.US_VISUAL_GRAPH_PATH) /
            settings.ARTIFACTS_GRAPH_VISUALIZER_PATH /
            jira_project_key /
            "guideline_graph"
        )
        # Ensure directory exists
        artifacts_target_visual_graph_folder.mkdir(parents=True, exist_ok=True)
        logger.info(f"Artifacts will be saved to: {artifacts_target_visual_graph_folder}")

        # 4. Graph name
        actual_graph_name = str(settings.GRAPH_GUIDELINES)
        

             
        # Convert string path to Path object
        project_path_obj = Path(user_input_files_path)
        logger.info(f"settings.INTERNAL_COMPANY_GUIDELINES_PATH: {settings.INTERNAL_COMPANY_GUIDELINES_PATH}")
        logger.info(f"Checking project path: {project_path_obj}")
        logger.info(f"user_input_files_path: {user_input_files_path}")
        
        # Check if directory exists and has files
        if not project_path_obj.exists() or not any(project_path_obj.iterdir()):
            raise HTTPException(
                status_code=400, 
                detail="No specification files have been uploaded"
            )
        
        
        # Call the create_graph function with adapted parameters
        success = graph_service.create_graph(
            graph_folder_path=str(settings.GRAPHS_FOLDER_PATH),
            graphs_specific_folder_path=specific_graph_path,
            graph_name=actual_graph_name,
            input_folder_path=user_input_files_path,
            output_folder=settings.OUTPUT_FOLDER,
            artifacts_graph_visualizer_path=artifacts_target_visual_graph_folder
        )
        
        if success:
            return GraphCreationResponse(
                status="success",
                message="Specification graph created successfully",
                graph_name=actual_graph_name
            )
        else:
            return GraphCreationResponse(
                status="warning",
                message="Graph creation completed but with warnings - check logs for details",
                graph_name=actual_graph_name
            )
    
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        import traceback
        error_detail = f"Graph creation failed: {str(e)}"
        logger.error(f"Error in create_spec_graph: {error_detail}\n{traceback.format_exc()}")
        
        raise HTTPException(
            status_code=500, 
            detail=error_detail
        )


@router.post("/Business-Domain/create/{jira_project_key}", response_model=GraphCreationResponse)
async def create_business_domain_graph(jira_project_key: str, graph_service: GraphService = Depends(get_graph_service)):
    """
    Create a specification graph from uploaded project specification files.
    
    Returns:
        GraphCreationResponse: Result of the graph creation operation
    """
    try:        
        # 1. Input files directory: PROJECT_SPEC_PATH/jira_project_key
        user_input_files_path = Path(settings.BUSINESS_DOMAIN_PATH) / jira_project_key
        user_input_files_path_str = str(user_input_files_path)

        # Ensure input directory exists (even if empty at this point)
        user_input_files_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Ensured input directory exists: {user_input_files_path_str}")

        # 2. Output graph directory: SPEC_GRAPH_PATH/us_graph_{jira_project_key}
        specific_graph_path = Path(settings.BUSINESS_GRAPH_PATH) / f"{jira_project_key}"
        specific_graph_path_str = str(specific_graph_path)

        # Ensure output directory exists
        specific_graph_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created or confirmed graph output directory: {specific_graph_path_str}")

        # 3. ✅ Artifacts path: US_VISUAL_GRAPH_PATH / ARTIFACTS_DIR / jira_project_key / business_domain_graph
        artifacts_target_visual_graph_folder = (
            Path(settings.US_VISUAL_GRAPH_PATH) /
            settings.ARTIFACTS_GRAPH_VISUALIZER_PATH /
            jira_project_key /
            "business_domain_graph"
        )
        # Ensure directory exists
        artifacts_target_visual_graph_folder.mkdir(parents=True, exist_ok=True)
        logger.info(f"Artifacts will be saved to: {artifacts_target_visual_graph_folder}")

        # 4. Graph name
        actual_graph_name = str(settings.GRAPH_BUSINESS_DOMAIN)
        
             
        # Convert string path to Path object
        project_path_obj = Path(user_input_files_path)
        logger.info(f"settings.BUSINESS_DOMAIN_PATH: {settings.BUSINESS_DOMAIN_PATH}")
        logger.info(f"Checking project path: {project_path_obj}")
        logger.info(f"user_input_files_path: {user_input_files_path}")
        
        # Check if directory exists and has files
        if not project_path_obj.exists() or not any(project_path_obj.iterdir()):
            raise HTTPException(
                status_code=400, 
                detail="No specification files have been uploaded"
            )
        
        
        # Call the create_graph function with adapted parameters
        success = graph_service.create_graph(
            graph_folder_path=str(settings.GRAPHS_FOLDER_PATH),
            graphs_specific_folder_path=specific_graph_path,
            graph_name=actual_graph_name,
            input_folder_path=user_input_files_path,
            output_folder=settings.OUTPUT_FOLDER,
            artifacts_graph_visualizer_path=artifacts_target_visual_graph_folder
        )
        
        if success:
            return GraphCreationResponse(
                status="success",
                message="Specification graph created successfully",
                graph_name=actual_graph_name
            )
        else:
            return GraphCreationResponse(
                status="warning",
                message="Graph creation completed but with warnings - check logs for details",
                graph_name=actual_graph_name
            )
    
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        import traceback
        error_detail = f"Graph creation failed: {str(e)}"
        logger.error(f"Error in create_spec_graph: {error_detail}\n{traceback.format_exc()}")
        
        raise HTTPException(
            status_code=500, 
            detail=error_detail
        )
    

@router.post("/test-cases/create/{jira_project_key}", response_model=GraphCreationResponse)
async def create_test_cases_graph(jira_project_key: str, graph_service: GraphService = Depends(get_graph_service)):
    """
    Create a specification graph from uploaded project specification files.
    
    Returns:
        GraphCreationResponse: Result of the graph creation operation
    """
    try:
        # 1. Input files directory: PROJECT_SPEC_PATH/jira_project_key
        user_input_files_path = Path(settings.HISTORY_TC_PATH) / jira_project_key
        user_input_files_path_str = str(user_input_files_path)

        # Ensure input directory exists (even if empty at this point)
        user_input_files_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Ensured input directory exists: {user_input_files_path_str}")

        # 2. Output graph directory: SPEC_GRAPH_PATH/us_graph_{jira_project_key}
        specific_graph_path = Path(settings.TC_HISTORY_GRAPH_PATH) / f"{jira_project_key}"
        specific_graph_path_str = str(specific_graph_path)

        # Ensure output directory exists
        specific_graph_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created or confirmed graph output directory: {specific_graph_path_str}")

        # 3. ✅ Artifacts path: US_VISUAL_GRAPH_PATH / ARTIFACTS_DIR / jira_project_key / test_case_graph
        artifacts_target_visual_graph_folder = (
            Path(settings.US_VISUAL_GRAPH_PATH) /
            settings.ARTIFACTS_GRAPH_VISUALIZER_PATH /
            jira_project_key /
            "test_case_graph"
        )
        # Ensure directory exists
        artifacts_target_visual_graph_folder.mkdir(parents=True, exist_ok=True)
        logger.info(f"Artifacts will be saved to: {artifacts_target_visual_graph_folder}")

        # 4. Graph name
        actual_graph_name = str(settings.GRAPH_HISTORY_TC)
        
                
        # Convert string path to Path object
        project_path_obj = Path(user_input_files_path)
        logger.info(f"settings.HISTORY_TC_PATH: {settings.HISTORY_TC_PATH}")
        logger.info(f"Checking project path: {project_path_obj}")
        logger.info(f"user_input_files_path: {user_input_files_path}")
        
        # Check if directory exists and has files
        if not project_path_obj.exists() or not any(project_path_obj.iterdir()):
            raise HTTPException(
                status_code=400, 
                detail="No project key or files have been uploaded"
            )
        
        
        # Call the create_graph function with adapted parameters
        success = graph_service.create_graph(
            graph_folder_path=str(settings.GRAPHS_FOLDER_PATH),
            graphs_specific_folder_path=specific_graph_path,
            graph_name=actual_graph_name,
            input_folder_path=user_input_files_path,
            output_folder=settings.OUTPUT_FOLDER,
            artifacts_graph_visualizer_path=artifacts_target_visual_graph_folder
        )
        
        if success:
            return GraphCreationResponse(
                status="success",
                message="Test cases graph created successfully",
                graph_name=actual_graph_name
            )
        else:
            return GraphCreationResponse(
                status="warning",
                message="Graph creation completed but with warnings - check logs for details",
                graph_name=actual_graph_name
            )
    
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        import traceback
        error_detail = f"Graph creation failed: {str(e)}"
        logger.error(f"Error in create_test_cases_graph: {error_detail}\n{traceback.format_exc()}")
        
        raise HTTPException(
            status_code=500, 
            detail=error_detail
        )
    


@router.post("/test-cases/update/{jira_project_key}/{user_id}", response_model=GraphUpdateResponse)
async def update_test_cases_graph(
    jira_project_key: str, 
    user_id: str,
    file: Optional[UploadFile] = File(None),    
    graph_service: GraphService = Depends(get_graph_service),
    jira_service: JiraService = Depends(get_jira_service),
    user_manager: UserDataManager = Depends(get_user_data_manager),
    ticket_history_manager: TicketHistoryManager = Depends(get_ticket_history_manager)
):
    """
    Update test cases graph with new data from file or JIRA.
    
    Args:
        file: Optional Excel file with test cases
        
    Returns:
        GraphUpdateResponse: Update result
    """
    ticket_type = "Test"
            
    # 1. Input files directory: PROJECT_SPEC_PATH/jira_project_key
    user_input_files_path = Path(settings.HISTORY_TC_PATH) / jira_project_key
    user_input_files_path_str = str(user_input_files_path)

    # Ensure input directory exists (even if empty at this point)
    user_input_files_path.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured input directory exists: {user_input_files_path_str}")

    # 2. Output graph directory: SPEC_GRAPH_PATH/us_graph_{jira_project_key}
    specific_graph_path = Path(settings.TC_HISTORY_GRAPH_PATH) / f"{jira_project_key}"
    specific_graph_path_str = str(specific_graph_path)
    # Ensure output directory exists
    specific_graph_path.mkdir(parents=True, exist_ok=True)
    logger.info(f"Created or confirmed graph output directory: {specific_graph_path_str}")
    # 3. Visualization artifacts folder
    artifacts_target_visual_graph_folder = str(
        Path(settings.US_VISUAL_GRAPH_PATH) / settings.ARTIFACTS_GRAPH_VISUALIZER_PATH / jira_project_key / "test_case_graph"
    )
    Path(artifacts_target_visual_graph_folder).mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured visualization artifacts directory exists: {artifacts_target_visual_graph_folder}")
    # 4. Graph name
    actual_graph_name = str(settings.GRAPH_HISTORY_TC)

    try:
        if not file and not jira_project_key:
            raise HTTPException(
                status_code=400,
                detail="Provide at least an Excel file or JIRA information."
            )
        
        logger.warning("Updating test cases graph")
        
        # Handle file upload if provided
        if file:
            if not file.filename.endswith(('.xlsx', '.xls', '.json')):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid file format. Only .xlsx, .xls, or .json allowed."
                )
            
            file_service = get_file_service()
            saved_filename = await file_service.save_file(file, user_input_files_path)
            logger.warning(f"File saved as: {saved_filename}")
        
        # Handle JIRA import if provided
        if jira_project_key:
            # Load history and get the most recent date
            history = ticket_history_manager.load_latest_ticket_history(ticket_type, jira_project_key)
            most_recent_date = history["most_recent_ticket_date"]

            user_paths = user_manager._load_data(us_user_id=user_id)

            # Convert ISO format date to expected format
        try:
            
            if isinstance(most_recent_date, str):
                # Parse ISO format date
                parsed_date = pd.to_datetime(most_recent_date)
                # Convert to simple format (YYYY-MM-DD HH:MM)
                formatted_date = parsed_date.strftime('%Y-%m-%d %H:%M')
                print("update Formatted date for Jira import: *********", formatted_date)
            else:
                # If it's already a datetime object
                formatted_date = most_recent_date.strftime('%Y-%m-%d %H:%M')
                logger.info("update Formatted date for Jira import: *********", formatted_date)
        except Exception as e:
            logger.error(f"Error formatting date: {e}")
            # Fallback to a default date or raise an error
            formatted_date = "2024-01-01"  # Or use a sensible default
            logger.error("update Using fallback date: *********", formatted_date)

        
        # Initialize variables at the beginning
        ids_list = []
        
        if jira_project_key:
            # Import updated tickets from JIRA
            logger.info("starting import tickets from JIRA")
            imported_file_path, ids_list, titles_list, dataframe, most_recent_date = jira_service.jira_import_tickets_by_date(
                user_paths,                
                user_input_files_path,
                ticket_type,
                formatted_date
            )
            logger.warning(f"Imported {len(ids_list)} tickets from JIRA")
            logger.warning(f"Imported file path: {imported_file_path}")
            logger.warning(f"Imported titles: {titles_list}")
            logger.warning(f"most_recent_date: {most_recent_date}")
            logger.warning(f"formatted_date: {formatted_date}")

            logger.warning(f"✅ DONE import tickets from JIRA {ticket_type}, ✅ imported {len(ids_list)} to {imported_file_path} ✅  && starting save tickets history")
            # Save updated history
            ticket_history_manager.save_ticket_history(
                most_recent_date,
                len(ids_list),
                ticket_type,
                jira_project_key
            )
            logger.info("✅ DONE save tickets history")
            

        logger.info("starting graph update")
        # Update the graph
        graph_service.graph_update(
            specific_graph_path,
            actual_graph_name,
            user_input_files_path,            
            artifacts_target_visual_graph_folder,
            imported_file_path
        )
        logger.info("✅ DONE graph update")
        
        # Mark graph as updated
        ticket_history_manager.mark_graph_as_updated(ticket_type, jira_project_key)
        
        logger.info("✅ marking of Graph update completed successfully")

        return GraphUpdateResponse(
            status="success",
            message="Test cases graph updated successfully",
            upload_result=f"Files processed: {1 if file else 0}",
            update_result={
                "graph_name": actual_graph_name,
                "updated_files": 1 if file else 0,
                "jira_tickets_imported": len(ids_list)
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating test cases graph: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Graph update failed: {str(e)}"
        )
    

@router.post("/user-stories/update/{jira_project_key}/{user_id}", response_model=GraphUpdateResponse)
async def update_user_stories_graph(
    jira_project_key: str,
    user_id: str,
    file: Optional[UploadFile] = File(None),
    graph_service: GraphService = Depends(get_graph_service),
    jira_service: JiraService = Depends(get_jira_service),
    user_manager: UserDataManager = Depends(get_user_data_manager),
    ticket_history_manager: TicketHistoryManager = Depends(get_ticket_history_manager)
):
    """
    Update user stories graph with new data from file or JIRA.

    Args:
        file: Optional Excel file with test cases
        jira_project_key: Optional JIRA project key
        
    Returns:
        GraphUpdateResponse: Update result
    """

    ticket_type = "Story"

    # user_input_files_path = str(settings.CURRENT_US_PATH)
    # specific_graph_path = str(settings.US_GRAPH_PATH)
    # artifacts_target_visual_graph_folder = os.path.join(str(settings.US_VISUAL_GRAPH_PATH), str(settings.ARTIFACTS_GRAPH_VISUALIZER_PATH))
    # actual_graph_name = str(settings.GRAPH_US)

    # 1. Input files directory: PROJECT_SPEC_PATH/jira_project_key
    user_input_files_path = Path(settings.CURRENT_US_PATH) / jira_project_key
    user_input_files_path_str = str(user_input_files_path)

    # Ensure input directory exists (even if empty at this point)
    user_input_files_path.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured input directory exists: {user_input_files_path_str}")

    # 2. Output graph directory: SPEC_GRAPH_PATH/us_graph_{jira_project_key}
    specific_graph_path = Path(settings.US_GRAPH_PATH) / f"{jira_project_key}"
    specific_graph_path_str = str(specific_graph_path)
    # Ensure output directory exists
    specific_graph_path.mkdir(parents=True, exist_ok=True)
    logger.info(f"Created or confirmed graph output directory: {specific_graph_path_str}")
    # 3. Visualization artifacts folder
    artifacts_target_visual_graph_folder = str(
        Path(settings.US_VISUAL_GRAPH_PATH) / settings.ARTIFACTS_GRAPH_VISUALIZER_PATH / jira_project_key / "us_graph"
    )
    Path(artifacts_target_visual_graph_folder).mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured visualization artifacts directory exists: {artifacts_target_visual_graph_folder}")
    # 4. Graph name
    actual_graph_name = str(settings.GRAPH_US)

    try:
        if not file and not jira_project_key:
            logger.warning("No file or JIRA project key provided")
            raise HTTPException(
                status_code=400,
                detail="Provide at least an Excel file or JIRA information."
            )

        logger.warning(f"jira proj key : {jira_project_key} ; Updating user stories graph")

        # Handle file upload if provided
        if file:
            if not file.filename.endswith(('.xlsx', '.xls', '.json')):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid file format. Only .xlsx, .xls, or .json allowed."
                )
            
            file_service = get_file_service()
            saved_filename = await file_service.save_file(file, user_input_files_path)
            logger.warning(f"File saved as: {saved_filename}")
        
        # Handle JIRA import if provided
        if jira_project_key:
            # Load history and get the most recent date
            logger.warning("Loading latest ticket history")
            history = ticket_history_manager.load_latest_ticket_history(ticket_type, jira_project_key)
            logger.warning(f" Loaded ticket history: {history}")
            most_recent_date = history["most_recent_ticket_date"]
            
            user_paths = user_manager._load_data(user_id)

            # Convert ISO format date to expected format
        try:
            import pandas as pd
            if isinstance(most_recent_date, str):
                # Parse ISO format date
                parsed_date = pd.to_datetime(most_recent_date)
                # Convert to simple format (YYYY-MM-DD HH:MM)
                formatted_date = parsed_date.strftime('%Y-%m-%d %H:%M')
                logger.info("update Formatted date for Jira import: *********", formatted_date)
            else:
                # If it's already a datetime object
                formatted_date = most_recent_date.strftime('%Y-%m-%d %H:%M')
                logger.info("update Formatted date for Jira import: *********", formatted_date)
        except Exception as e:
            logger.error(f"Error formatting date: {e}")
            # Fallback to a default date or raise an error
            formatted_date = "2024-01-01"  # Or use a sensible default
            logger.error("update Using fallback date: *********", formatted_date)

        
        # Initialize variables at the beginning
        ids_list = []
        
        if jira_project_key:
            # Import updated tickets from JIRA
            logger.warning("starting import tickets from JIRA")
            imported_file_path, ids_list, titles_list, dataframe, most_recent_date = jira_service.jira_import_tickets_by_date(
                user_paths,                
                user_input_files_path,
                ticket_type,
                formatted_date
            )
            logger.warning(f"Imported {len(ids_list)} tickets from JIRA")
            logger.warning(f"Imported file path: {imported_file_path}")
            logger.warning(f"Imported titles: {titles_list}")
            logger.warning(f"most_recent_date: {most_recent_date}")
            logger.warning(f"formatted_date: {formatted_date}")

            logger.warning(f"✅ DONE import tickets from JIRA {ticket_type}, ✅ imported {len(ids_list)} to {imported_file_path} ✅  && starting save tickets history")
            # Save updated history
            ticket_history_manager.save_ticket_history(
                most_recent_date,
                len(ids_list),
                ticket_type,
                jira_project_key
            )
            logger.warning(f"✅ DONE save tickets history {ticket_type} && starting graph update")
            

        logger.info("starting graph update")
        # Update the graph
        graph_service.graph_update(
            specific_graph_path,
            actual_graph_name,
            str(user_input_files_path),            
            artifacts_target_visual_graph_folder,
            imported_file_path
        )
        logger.warning("✅ DONE graph update")
        
        # Mark graph as updated
        ticket_history_manager.mark_graph_as_updated(ticket_type, jira_project_key)

        logger.warning("✅ marking of Graph update completed successfully")

        return GraphUpdateResponse(
            status="success",
            message="Test cases graph updated successfully",
            upload_result=f"Files processed: {1 if file else 0}",
            update_result={
                "graph_name": actual_graph_name,
                "updated_files": 1 if file else 0,
                "jira_tickets_imported": len(ids_list)
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user stories graph: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Graph update failed: {str(e)}"
        )
   
@router.get("/status/{graph_type}")
async def get_graph_status(
    graph_type: str,
    graph_service: GraphService = Depends(get_graph_service)
):
    """
    Get the status of a specific graph.
    
    Args:
        graph_type: Type of graph (spec, user-stories, guidelines, test-cases)
        
    Returns:
        dict: Graph status information
    """
    try:
        graph_mapping = {
            "spec": {
                "path": settings.SPEC_GRAPH_PATH,
                "name": settings.GRAPH_CONTEXT,
                "input_path": settings.PROJECT_SPEC_PATH
            },
            "user-stories": {
                "path": settings.US_GRAPH_PATH,
                "name": settings.GRAPH_US,
                "input_path": settings.CURRENT_US_PATH
            },
            "guidelines": {
                "path": settings.GUIDELINES_GRAPH_PATH,
                "name": settings.GRAPH_GUIDELINES,
                "input_path": settings.INTERNAL_COMPANY_GUIDELINES_PATH
            },
            "test-cases": {
                "path": settings.TC_HISTORY_GRAPH_PATH,
                "name": settings.GRAPH_HISTORY_TC,
                "input_path": settings.HISTORY_TC_PATH
            }
        }
        
        if graph_type not in graph_mapping:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid graph type. Must be one of: {list(graph_mapping.keys())}"
            )
        
        graph_info = graph_mapping[graph_type]
        status = graph_service.get_graph_status(
            graph_path=graph_info["path"],
            input_path=graph_info["input_path"]
        )
        
        return {
            "graph_type": graph_type,
            "graph_name": graph_info["name"],
            "status": status
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting graph status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get graph status: {str(e)}"
        )

@router.delete("/{graph_type}")
async def delete_graph(
    graph_type: str,
    graph_service: GraphService = Depends(get_graph_service)
):
    """
    Delete a specific graph and its associated files.
    
    Args:
        graph_type: Type of graph to delete
        
    Returns:
        dict: Deletion status
    """
    try:
        graph_mapping = {
            "spec": {
                "path": settings.SPEC_GRAPH_PATH,
                "visual_path": settings.SPEC_VISUAL_GRAPH_PATH,
                "name": settings.GRAPH_CONTEXT
            },
            "user-stories": {
                "path": settings.US_GRAPH_PATH,
                "visual_path": settings.US_VISUAL_GRAPH_PATH,
                "name": settings.GRAPH_US
            },
            "guidelines": {
                "path": settings.GUIDELINES_GRAPH_PATH,
                "visual_path": settings.GUIDELINES_VISUAL_GRAPH_PATH,
                "name": settings.GRAPH_GUIDELINES
            },
            "test-cases": {
                "path": settings.TC_HISTORY_GRAPH_PATH,
                "visual_path": settings.TC_HISTORY_VISUAL_GRAPH_PATH,
                "name": settings.GRAPH_HISTORY_TC
            }
        }
        
        if graph_type not in graph_mapping:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid graph type. Must be one of: {list(graph_mapping.keys())}"
            )
        
        graph_info = graph_mapping[graph_type]
        
        # Delete the graph
        deleted = graph_service.delete_graph(
            graph_path=graph_info["path"],
            visual_path=graph_info["visual_path"]
        )
        
        if deleted:
            return {
                "status": "success",
                "message": f"Graph '{graph_info['name']}' deleted successfully",
                "graph_type": graph_type
            }
        else:
            return {
                "status": "info",
                "message": f"Graph '{graph_info['name']}' was not found or already deleted",
                "graph_type": graph_type
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting graph: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete graph: {str(e)}"
        )