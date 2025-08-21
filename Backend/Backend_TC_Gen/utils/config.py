"""
utils/config.py - Application Configuration
"""
import os
from pathlib import Path
from typing import List, Dict, Any
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import logging
# Load environment variables
load_dotenv()
# ------------------ Logging Setup ------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
class Settings(BaseSettings):
    """Application settings"""
    
    # Server Configuration
    HOST: str = "127.0.0.1"
    PORT: int = 8003
    DEBUG: bool = False
    
    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Jarvis Test Case Generator"
    VERSION: str = "2.0.2"
    
    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:8003",
        "http://127.0.0.1:8004",
        "http://127.0.0.1:8000",
        "http://127.0.0.1:8001",
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
    
    # Base Directories - Dynamic path resolution
    @property
    def BASE_DIR(self) -> Path:
        """Get the root directory of the project"""
        # Start from current file location and traverse up to find project root
        current_dir = Path(__file__).parent
        # Assuming config.py is in utils/ folder, go up to find project root
        return current_dir.parent.parent.parent
    
    @property
    def BACKEND_TC_GEN_DIR(self) -> Path:
        """Backend test case generation directory"""
        return Path(__file__).parent.parent
    
    # Main Data Directories
    @property
    def ALL_INPUT(self) -> Path:
        return self.BASE_DIR / "ALL_INPUT"
    
    @property
    def ALL_OUTPUT(self) -> Path:
        return self.BASE_DIR / "ALL_OUTPUT"
    
    @property
    def ALL_INTERMEDIATE_STATE_CONFIG(self) -> Path:
        return self.BASE_DIR / "ALL_INTERMEDIATE_STATE_CONFIG"

    # Custom Prompts and YAML Configuration Paths
    @property
    def CUSTOM_PROMPTS_TC(self) -> Path:
        return self.ALL_INTERMEDIATE_STATE_CONFIG / "Custom prompts tuning TC graph" / "Custom prompts for tc"
    
    @property
    def CUSTOM_YAML_TC(self) -> Path:
        return self.ALL_INTERMEDIATE_STATE_CONFIG / "Custom prompts tuning TC graph" / "Custom yaml tc"

    # User Data Paths
    @property
    def USER_DATA_PATH(self) -> Path:
        return self.ALL_INPUT / "User_Data"
    @property
    def USER_PATHS_JSON(self) -> Path:
        return self.ALL_INTERMEDIATE_STATE_CONFIG / "USER_PATHS_JSON" 
    
    @property
    def USER_PATHS_JSON_FILE(self) -> Path:
        return self.USER_PATHS_JSON /  "User_data.json"
    
    @property
    def US_PATH_TO_GENERATE(self) -> Path:
        return self.USER_DATA_PATH / "US_to_generate_folder"
    
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
    def HISTORY_US_PATH(self) -> Path:
        return self.USER_DATA_PATH / "History_User_Stories"
    
    @property
    def HISTORY_TC_PATH(self) -> Path:
        return self.USER_DATA_PATH / "Previous_Test_Cases"
    
    # Output Paths
    # @property
    # def DATAFRAMES_PATH(self) -> Path:
    #     return self.ALL_OUTPUT / "Created_Dataframes"
    
    @property
    def GENERATED_EDGE_FUNCTIONAL_TESTS(self) -> Path:
        return self.GENERATED_OUTPUT_PATH / "Final_Generated_Edge_Functional_Tests"
    
    @property
    def GENERATED_END_TO_END_TESTS(self) -> Path:
        return self.GENERATED_OUTPUT_PATH / "Final_Generated_End_To_End_Tests" 

    @property
    def INTERMEDIARY_FUNC_EDGE_GENERATED_TESTS(self) -> Path:
        return self.ALL_INTERMEDIATE_STATE_CONFIG / "Intermediary_Functional_Edge_Generated_Tests" 
    
    @property
    def PRIORITY_CONFIGURATION(self) -> Path:
        return self.GENERATED_OUTPUT_PATH / "Priority_Configuration" 
    
    @property
    def GRAPHS_FOLDER_PATH(self) -> Path:
        return self.BASE_DIR / "Graphs"
    
    @property
    def GRAPHS_VISUALS_FOLDER_PATH(self) -> Path:
        return self.BASE_DIR / "Created_Graphs"
    
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
    def ARCHIVED_US_TO_GENERATE_FILES_DIRECTORY(self) -> Path:
        return self.ALL_INPUT / "User_Data_Archived" / "Archived_US_to_generate"
    
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
    
    # End-to-End Process Paths
    @property
    def END_TO_END_INTERMEDIARY_FILES(self) -> Path:
        return self.ALL_INTERMEDIATE_STATE_CONFIG / "End_To_End_Intermediary_Files"
    
    @property
    def END_TO_END_INTERMEDIARY_CONVERS_LOGS(self) -> Path:
        return self.END_TO_END_INTERMEDIARY_FILES / "End_To_End_Intermediary_Conversation_Logs"

    @property
    def END_TO_END_INTERMEDIARY_FILES_PHASE_I_AG_CONVERSATION(self) -> Path:
        return self.END_TO_END_INTERMEDIARY_CONVERS_LOGS / "Phase_I_Agents_Conversation"
    
    @property
    def END_TO_END_INTERMEDIARY_FILES_PHASE_II_AG_CONVERSATION(self) -> Path:
        return self.END_TO_END_INTERMEDIARY_CONVERS_LOGS / "Phase_II_Agents_Conversation"
    
    @property
    def END_TO_END_INTERMEDIARY_FILES_TRACE_FILES(self) -> Path:
        return self.END_TO_END_INTERMEDIARY_FILES / "Intermediate_Trace_Files"
    
    @property
    def END_TO_END_INTERMEDIARY_FILES_BLOC_I(self) -> Path:
        return self.END_TO_END_INTERMEDIARY_FILES_TRACE_FILES / "Intermediate_Bloc_I"
    @property
    def END_TO_END_INTERMEDIARY_FILES_BLOC_II(self) -> Path:
        return self.END_TO_END_INTERMEDIARY_FILES_TRACE_FILES / "Intermediate_Bloc_II"
    @property
    def END_TO_END_INTERMEDIARY_FILES_BLOC_III(self) -> Path:
        return self.END_TO_END_INTERMEDIARY_FILES_TRACE_FILES / "Intermediate_Bloc_III"
    
    @property
    def END_TO_END_INTERMEDIARY_CLEAN_FILES(self) -> Path:
        return self.END_TO_END_INTERMEDIARY_FILES / "Intermediate_Clean_Files"

    # Simple Output Directories
    @property
    def GENERATED_OUTPUT_PATH(self) -> Path:
        return self.BASE_DIR / self.ALL_OUTPUT / "Generated_output"
    
    @property
    def INPUT_PATH(self) -> Path:
        return self.BASE_DIR / "Input"
    
    # Graph Configuration Constants
    OUTPUT_FOLDER: str = "input"
    GRAPH_CONTEXT: str = "project_contxt_graph"
    GRAPH_US: str = "us_graph"
    GRAPH_GUIDELINES: str = "guidelines_graph"
    GRAPH_BUSINESS_DOMAIN: str = "business_domain_graph"
    GRAPH_HISTORY_TC: str = "test_cases_history_graph"
    SAVE_OUTPUT_FOLDER: str = "Generated_output"
    ARTIFACTS_GRAPH_VISUALIZER_PATH: str = "graphrag-visualizer/public/artifacts"


    us_output_format: str = '''{
        "User Story Description": "<User Story Description>",
        "Acceptance Criteria": "- Un appui sur le bouton \"Valider\" doit enregistrer les informations saisies. - Un message de confirmation doit s'afficher après l'enregistrement. - Un toggle contenant un \"Done\" icon doit apparaître.",
        "Business Rules": "- Les informations saisies doivent être valides. - Un utilisateur ne peut pas soumettre le formulaire sans avoir rempli tous les champs obligatoires."
        }'''

    output_format_Features_Analyzer : str  = '''
                    [
                        {
                            "Step_Id": 1,
                            "Step_Name": "Login Valide",
                            "Feature": "Feature_id_2",
                            "Step_Status": "Passing"
                        },
                        {
                            "Step_Id": 2,
                            "Step_Name": "Choix Montant invalide",
                            "Feature": "Feature_id_7",
                            "Step_Status": "Non Passing"
                        }
                    ] '''

    output_format_High_Level_Tests_Generator : str = ''' 
    [
        {
            "Test_Title": "Connexion utilisateur",
            "Test_Steps": [
                {"Step_Name": "Login valide", "Step_Features": ["Accès Utilisateur"], "Step_Status": "Passing"},
                {"Step_Name": "ouvrir page profil user", "Step_Features": ["Navigation sur le profil utilisateur"], "Step_Status": "Passing"},
            ]
        },
        {
            "Test_Title": "Connexion utilisateur non passant_Login invalide",
            "Test_Steps": [
                {"Step_Name": "Login invalide", "Step_Features": ["Accès Utilisateur"], "Step_Status": "Non Passing"},
            ]
        },
        {
            "Test_Title": "Connexion utilisateur non passant_Mot de passe invalide",
            "Test_Steps": [
                {"Step_Name": "Login valide", "Step_Features": ["Accès Utilisateur"], "Step_Status": "Passing"},
                {"Step_Name": "Mot de passe invalide", "Step_Features": ["Authentification"], "Step_Status": "Non Passing"}
            ]
        }
    ]
                    '''


    output_format_Refined_Tests_Generator : str  = '''
[
    {
        "Test_Id": 1,
        "Test_Name": "Login Valide",
        "Test_Feature": "Accès Utilisateur",
        "Test_Status": "passing",
        "Detailed_Test_Steps": [
            {"step": "Ouvrir la page de connexion", "Expected_Result": "Page chargée"},
            {"step": "Entrer l'email", "Expected_Result": "Email valide"},
            {"step": "Entrer le mot de passe", "Expected_Result": "Mot de passe valide"},
            {"step": "Cliquer sur le bouton 'Se connecter'", "Expected_Result": "Redirection vers la page d'accueil"}
        ]
    },
    {
        "Test_Id": 2,
        "Test_Name": "Choix Montant invalide",
        "Test_Feature": "Gestion des transactions",
        "Test_Status": "Non Passing",
        "Detailed_Test_Steps": [
            {"step": "Ouvrir la page de retrait", "Expected_Result": "Page chargée"},
            {"step": "Entrer un montant invalide", "Expected_Result": "Message d'erreur affiché"}
        ]
    }
]
        
'''
    output_format_USLinker : str = '''
        [
            {
            'US': 'Debiter compte selon montant ', 
            'relevant_conditions': 'Le montant doit être valide et supérieur à 0. Le montant doit être inférieur au solde du compte.'
            },
            ...
        ]
            '''
   

    # File Upload Settings
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_FILE_EXTENSIONS: List[str] = ['.pdf', '.txt', '.xlsx', '.xls', '.json']

    def create_directories(self):
        """Create necessary directories if they don't exist"""
        directories = [
            # Main directories
            self.ALL_INPUT,
            self.ALL_OUTPUT,
            self.ALL_INTERMEDIATE_STATE_CONFIG,
            
            # User data directories
            self.USER_DATA_PATH,
            self.PROJECT_SPEC_PATH,
            self.BUSINESS_DOMAIN_PATH,
            self.INTERNAL_COMPANY_GUIDELINES_PATH,
            self.CURRENT_US_PATH,
            self.HISTORY_US_PATH,
            self.HISTORY_TC_PATH,
            self.US_PATH_TO_GENERATE,
            
            # Output directories
            # self.DATAFRAMES_PATH,
            self.GENERATED_OUTPUT_PATH,
            self.INPUT_PATH,
            
            # Graph directories
            self.GRAPHS_FOLDER_PATH,
            self.GRAPHS_VISUALS_FOLDER_PATH,
            self.US_GRAPH_PATH,
            self.SPEC_GRAPH_PATH,
            self.GUIDELINES_GRAPH_PATH,
            self.BUSINESS_GRAPH_PATH,
            self.TC_HISTORY_GRAPH_PATH,
            
            # Visual graph directories
            self.US_VISUAL_GRAPH_PATH,
            self.SPEC_VISUAL_GRAPH_PATH,
            self.GUIDELINES_VISUAL_GRAPH_PATH,
            self.BUSINESS_DOMAIN_VISUAL_GRAPH_PATH,
            self.TC_HISTORY_VISUAL_GRAPH_PATH,
            
            # Archive directories
            self.ARCHIVED_HISTORY_TC_FILES_DIRECTORY,
            self.ARCHIVED_PROJECT_SPEC_FILES_DIRECTORY,
            self.ARCHIVED_CURRENT_US_FILES_DIRECTORY,
            self.ARCHIVED_GRAPH_TC_FILES_DIRECTORY,
            self.ARCHIVED_GRAPH_BUSINESS_FILES_DIRECTORY,
            self.ARCHIVED_US_TO_GENERATE_FILES_DIRECTORY,
            
            # Custom configuration directories
            self.CUSTOM_PROMPTS_TC,
            self.CUSTOM_YAML_TC,
            self.END_TO_END_INTERMEDIARY_FILES,
            self.INTERMEDIARY_FUNC_EDGE_GENERATED_TESTS,
            self.USER_PATHS_JSON,
            self.END_TO_END_INTERMEDIARY_FILES_PHASE_I_AG_CONVERSATION,
            self.END_TO_END_INTERMEDIARY_FILES_PHASE_II_AG_CONVERSATION,
            self.END_TO_END_INTERMEDIARY_FILES_TRACE_FILES,
            self.END_TO_END_INTERMEDIARY_CONVERS_LOGS,
            self.END_TO_END_INTERMEDIARY_FILES_BLOC_I,
            self.END_TO_END_INTERMEDIARY_FILES_BLOC_II,
            self.END_TO_END_INTERMEDIARY_FILES_BLOC_III,
            self.END_TO_END_INTERMEDIARY_CLEAN_FILES

        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def print_paths(self):
        """Print key paths for debugging"""
        logger.info(f"BASE_DIR: {self.BASE_DIR}")
        logger.info(f"USER_DATA_PATH: {self.USER_DATA_PATH}")
        logger.info(f"PROJECT_SPEC_PATH: {self.PROJECT_SPEC_PATH}")
        logger.info(f"GRAPHS_FOLDER_PATH: {self.GRAPHS_FOLDER_PATH}")
        logger.info(f"GENERATED_OUTPUT_PATH: {self.GENERATED_OUTPUT_PATH}")
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        env_file_encoding = 'utf-8'


# LLM Configurations
LLM_CONFIGS: Dict[str, Dict[str, Any]] = {
        "gpt4_turbo": {"model": "gpt-4-turbo"},
        "gpt4o_mini": {"model": "gpt-4o-mini"},
        "gpt4o": {"model": "gpt-4o"}
    }

# Output Format Templates
OUTPUT_FORMATS: Dict[str, str] = {
        "Gherkin sans paramètres": '''
    US: Créer mon compte : Authentification à l'application
    Scenario 1 : Cas passant : Authentification réussie
    [Précondition] : Le beneficiaire possède deja un compte
    Etant donné que, le beneficiaire est sur la page d'accueil,
    et il introduit son email correct et son mot de passe correct,
    Lorsque, il clique sur le bouton 'Connexion'
    Alors, il est authentifié correctement et redirigé vers la page Home de son compte.
    ''',
        "Gherkin avec paramètres": '''
    US: Créer mon compte : Authentification à l'application
    Scenario 1 : Cas Passant : Authentification réussie
    Given le Jeu de données de l'<utilisateur>
    AND le beneficiaire possède deja un compte
    AND le beneficiaire est sur la page d'accueil,
    AND il introduit son email <email> et son mot de passe <mdp>,
    WHEN il clique sur le bouton 'Connexion'
    THEN il est authentifié correctement et redirigé vers la page Home de son compte.
    AND le code de retour est <code>
    ''',
        "Format language naturel": '''
    US : Authentification au système
    Scenario 1 : Authentification réussie
    Préconditions : L'utilisateur possède déjà un compte 
    Actions:
    1- Je suis sur la page de login 
    2- J'introduis mon adresse email sous format valide
    3- J'introduis mon mot de passe contenant au moins 8 caractères
    4- Je vois un message de succès d'authentification
    5- Je suis déplacé vers la page Home.
    Résultat attendu : Je suis sur la page Home.
    '''
    }

# Global settings instance
_settings = None

def get_settings() -> Settings:
    """Get global settings instance (singleton pattern)"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings

def setup_directories():
    """Create necessary directories if they don't exist"""
    settings = get_settings()
    settings.create_directories()
    if settings.DEBUG:
        settings.print_paths()

# Create settings instance
settings = get_settings()

# Create directories on import
setup_directories()