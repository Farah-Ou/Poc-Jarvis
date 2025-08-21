
import os
import sys
import shutil
import subprocess
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from dotenv import load_dotenv
from typing_extensions import Annotated
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.tools import AgentTool

from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
from autogen_agentchat.messages import BaseAgentEvent, BaseChatMessage
from autogen_agentchat.teams import SelectorGroupChat
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import OpenAIChatCompletionClient

from src.utils.file_utils import FileService
from src.utils.config import settings
from Backend_TC_Gen.utils.config import settings, LLM_CONFIGS

logger = logging.getLogger(__name__)
model_client = OpenAIChatCompletionClient(model="gpt-4o")

class GraphAgents:
    def __init__(self, custom_settings: Optional[Dict[str, Any]] = None):
        """
        Initialize the FuncEdgeGeneration class with configurations from settings.
        
        Args:
            custom_settings: Optional dictionary to override default settings
        """
        # Set encoding for Python
        os.environ["PYTHONIOENCODING"] = "utf-8"
        
        # Use settings from config
        self.settings = settings
        self.output_folder = settings.OUTPUT_FOLDER
        self.graph_context = settings.GRAPH_CONTEXT
        self.graph_us = settings.GRAPH_US
        self.graph_guidelines = settings.GRAPH_GUIDELINES
        self.graph_business_domain = settings.GRAPH_BUSINESS_DOMAIN
        self.graph_history_tc = settings.GRAPH_HISTORY_TC
        self.EXPERT_ACCOUNTING = settings.EXPERT_ACCOUNTING 
        self.EXPERT_RGAA = settings.EXPERT_RGAA
        self.EXPERT_FINANCE = settings.EXPERT_FINANCE
        self.project_folder_path = str(settings.GRAPHS_FOLDER_PATH)
        
        # LLM configurations from config
        self.llm_configs = LLM_CONFIGS
        self.default_llm_config = {"model": settings.LLM_MODEL_GPT4_TURBO}

        # Apply custom settings if provided
        if custom_settings:
            self._apply_custom_settings(custom_settings)
        
        # Ensure output directories exist
        # self._ensure_output_directories()
        
        logger.info(f"GraphAgents initialized with project path: {self.project_folder_path}")

    def get_llm_config(self, model_name: str = "gpt4_turbo") -> Dict[str, Any]:
        """
        Get LLM configuration by name.
        
        Args:
            model_name: Name of the LLM model configuration
            
        Returns:
            LLM configuration dictionary
        """
        config = self.llm_configs.get(model_name, self.default_llm_config)
        logger.debug(f"Using LLM config: {config}")
        return config
    

    def _apply_custom_settings(self, custom_settings: Dict[str, Any]):
        """Apply custom settings to override defaults."""
        for key, value in custom_settings.items():
            if hasattr(self, key):
                setattr(self, key, value)
                logger.info(f"Custom setting applied: {key} = {value}")

    def run_local_query(self, project_folder_path: Annotated[str, "The folder path where the graph is located"], 
                    graph_name: Annotated[str, "The end folder name where the graph is located"],
                    query_text: Annotated[str, "The Query text"],
                    jira_project_key : Annotated[Optional[str],"Jira Project Key of Target project"]) -> Annotated[str, "The retrieved content from the graph after a local call"]:
        """
        Makes a local call to the GraphRAG graph.
        
        Args:
            project_folder_path: The folder path where the graph is located
            graph_name: The end folder name where the graph is located  
            query_text: The query text
            
        Returns:
            The retrieved content from the graph after a local call
        """
        working_directory = os.path.join(project_folder_path, graph_name, jira_project_key)
        
        # Validate that the graph directory exists
        if not os.path.exists(working_directory):
            error_msg = f"Graph directory does not exist: {working_directory}"
            logger.error(error_msg)
            return f"Error: {error_msg}"
        

        command = [
        'graphrag', 'query',
        '--root', working_directory,
        '--method', 'local',
        '--query', query_text
        ]

        try:
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                encoding='utf-8',
                timeout=300  # 5 minute timeout
            )

            if result.returncode == 0:
                logger.info("Local retrieval success")
                return result.stdout
            else:
                logger.error(f"Local query failed: {result.stderr}")
                return f"Error: {result.stderr}"
        except subprocess.TimeoutExpired:
            logger.error("Local query timed out")
            return "Error: Query timed out"
        except Exception as e:
            logger.error(f"Exception during local query: {str(e)}")
            return f"Error: {str(e)}"

    def run_global_query(self, project_folder_path: Annotated[str, "The folder path where the graph is located"],
                        graph_name: Annotated[str, "The end folder name where the graph is located"],
                        query_text: Annotated[str, "The Query text"],
                        jira_project_key : Annotated[Optional[str],"Jira Project Key of Target project"]) -> Annotated[str, "The retrieved content from the graph after a global call"]:
        """
        Makes a global call to the GraphRAG graph.
        
        Args:
            project_folder_path: The folder path where the graph is located
            graph_name: The end folder name where the graph is located
            query_text: The query text
            
        Returns:
            The retrieved content from the graph after a global call
        """
        working_directory = os.path.join(project_folder_path, graph_name, jira_project_key)
        
        # Validate that the graph directory exists
        if not os.path.exists(working_directory):
            error_msg = f"Graph directory does not exist: {working_directory}"
            logger.error(error_msg)
            return f"Error: {error_msg}"
        
        command = [   
            'graphrag', 'query',
            '--root', working_directory,
            '--method', 'global',
            '--query', query_text
        ]



        try:
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                encoding='utf-8',
                timeout=300  # 5 minute timeout
            )

            if result.returncode == 0:
                logger.info("Global retrieval success")
                return result.stdout
            else:
                logger.error(f"Global query failed: {result.stderr}")
                return f"Error: {result.stderr}"
        except subprocess.TimeoutExpired:
            logger.error("Global query timed out")
            return "Error: Query timed out"
        except Exception as e:
            logger.error(f"Exception during global query: {str(e)}")
            return f"Error: {str(e)}"  


    def define_us_agent(self, jira_project_key, project_folder_path: str = None, enhance_agent_syst_message : Optional[str] = "", query_txt: Optional[str | List[str]] = None) -> AssistantAgent:
        """
        Define the User Story (US) agent for generating test cases.
        
        Args:
            llm_config_name: Name of the LLM configuration to use
        
        Returns:
            A ConversableAgent instance for US generation
        """
        

        if project_folder_path is None:
            project_folder_path = self.project_folder_path
        
        def run_global_query_wrapper(project_folder_path: str, graph_name: str, query_text: str, jira_project_key: str):
            """Wrapper function for the run_global_query method"""
            return self.run_global_query(project_folder_path, graph_name, query_text, jira_project_key)

        def run_local_query_wrapper(project_folder_path: str, graph_name: str, query_text: str, jira_project_key: str):
            """Wrapper function for the run_local_query method"""
            return self.run_local_query(project_folder_path, graph_name, query_text, jira_project_key)
        

        US_Agent = AssistantAgent(
            name="US_Agent",
            description="Agent specialized in User Story (US) generation.",
            model_client=model_client,
            system_message=f'''Tu es un Product Owner connaisseur de la spécification fonctionnelle projet.
            
            Tu as accès à un graphe de connaissances qui contient des spécifications fonctionnelles, des epics, features, et des user stories du projet, règles de gestion et critères d'acceptance.
            Tu établis L'accès à ce graphe à travers des tools calls :  
            
            - run_global_query(project_folder_path, graph_name, query_text,jira_project_key) avec les paramètres suivants: {project_folder_path}, {self.graph_us} , {query_txt}, et {jira_project_key}.
            - run_local_query(project_folder_path, graph_name, query_text,jira_project_key) avec les paramètres suivants: {project_folder_path}, {self.graph_us} , {query_txt} et {jira_project_key}.
            
            Si tu es sollicité par un autre agent, tu vas toujours éxécuter un tool call  pour essayer de répondre aux questions de l'agent.
            Tu reçois un besoin qu'on souhaite connaitre à propos de l'aspect fonctionnel du projet. Le besoin est exprimé sous forme de 'query_text' {query_txt}, Cette query que tu reçois, sera utilisé dans tes tools calls pour extraire les informations nécessaires du graphe.
            Les informations que tu retournes doivent être très détaillées et réelles, pas de choses vagues ou inventées.
            Si query_text est vide, tu dois demander à l'agent en question de te communiquer des questions concises à propos du projet.
            Si query est une liste de plusieurs questions, tu réponds à chacune d'elles en faisant appel aux run_local_query_wrapper et run_global_query_wrapper et tu sauvegarde le résultat de chaque tool call dans 2 variables : Global_qs_i, Local_qs_i pour chaque question d'ordre i.
            Finalement, tu reournes les réponses à toutes les question sous ce format: 
            
            Qs 1 : Comment se fait la validation du login ?
            - Local_qs_1 : Pour valider le login, il faut effectuer une validation à deux étapes, en utilisant un token variable.
            - Global_qs_1 : Pour valider le login, il faut utiliser un compte microsoft interne à l'organisme.

            Qs 2 : Comment se fait la validation du montant demandé pour débiter un compte ?
            - Local_qs_2 : Pour valider le montant demandé, il faut vérifier qu'il est inférieur au solde du compte.
            - Global_qs_2 : Pour valider le montant demandé, il faut utiliser un service de validation externe.
            
            {enhance_agent_syst_message}
            ''',
            tools=[run_global_query_wrapper, run_local_query_wrapper]
            )
 
        return US_Agent
    
    def define_project_context_agent(self, jira_project_key, project_folder_path: str = None, enhance_agent_syst_message : Optional[str] = "", query_txt: Optional[str | List[str]] = None) -> AssistantAgent:
        """
        Define the User Story (US) agent for generating test cases.
        
        Args:
            llm_config_name: Name of the LLM configuration to use
        
        Returns:
            A ConversableAgent instance for US generation
        """
        

        if project_folder_path is None:
            project_folder_path = self.project_folder_path
        
        def run_global_query_wrapper(project_folder_path: str, graph_name: str, query_text: str, jira_project_key: str):
            """Wrapper function for the run_global_query method"""
            return self.run_global_query(project_folder_path, graph_name, query_text, jira_project_key)

        def run_local_query_wrapper(project_folder_path: str, graph_name: str, query_text: str, jira_project_key: str):
            """Wrapper function for the run_local_query method"""
            return self.run_local_query(project_folder_path, graph_name, query_text, jira_project_key)
        
        project_Context_Agent = AssistantAgent(
            name="project_Context_Agent",
            description="Agent specialized in the project context.",
            model_client=model_client,
            system_message=f'''Tu es un Product Owner connaisseur du contexte du projet.
            
            Tu as accès à un graphe de connaissances qui contient des connaissances concernant le contexte général du projet. Il peut aussi contenir des abbréviations utilisés dans le projet.
            Les informations que tu retournes doivent être très détaillées et réelles, pas de choses vagues ou inventées..
            Tu établis L'accès à ce graphe à travers des tools calls :  
            
            - run_global_query(project_folder_path, graph_name, query_text,jira_project_key) avec les paramètres suivants: {project_folder_path}, {self.graph_us} , {query_txt}, et {jira_project_key}.
            - run_local_query(project_folder_path, graph_name, query_text,jira_project_key) avec les paramètres suivants: {project_folder_path}, {self.graph_us} , {query_txt} et {jira_project_key}.
            
            Si tu es sollicité par un autre agent, tu vas toujours éxécuter un tool call  pour essayer de répondre aux questions de l'agent.
            Tu reçois un besoin qu'on souhaite connaitre à propos de l'aspect fonctionnel du projet. Le besoin est exprimé sous forme de 'query_text' {query_txt}, Cette query que tu reçois, sera utilisé dans tes tools calls pour extraire les informations nécessaires du graphe.
            Les informations que tu retournes doivent être très détaillées et réelles, pas de choses vagues ou inventées.
            Si query_text est vide, tu dois demander à l'agent en question de te communiquer des questions concises à propos du projet.
            Si query est une liste de plusieurs questions, tu réponds à chacune d'elles en faisant appel aux run_local_query_wrapper et run_global_query_wrapper et tu sauvegarde le résultat de chaque tool call dans 2 variables : Global_qs_i, Local_qs_i pour chaque question d'ordre i.
            Finalement, tu reournes les réponses à toutes les question sous ce format: 
            
            Qs 1 : Qu'est ce qu'un fichier cinématique ?
            - Local_qs_1 : un fichier cinématique contient les noms des paramètres de l'application ainsi que les détails qui les concernent.
            - Global_qs_1 : un fichier cinématique contient les noms des paramètres de l'application, leurs codes, leurs descriptions, tous les détails.
            
            {enhance_agent_syst_message}
            ''',
            tools=[run_global_query_wrapper, run_local_query_wrapper]
            )
 
        return project_Context_Agent
    

    def define_TC_History_agent(self, jira_project_key, project_folder_path: str = None, enhance_agent_syst_message : Optional[str] = "", query_txt: Optional[str | List[str]] = None) -> AssistantAgent:
        """
        Define the User Story (US) agent for generating test cases.
        
        Args:
            llm_config_name: Name of the LLM configuration to use
        
        Returns:
            A ConversableAgent instance for US generation
        """
        

        if project_folder_path is None:
            project_folder_path = self.project_folder_path
        
        def run_global_query_wrapper(project_folder_path: str, graph_name: str, query_text: str, jira_project_key: str):
            """Wrapper function for the run_global_query method"""
            return self.run_global_query(project_folder_path, graph_name, query_text, jira_project_key)

        def run_local_query_wrapper(project_folder_path: str, graph_name: str, query_text: str, jira_project_key: str):
            """Wrapper function for the run_local_query method"""
            return self.run_local_query(project_folder_path, graph_name, query_text, jira_project_key)
        

        history_tc_Agent = AssistantAgent(
            name="history_tc_Agent",
            description="Agent specialized in historical test cases.",  
            model_client=model_client,
            system_message=f'''Tu es un QA connaisseur de l'historique des tests du projet.
            
            Tu as accès à un graphe de connaissances qui contient tout l'historique de Tests du projet au format Gherkin.
            Tu établis L'accès à ce graphe à travers des tools calls :  
            
            - run_global_query(project_folder_path, graph_name, query_text,jira_project_key) avec les paramètres suivants: {project_folder_path}, {self.graph_us} , {query_txt}, et {jira_project_key}.
            - run_local_query(project_folder_path, graph_name, query_text,jira_project_key) avec les paramètres suivants: {project_folder_path}, {self.graph_us} , {query_txt} et {jira_project_key}.
            
            Si tu es sollicité par un autre agent, tu vas toujours éxécuter un tool call pour essayer de répondre aux questions de l'agent.
            Ton role principale est d'extraire du graphe un ou plusieurs test case Gherkin, en son écriture intégrale avec les paramètres et les étapes, à base du titre d'un test ou de mots clés qui reflètent un test donné.

            
            Tu reçois le titre d'un cas de test, ou des mots clés indiquants des caractéristiques d'un test à retourner (Login invalide, redirection page user valide...). 
            Le besoin est exprimé sous forme de 'query_text' {query_txt}, Cette query que tu reçois, sera utilisée dans tes tools calls pour extraire les informations nécessaires du graphe.
            Les informations que tu retournes doivent être très détaillées et réelles, pas de choses vagues ou inventées.
            Si query_text est vide, tu dois demander à l'agent en question de te communiquer un titre ou des indications précises du test à retourner.
            Si query est une liste de plusieurs questions, tu réponds à chacune d'elles en faisant appel aux run_local_query_wrapper et run_global_query_wrapper et tu sauvegarde le résultat de chaque tool call dans 2 variables : Global_query_i, Local_query_i pour chaque requete d'ordre i.
            Finalement, tu reournes les réponses à toutes les question sous ce format:

            Qs 1 : Login Utilisateur valide
            - Global_query_1 : 
            Given Je suis sur la page de Login
            When Je saisis mes identifiants
            Then Je devrais être redirigé vers la page d'accueil
            - Local_query_1 : 
            Given Je suis sur la page de Login
            When Je saisis mon adresse email
            And Je saisis mon mot de passe
            And J'effectue la double authentification
            And Je clique sur le bouton de connexion
            Then Je devrais être redirigé vers la page d'accueil

            Qs 2 : Ajout de Transaction
            - Global_query_2 : 
            Given Je suis sur la page d'ajout de transaction
            When Je saisis le montant de la transaction
            Then Je devrais voir un message de confirmation
            - Local_query_2 : 
            Given Je suis sur la page d'ajout de transaction
            When Je saisis le montant de la transaction
            And Je sélectionne le compte à débiter
            And Je clique sur le bouton de validation
            Then Je devrais voir un message de confirmation

            {enhance_agent_syst_message}
            ''',
            tools=[run_global_query_wrapper, run_local_query_wrapper]
            )
 
        return history_tc_Agent

    def define_all_graph_agents(self, jira_project_key,
                                graph_US: str = None, graph_context: str = None,
                                    project_folder_path: Optional[str] = None,
                                    FUNC_EDGE_message: bool ="False"
                                    
                                    ) -> Tuple:
        """
        Define the prompt generation module with various AutoGen agents.
        
        Args:
            
            
        Returns:
            Tuple of all defined agents
        """

        # Set defaults from config
        if graph_US is None:
            graph_US = self.graph_us
        if graph_context is None:
            graph_context = self.graph_context
        if project_folder_path is None:
            project_folder_path = self.project_folder_path


        def run_global_query_wrapper(project_folder_path: str, graph_name: str, query_text: str, jira_project_key : Optional[str]):
            """Wrapper function for the run_global_query method"""
            return self.run_global_query(project_folder_path, graph_name, query_text, jira_project_key)

        def run_local_query_wrapper(project_folder_path: str, graph_name: str, query_text: str, jira_project_key : Optional[str]):
            """Wrapper function for the run_local_query method"""
            return self.run_local_query(project_folder_path, graph_name, query_text, jira_project_key)


        enhanced_RGAA_Edge = ""
        enhanced_IFRS_Edge = ""
        enhanced_FR_Accounting_Edge = ""
        enhanced_Guidelines_Edge = ""
        enhanced_Business_Domain_Edge = ""
            
        if FUNC_EDGE_message == True:
            msgs_dict = self.create_custom_templates_per_task(project_folder_path)

            if msgs_dict:
                enhanced_RGAA_Edge = msgs_dict.get("RGAA", {}).get("FUNC_EDGE_message")
                enhanced_IFRS_Edge = msgs_dict.get("IFRS", {}).get("FUNC_EDGE_message")
                enhanced_FR_Accounting_Edge = msgs_dict.get("FR_Accounting", {}).get("FUNC_EDGE_message")
                enhanced_Guidelines_Edge = msgs_dict.get("Guidelines", {}).get("FUNC_EDGE_message")
                enhanced_Business_Domain_Edge = msgs_dict.get("Business_Domain", {}).get("FUNC_EDGE_message")
           


        RGAA_Agent = AssistantAgent(
            name="RGAA_Agent",
            description="Agent specialized in RGAA accessibility rules.",
            model_client=model_client,
            system_message=f'''Tu es un Agent connaisseur des Règles Générales d'Accessibilité pour les Administrations (RGAA).
            Tu fais appel à l'outil run_global_query(project_folder_path, graph_name, query_text) avec les paramètres suivants: {project_folder_path}, {self.EXPERT_RGAA}.
            Ce tool call te permet d'avoir accès à un graphe de connaissances qui contient des règles d'accessibilité.
            Tu récurpères les règles nécessaires selon la référence normative RGAA, et tu effectues les étapes suivantes : 
            Les informations que tu retournes doivent être très détaillées et réelles, pas de choses vagues ou inventées.
            {enhanced_RGAA_Edge}
            ''',
            tools=[run_global_query_wrapper, run_local_query_wrapper]
           
            )
        
        Finance_Agent = AssistantAgent(
            name="Finance_Agent",
            description="Agent specialized in finance rules according to IFRS.",
            model_client=model_client,
            system_message=f'''Tu es un Agent connaisseur des Règles de finance selon l'IFRS.
            Tu fais appel à l'outil run_global_query(project_folder_path, graph_name, query_text) avec les paramètres suivants: {project_folder_path}, {self.EXPERT_FINANCE}.
            Ce tool call te permet d'avoir accès à un graphe de connaissances qui contient des règles de l'IFRS.
            Tu récurpères les règles nécessaires selon la référence normative IFRS, et tu effectues les étapes suivantes : 
            Les informations que tu retournes doivent être très détaillées et réelles, pas de choses vagues ou inventées.
            {enhanced_IFRS_Edge}
            ''',
            tools=[run_global_query_wrapper, run_local_query_wrapper]
           
            )
        
        
        FR_Accounting_Agent = AssistantAgent(
            name="FR_Accounting_Agent",
            description="Agent specialized in French accounting rules.",
            model_client=model_client,
            system_message=f'''Tu es un Agent connaisseur des Règles de comptabilité de France selon la norme comptable de France.
            Tu fais appel à l'outil run_global_query(project_folder_path, graph_name, query_text) avec les paramètres suivants: {project_folder_path}, {self.EXPERT_ACCOUNTING}.
            Ce tool call te permet d'avoir accès à un graphe de connaissances qui contient des règles de la norme comptable de France.
            Tu récurpères les règles nécessaires selon la référence normative de comptabilité française, et tu effectues les étapes suivantes : 
            
            Les informations que tu retournes doivent être très détaillées et réelles, pas de choses vagues ou inventées.
            {enhanced_FR_Accounting_Edge}
            ''',
            tools=[run_global_query_wrapper, run_local_query_wrapper]
           
            )
        

        guidelines_Agent = AssistantAgent(
            name="guidelines_Agent",
            description="Agent specialized in internal guidelines and directives.",
            model_client=model_client,
            system_message=f'''Tu es un  connaisseur des règlementations internes de l'organisme.
            Tu fais appel à l'outil run_global_query(project_folder_path, graph_name, query_text, jira_project_key) avec les paramètres suivants: {project_folder_path}, {self.graph_guidelines} et {jira_project_key}.
            Ce tool call te permet d'avoir accès à un graphe de connaissances qui contient des directives et guidelines internes de l'entreprise : politique qualité, système de management de la qualité, RSE, ou tout autre domaine figurant  dans le graphe.
            Les informations que tu retournes doivent être très détaillées et réelles, pas de choses vagues ou inventées.
            {enhanced_Guidelines_Edge}
            ''',
            tools=[run_global_query_wrapper, run_local_query_wrapper]
            
            )
        
        business_domain_Agent = AssistantAgent(
            name="business_domain_Agent",
            description="Agent specialized in the business domain of the project.",
            model_client=model_client,
            system_message=f'''Tu es un Expert Métier connaisseur du domaine métier du projet.
            Tu fais appel à l'outil run_global_query(project_folder_path, graph_name, query_text, jira_project_key) avec les paramètres suivants: {project_folder_path}, {self.graph_business_domain} et {jira_project_key}.
            Ce tool call te permet d'avoir accès à un graphe de connaissances qui contient des connaissances concernant le domaine métier du projet (énergétique, environnemental, système de rails, etc.) Il peut aussi contenir des abbréviations utilisés dans le projet.
            Les informations que tu retournes doivent être très détaillées et réelles, pas de choses vagues ou inventées.
            {enhanced_Business_Domain_Edge}
            ''',
            tools=[run_global_query_wrapper, run_local_query_wrapper]
            )


        logger.info("Experts Agents defined successfully")
        return RGAA_Agent, Finance_Agent, FR_Accounting_Agent, guidelines_Agent, business_domain_Agent
    


    
    def create_custom_templates_per_task(self, jira_project_key, project_folder_path: str, US: str="") -> Dict[str, str]:
        FR_Accounting_FUNC_EDGE_message = f''' 1. Tu récupères le contenu de l'US (User Story) {US} et des Règles de Gestion et tu essayes de formuler des questions (queries) au graphe de l'IFRS.
            2. Tu sauvegrades les queries formulées dans une variable 'queries' dans ta mémoire.
            3. Tu extrait les règles de l'IFRS en relation avec le projet, en faisant appel à l'outil run_global_query(project_folder_path, graph_name, query_text)
            avec les paramètres suivants: {project_folder_path} et {self.EXPERT_ACCOUNTING}. La variable query_text prendra la liste des queries formulées et sauvegardés dans la variable 'queries'.
             4. Tu enregistre l'ensemble des retours du graphe pour chaque query dans une variable RESULTAT_FINANCE_1, qui contient un ensemble de couples : [Query: Règles d'IFRS applicables extraites ]
             5. Finalement, tu executes l'outil run_global_query(project_folder_path, graph_name, query_text,jira_project_key) avec 
           {project_folder_path}, {self.EXPERT_ACCOUNTING} et query :"""Quelles sont les règles de l'IFRS applicables pour cet User Story {US} ?"""
            6. Tu enregistres le contenu retourné par la fonction dans une variable RESULTAT_FINANCE_2.
            7. Tu synthétises le contenu retourné par RESULTAT_FINANCE_1 et RESULTAT_FINANCE_2, et tu le formates de manière à ce qu'il soit clair et concis.
            8. Tu retournes le contenu final synthétisé et formaté, qui contient les règles de finance pertinentes pour l'US et les RG.'''
        
        IFRS_FUNC_EDGE_message = f''' 1. Tu récupère le contenu de l'US (User Story) {US} et des Règles de Gestion et tu essayes de formuler des questions (queries) au graphe de l'IFRS.
            2. Tu sauvegrade les queries formulées dans une variable 'queries' dans ta mémoire.
            3. Tu extrait les règles de l'IFRS en relation avec le projet, en faisant appel à l'outil run_global_query(project_folder_path, graph_name, query_text, jira_project_key)
            avec les paramètres suivants: {project_folder_path} et {self.EXPERT_FINANCE}. La variable query_text prendra la liste des queries formulées et sauvegardés dans la variable 'queries'.
            4. Tu enregistre l'ensemble des retours du graphe pour chaque query dans une variable RESULTAT_FINANCE_1, qui contient un ensemble de couples : [Query: Règles d'IFRS applicables extraites ]
            5. Finalement, tu executes l'outil run_global_query(project_folder_path, graph_name, query_text, jira_project_key) avec
           {project_folder_path}, {self.EXPERT_FINANCE} et query :"""Quelles sont les règles de l'IFRS applicables pour cet User Story {US} ?"""
           6. Tu enregistres le contenu retourné par la fonction dans une variable RESULTAT_FINANCE_2.
           7. Tu synthétises le contenu retourné par RESULTAT_FINANCE_1 et RESULTAT_FINANCE_2, et tu le formates de manière à ce qu'il soit clair et concis.
           8. Tu retournes le contenu final synthétisé et formaté, qui contient les règles de finance pertinentes pour l'US et les RG.'''
            
        RGAA_FUNC_EDGE_message = f''' 1. Tu récupères le contenu de l'US (User Story) {US} et des Règles de Gestion et tu essayes de formuler des questions (queries) au graphe de l'RGAA.
            2. Tu sauvegrade les queries formulées dans une variable 'queries' dans ta mémoire.
            3. Tu extrait les règles d'accessibilité en relation avec le projet, en faisant appel à l'outil run_global_query(project_folder_path, graph_name, query_text,jira_project_key)
            avec les paramètres suivants: {project_folder_path} et {self.EXPERT_RGAA}. La variable query_text prendra La liste des queries formulées et sauvegardés dans la variable 'queries'.
            4. Tu enregistre l'ensemble des retours du graphe pour chaque query dans une variable RESULTAT_RGAA_1, qui contient : [Query: Règles d'RGAA applicables extraites ]
            5. Finalement, tu executes l'outil run_global_query(project_folder_path, graph_name, query_text,jira_project_key) avec
           {project_folder_path}, {self.EXPERT_RGAA} et query :"""Quelles sont les règles d'accessibilité applicables pour cet User Story {US} ?"""
            6. Tu enregistres le contenu retourné par la fonction dans une variable RESULTAT_RGAA_2."
            7. Tu synthétises le contenu retourné par RESULTAT_RGAA_1 et RESULTAT_RGAA_2, et tu le formates de manière à ce qu'il soit clair et concis.
            8. Tu retournes le contenu final synthétisé et formaté, qui contient les règles d'accessibilité pertinentes pour l'US et les RG.'''

        guidelines_FUNC_EDGE_message = f''' 1. Tu récupères le contenu de l'US (User Story) {US} et des Règles de Gestion et tu essayes de formuler des questions (queries) au graphe des règles internes de l'organisme (norme qualité, norme RSE, sécurité, etc.).
            2. Tu sauvegrades les queries formulées dans une variable 'queries' dans ta mémoire.
            3. Tu extrait les règles de conformité en relation avec le projet, en faisant appel à l'outil run_global_query(project_folder_path, graph_name, query_text, jira_project_key)
            avec les paramètres suivants: {project_folder_path} et {self.graph_guidelines}. La variable query_text prendra la liste des queries formulées et sauvegardés dans la variable 'queries'.
            4. Tu enregistre l'ensemble des retours du graphe pour chaque query dans une variable RESULTAT_Guidelines_1, qui contient un ensemble de couples : [Query: Règles de conformité applicables extraites ]
            5. Finalement, tu executes l'outil run_global_query(project_folder_path, graph_name, query_text, jira_project_key) avec
           {jira_project_key}, {project_folder_path}, {self.graph_guidelines} et query :"""Quelles sont les règles de l'IFRS applicables pour cet User Story {US} ?"""
            6. Tu enregistres le contenu retourné par la fonction dans une variable RESULTAT_Guidelines_2.
            7. Tu synthétises le contenu retourné par RESULTAT_Guidelines_1 et RESULTAT_Guidelines_2, et tu le formates de manière à ce qu'il soit clair et concis.
            8. Tu retournes le contenu final synthétisé et formaté, qui contient les règles pertinentes pour l'US et les RG.'''

        business_domain_FUNC_EDGE_message = f''' 1. Tu récupère le contenu de l'US (User Story) {US} et des Règles de Gestion et tu essayes de formuler des questions (queries) au graphe du domaine métier de l'organisme.
            2. Tu sauvegrades les queries formulées dans une variable 'queries' dans ta mémoire.
            3. Tu extrait les règles de conformité au domaine métier en relation avec le projet, en faisant appel à l'outil run_global_query(project_folder_path, graph_name, query_text, jira_project_key)
            avec les paramètres suivants: {project_folder_path} et {self.graph_business_domain}. La variable query_text prendra La liste des queries formulées et sauvegardés dans la variable 'queries'.
            4. Tu enregistres l'ensemble des retours du graphe pour chaque query dans une variable RESULTAT_BUSINESS_1, qui contient : [Query: Règles de conformité au domaine métier applicables extraites ]
            5. Finalement, tu executes l'outil run_global_query(project_folder_path, graph_name, query_text, jira_project_key) avec
           {jira_project_key}, {project_folder_path}, {self.graph_business_domain} et query :"""Quelles sont les règles de conformité au domaine métier applicables pour cet User Story {US} ?"""
            6. Tu enregistres le contenu retourné par la fonction dans une variable RESULTAT_BUSINESS_2.
            7. Tu synthétises le contenu retourné par RESULTAT_BUSINESS_1 et RESULTAT_BUSINESS_2, et tu le formates de manière à ce qu'il soit clair et concis.
            8. Tu retournes le contenu final synthétisé et formaté, qui contient les règles pertinentes pour l'US et les RG.'''

        agents_query_templates = {
            "RGAA": {'FUNC_EDGE_message': RGAA_FUNC_EDGE_message},
            "IFRS": {'FUNC_EDGE_message': IFRS_FUNC_EDGE_message},
            "FR_Accounting": {'FUNC_EDGE_message': FR_Accounting_FUNC_EDGE_message},
            "Business_Domain": {'FUNC_EDGE_message': business_domain_FUNC_EDGE_message},
            "Guidelines": {'FUNC_EDGE_message': guidelines_FUNC_EDGE_message}
        }

        return agents_query_templates
    