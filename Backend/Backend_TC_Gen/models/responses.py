from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

class StandardResponse(BaseModel):
    message: str
    status: str = "success"

class UploadResponse(StandardResponse):
    file_saved: Optional[str] = None
    file_size: Optional[int] = None
    jira_project_key: Optional[str] = None
    source_state_field_name: Optional[str] = None
    target_state_field_name: Optional[str] = None
    jira_warning: Optional[str] = None

class GenerationResponse(StandardResponse):
    excel_path: str
    json_path: str
    total_cases_generated: int
    total_cases_in_history: int

class JiraUpdateResponse(StandardResponse):
    success: bool
    output_file: str
    records_processed: int

class E2ETestGenerationResponse(BaseModel):
    status: str = Field(..., description="Generation status")
    message: str = Field(..., description="Response message")
    test_steps_count: Optional[int] = Field(None, description="Number of test steps generated")
    test_flows_count: Optional[int] = Field(None, description="Number of test flows generated")
    files_generated: Optional[List[str]] = Field(default_factory=list, description="List of generated files")
    processing_time: Optional[float] = Field(None, description="Processing time in seconds")
