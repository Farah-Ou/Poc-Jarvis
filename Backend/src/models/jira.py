
"""
models/jira.py - JIRA related Pydantic models
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional
import re

class JiraCredentials(BaseModel):
    """JIRA credentials model"""
    jira_server_url: str = Field(..., description="JIRA server URL")
    jira_username: str = Field(..., description="JIRA username or email")
    jira_project_key: str = Field(..., description="JIRA Project Key (required)")
    user_id: str = Field(..., description="User ID performing the upload or import") 

    @field_validator('jira_server_url')
    @classmethod
    def validate_server_url(cls, v: str) -> str:
        if not v.startswith(('http://', 'https://')):
            raise ValueError('Server URL must start with http:// or https://')
        return v.rstrip('/')

    @field_validator('jira_username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        if not v or len(v.strip()) == 0:
            raise ValueError('Username cannot be empty')
        return v.strip()

    @field_validator('jira_project_key')
    @classmethod
    def validate_project_key(cls, v: str) -> str:
        v = v.strip().upper()
        if not re.match(r'^[A-Z][A-Z0-9_]*$', v):
            raise ValueError('Invalid JIRA project key format (e.g., PROJ)')
        return v

    @field_validator('user_id')
    @classmethod
    def validate_user_id(cls, v: str) -> str:
        if not v or len(v.strip()) == 0:
            raise ValueError('user_id cannot be empty')
        return v.strip()
    
class JiraProjectRequest(BaseModel):
    """JIRA project request model"""
    jira_project_key: str = Field(..., description="JIRA project key")

    @field_validator('jira_project_key')
    @classmethod
    def validate_project_key(cls, v: str) -> str:
        if not re.match(r'^[A-Z][A-Z0-9_]+$', v):
            raise ValueError('Invalid JIRA project key format')
        return v.upper()

class JiraUploadRequest(BaseModel):
    """JIRA upload request with optional file"""
    jira_project_key: Optional[str] = Field(None, description="JIRA project key")

    @field_validator('jira_project_key')
    @classmethod
    def validate_project_key(cls, v: Optional[str]) -> Optional[str]:
        if v and not re.match(r'^[A-Z][A-Z0-9_]+$', v):
            raise ValueError('Invalid JIRA project key format')
        return v.upper() if v else v
