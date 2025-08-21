"""
utils/config.py - Application Configuration
"""
import os
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings"""
    
    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Jarvis Tester Agent"
    VERSION: str = "2.0.2"
    
    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:8000",
    ]
    
    # External API Keys
    
    JIRA_TOKEN: str
    GRAPHRAG_API_KEY: str
    OPENAI_API_KEY: str
    AUTOGEN_USE_DOCKER: bool = False  # Use Docker for Autogen
    
    # LLM Configurations
    LLM_MODEL_GPT4_TURBO: str = "gpt-4-turbo"
    LLM_MODEL_GPT4O_MINI: str = "gpt-4o-mini" 
    LLM_MODEL_GPT4O: str = "gpt-4o"
    
    # Base Directories
    BASE_DIR: Path = Path(__file__).parent.parent.parent.parent
    
    # Data Directories
    @property
    def US_PATH_TO_GENERATE(self) -> Path:
        return self.USER_DATA_PATH / "US_to_generate_folder"
    
    @property
    def ALL_INPUT(self) -> Path:
        return self.BASE_DIR / "ALL_INPUT"
    
    @property
    def ALL_OUTPUT(self) -> Path:
        return self.BASE_DIR / "ALL_OUTPUT"
    
    @property
    def ALL_INTERMEDIATE_STATE_CONFIG(self) -> Path:
        return self.BASE_DIR / "ALL_INTERMEDIATE_STATE_CONFIG"
    
    @property
    def Ticket_History_Management(self) -> Path:
        return self.ALL_INTERMEDIATE_STATE_CONFIG / "Ticket_History_Management"

    @property
    def USER_PATHS_JSON(self) -> Path:
        return self.ALL_INTERMEDIATE_STATE_CONFIG / "USER_PATHS_JSON" 
    
    @property
    def USER_PATHS_JSON_FILE(self) -> Path:
        return self.USER_PATHS_JSON /  "User_data.json"

    @property
    def Custom_prompts_tc(self) -> Path:
        return self.ALL_INTERMEDIATE_STATE_CONFIG / "Custom prompts tuning TC graph" / "Custom prompts for tc" 
    @property
    def Custom_yaml_tc(self) -> Path:
        return self.ALL_INTERMEDIATE_STATE_CONFIG / "Custom prompts tuning TC graph" / "Custom yaml tc"

    @property
    def Custom_yaml_light_model(self) -> Path:
        return self.ALL_INTERMEDIATE_STATE_CONFIG / "Custom prompts or config tuning graph" / "custom yaml light model"

    @property
    def USER_DATA_PATH(self) -> Path:
        return self.ALL_INPUT / "User_Data"
    
    # @property
    # def DATAFRAMES_PATH(self) -> Path:
    #     return self.ALL_OUTPUT / "Created_Dataframes"
    
    @property
    def GRAPHS_FOLDER_PATH(self) -> Path:
        return self.BASE_DIR / "Graphs"
    
    @property
    def GRAPHS_VISUALS_FOLDER_PATH(self) -> Path:
        return self.BASE_DIR / "Created_Graphs"
    
    # Project Specific Paths
    @property
    def PROJECT_SPEC_PATH(self) -> Path:
        return self.USER_DATA_PATH / "Project_Spec"
    
    @property
    def BUSINESS_DOMAIN_PATH(self) -> Path:
        return self.USER_DATA_PATH / "Business_Domain"
    
    @property
    def INTERNAL_COMPANY_GUIDELINES_PATH(self) -> Path:
        return self.USER_DATA_PATH / "Internal_company_guidelines"
    
    @property
    def CURRENT_US_PATH(self) -> Path:
        return self.USER_DATA_PATH / "Current_User_Stories"

    
    @property
    def HISTORY_TC_PATH(self) -> Path:
        return self.USER_DATA_PATH / "Previous_Test_Cases"
    
    @property
    def BUSINESS_DOMAIN_PATH(self) -> Path:
        return self.USER_DATA_PATH / "Business_Domain"
    
    # Graph Paths
    @property
    def EXPERT_RGAA(self) -> Path:
        return self.GRAPHS_FOLDER_PATH / "Expert_RGAA"

    @property
    def EXPERT_FINANCE(self) -> Path:
        return self.GRAPHS_FOLDER_PATH / "Expert_Finance_IFRS"
    
    @property
    def EXPERT_ACCOUNTING(self) -> Path:
        return self.GRAPHS_FOLDER_PATH / "Expert_Accounting"


    @property
    def US_GRAPH_PATH(self) -> Path:
        return self.GRAPHS_FOLDER_PATH / "us_graph"
    
    @property
    def SPEC_GRAPH_PATH(self) -> Path:
        return self.GRAPHS_FOLDER_PATH / "project_contxt_graph"
    
    @property
    def GUIDELINES_GRAPH_PATH(self) -> Path:
        return self.GRAPHS_FOLDER_PATH / "guidelines_graph"

    @property
    def BUSINESS_GRAPH_PATH(self) -> Path:
        return self.GRAPHS_FOLDER_PATH / "business_graph"
    
    @property
    def TC_HISTORY_GRAPH_PATH(self) -> Path:
        return self.GRAPHS_FOLDER_PATH / "test_cases_history_graph"
    
    # Visual Graph Paths
    @property
    def US_VISUAL_GRAPH_PATH(self) -> Path:
        return self.GRAPHS_VISUALS_FOLDER_PATH / "US-Graph-Visual"
    
    @property
    def SPEC_VISUAL_GRAPH_PATH(self) -> Path:
        return self.GRAPHS_VISUALS_FOLDER_PATH / "Context-Graph-Visual"
    
    @property
    def GUIDELINES_VISUAL_GRAPH_PATH(self) -> Path:
        return self.GRAPHS_VISUALS_FOLDER_PATH / "Guidelines-Graph-Visual"
    @property
    def BUSINESS_DOMAIN_VISUAL_GRAPH_PATH(self) -> Path:
        return self.GRAPHS_VISUALS_FOLDER_PATH / "Business-Domain-Graph-Visual"
    
    @property
    def TC_HISTORY_VISUAL_GRAPH_PATH(self) -> Path:
        return self.GRAPHS_VISUALS_FOLDER_PATH / "Test-Cases-History-Graph-Visual"
    
    # Archive Paths
    @property
    def ARCHIVED_HISTORY_TC_FILES_DIRECTORY(self) -> Path:
        return self.ALL_INPUT / "User_Data_Archived" / "Archived_History_TC_Files"
    
    @property
    def ARCHIVED_PROJECT_SPEC_FILES_DIRECTORY(self) -> Path:
        return self.ALL_INPUT / "User_Data_Archived" / "Archived_Project_Spec_Files"
    
    @property
    def ARCHIVED_CURRENT_US_FILES_DIRECTORY(self) -> Path:
        return self.ALL_INPUT / "User_Data_Archived" / "Archived_Current_US_Files"
    
    @property
    def ARCHIVED_GRAPH_TC_FILES_DIRECTORY(self) -> Path:
        return self.ALL_INPUT / "Graph_Archived_Files" / "Archived_TC_History_Files"
    @property
    def ARCHIVED_GRAPH_BUSINESS_FILES_DIRECTORY(self) -> Path:
        return self.ALL_INPUT / "Graph_Archived_Files" / "Archived_Business_Domain_Files"
    
    # Graph Configuration
    OUTPUT_FOLDER: str = "input"
    GRAPH_CONTEXT: str = "project_contxt_graph"
    GRAPH_US: str = "us_graph"
    GRAPH_GUIDELINES: str = "guidelines_graph"
    GRAPH_BUSINESS_DOMAIN: str = "business_domain_graph"
    GRAPH_HISTORY_TC: str = "test_cases_history_graph"
    SAVE_OUTPUT_FOLDER: str = "Generated_output"
    ARTIFACTS_GRAPH_VISUALIZER_PATH: str = "graphrag-visualizer/public/artifacts"
    
    # File Upload Settings
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_FILE_EXTENSIONS: List[str] = ['.pdf', '.txt', '.xlsx', '.xls', '.json']
    
    def create_directories(self):
        """Create necessary directories if they don't exist"""
        directories = [
            self.USER_DATA_PATH,
            # self.DATAFRAMES_PATH,
            self.GRAPHS_FOLDER_PATH,
            self.Ticket_History_Management,
            self.GRAPHS_VISUALS_FOLDER_PATH,
            self.PROJECT_SPEC_PATH,
            self.BUSINESS_DOMAIN_PATH,
            self.INTERNAL_COMPANY_GUIDELINES_PATH,
            self.CURRENT_US_PATH,
            self.HISTORY_TC_PATH,
            self.ARCHIVED_HISTORY_TC_FILES_DIRECTORY,
            self.ARCHIVED_PROJECT_SPEC_FILES_DIRECTORY,
            self.ARCHIVED_CURRENT_US_FILES_DIRECTORY,
            self.ARCHIVED_GRAPH_TC_FILES_DIRECTORY,
            self.ARCHIVED_GRAPH_BUSINESS_FILES_DIRECTORY,
            self.US_GRAPH_PATH,
            self.SPEC_GRAPH_PATH,
            self.GUIDELINES_GRAPH_PATH,
            self.BUSINESS_GRAPH_PATH,
            self.TC_HISTORY_GRAPH_PATH,
            self.ALL_INPUT,
            self.ALL_OUTPUT,
            self.ALL_INTERMEDIATE_STATE_CONFIG,
            self.USER_PATHS_JSON,
            self.US_PATH_TO_GENERATE,
            self.EXPERT_ACCOUNTING,
            self.EXPERT_RGAA,
            self.EXPERT_FINANCE
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        env_file_encoding = 'utf-8'

# Create settings instance
settings = Settings()

# Create directories on import
settings.create_directories()