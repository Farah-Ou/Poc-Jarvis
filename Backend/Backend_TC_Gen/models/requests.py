from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum

class FormatRequest(BaseModel):
    format: str

class JiraUploadData(BaseModel):
    jira_project_key: Optional[str] = None
    source_state_field_name: Optional[str] = None
    target_state_field_name: Optional[str] = None

# Essential Enums
class TestStatus(str, Enum):
    PASSING = "passing"
    NON_PASSING = "Non Passing"
    EDGE_CASE = "edge_case"

class LLMModel(str, Enum):
    GPT4_TURBO = "gpt4_turbo"
    GPT4 = "gpt4"
    GPT35_TURBO = "gpt35_turbo"

# 1. MAIN REQUEST/RESPONSE MODELS (Essential)
class E2ETestGenerationRequest(BaseModel):
    force_regenerate: Optional[bool] = Field(False, description="Force regeneration of tests")
    llm_model: Optional[LLMModel] = Field(LLMModel.GPT4_TURBO, description="LLM model to use")
    max_rounds_phase_1: Optional[int] = Field(7, ge=1, le=20, description="Max rounds for phase 1")
    max_rounds_phase_2: Optional[int] = Field(5, ge=1, le=15, description="Max rounds for phase 2")
    save_intermediate: Optional[bool] = Field(True, description="Save intermediate results")
