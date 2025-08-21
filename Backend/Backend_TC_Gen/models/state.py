from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum

class ProcessingState:
    def __init__(self):
        self.jira_input: bool = False
        self.us_file_uploaded: bool = False
        self.context_file_uploaded: bool = False
        self.context_graph_exists: bool = False
        self.ensemble_paths: Dict[str, str] = {}
        self.selected_format: str = ""
        self.ids_list: List[str] = []
        self.titles_list: List[str] = []
        self.last_imported_excel_path: Optional[str] = None
        # Add E2E specific state
        self.e2e_generation_state: Optional['E2EProcessingState'] = None

class TestCaseEntry:
    def __init__(self, us_id: str, us_title: str, test_case: str,
                 prompt: str, costs: Dict[str, str], metadata: Dict[str, str]):
        self.timestamp = datetime.now().isoformat()
        self.us_id = us_id
        self.us_title = us_title
        self.test_case = test_case
        self.prompt = prompt
        self.costs = costs
        self.metadata = metadata
   
    def to_dict(self):
        return {
            "timestamp": self.timestamp,
            "us_id": self.us_id,
            "us_title": self.us_title,
            "test_case": self.test_case,
            "prompt": self.prompt,
            "costs": self.costs,
            "metadata": self.metadata
        }

# Global state instance
_processing_state = None

def get_processing_state() -> ProcessingState:
    """Get global processing state instance (singleton pattern)"""
    global _processing_state
    if _processing_state is None:
        _processing_state = ProcessingState()
    return _processing_state

def reset_processing_state():
    """Reset the global processing state"""
    global _processing_state
    _processing_state = ProcessingState()

def update_processing_state(**kwargs):
    """Update processing state with given parameters"""
    state = get_processing_state()
    for key, value in kwargs.items():
        if hasattr(state, key):
            setattr(state, key, value)
        else:
            raise AttributeError(f"ProcessingState has no attribute '{key}'")

# NEW: E2E specific state management functions
def update_e2e_processing_state(e2e_state: 'E2EProcessingState'):
    """Update E2E processing state"""
    state = get_processing_state()
    state.e2e_generation_state = e2e_state

def get_e2e_processing_state() -> Optional['E2EProcessingState']:
    """Get current E2E processing state"""
    state = get_processing_state()
    return state.e2e_generation_state

class TestStatus(str, Enum):
    PASSING = "passing"
    NON_PASSING = "Non Passing"
    EDGE_CASE = "edge_case"

class E2EProcessingState(BaseModel):
    phase: str = Field(..., description="Current processing phase")
    status: str = Field(..., description="Processing status")
    progress: float = Field(0.0, ge=0.0, le=100.0, description="Progress percentage")
    current_step: Optional[str] = Field(None, description="Current processing step")
    started_at: datetime = Field(default_factory=datetime.now, description="Processing start time")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last update time")
    error_message: Optional[str] = Field(None, description="Error message if failed")

# Core test models for internal state tracking
class TestStep(BaseModel):
    id: int = Field(..., description="Test step ID")
    name: str = Field(..., description="Test step name")
    feature: str = Field(..., description="Associated feature ID")
    status: TestStatus = Field(..., description="Test step status")

class EnrichedTestStep(BaseModel):
    name: str = Field(..., description="Test step name")
    features: List[str] = Field(default_factory=list, description="List of feature IDs")
    feature_names: Optional[List[str]] = Field(default_factory=list, description="List of feature names")

class TestFlow(BaseModel):
    titre: str = Field(..., description="Test flow title")
    steps: List[EnrichedTestStep] = Field(default_factory=list, description="Test flow steps")