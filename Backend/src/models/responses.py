"""
models/responses.py - Response models
"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class BaseResponse(BaseModel):
    """Base response model"""
    status: str
    message: str

class FileInfo(BaseModel):
    """File information model"""
    original_filename: str
    saved_as: str
    size_bytes: int

class FileError(BaseModel):
    """File error model"""
    filename: str
    reason: str

class FileUploadResponse(BaseResponse):
    """File upload response model"""
    saved_files: List[FileInfo] = []
    invalid_files: List[FileError] = []
    total_files: Optional[int] = None
    successful_uploads: Optional[int] = None

class DocumentUploadResponse(BaseResponse):
    """Document upload response for multiple categories"""
    results: Dict[str, Dict[str, Any]]

class JiraCredentialsResponse(BaseResponse):
    """JIRA credentials validation response"""
    jira_url: str
    username: str
    project_key: Optional[str] = None

class JiraUploadResponse(BaseResponse):
    """JIRA upload response"""
    file_saved: Optional[str] = None
    file_size: Optional[int] = None
    jira_project_key: Optional[str] = None
    jira_warning: Optional[str] = None

class GraphCreationResponse(BaseResponse):
    """Graph creation response"""
    graph_name: str

class GraphUpdateResponse(BaseResponse):
    """Graph update response"""
    upload_result: str
    update_result: Any