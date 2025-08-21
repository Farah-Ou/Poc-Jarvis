import os
import logging
import json
import asyncio
import asyncio

from typing_extensions import Annotated
# from pathlib import Path
from typing import Dict, Any, Tuple, Optional, Sequence, List 
from Backend_TC_Gen.utils.config import settings, LLM_CONFIGS, OUTPUT_FORMATS
from Backend_TC_Gen.utils.files_utils import FilesGraphs
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_core.tools import FunctionTool
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import BaseAgentEvent, BaseChatMessage
from autogen_agentchat.teams import SelectorGroupChat


from autogen_ext.models.openai import OpenAIChatCompletionClient


from datetime import datetime
from src.utils.graph_agents import GraphAgents

# ---------------------------------------
import pandas as pd
import glob
from fastapi import APIRouter
from Backend_TC_Gen.models.state import get_processing_state
from src.utils.user_data import UserDataManager


from src.utils.file_utils import FileService
from src.utils.jira_utils import  JiraService 



logger = logging.getLogger(__name__)
# router = APIRouter(prefix="/edge_functional_tests")
router = APIRouter()    
# settings = get_settings()

user_data_manager = UserDataManager()
# user_paths = user_data_manager._load_data(us_user_id)

jira_service = JiraService()
file_service = FileService()


# ------------------------


Graph_Agents = GraphAgents()
file_graphs = FilesGraphs()

logger = logging.getLogger(__name__)

class FuncEdgeGeneration:
    """
    A class for generating test cases using AutoGen agents and GraphRAG queries.
    Handles prompt generation, context retrieval, and test case generation with reflection.
    """
    
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
        self.project_folder_path = settings.GRAPHS_FOLDER_PATH
        self.project_folder_path = settings.GRAPHS_FOLDER_PATH
        
        # LLM configurations from config
        self.llm_configs = LLM_CONFIGS
        self.default_llm_config = {"model": settings.LLM_MODEL_GPT4_TURBO}

        self.model_client = OpenAIChatCompletionClient(model="gpt-4o", config={"log_usage": True})
        self.model_client_REASONING_3_MINI = OpenAIChatCompletionClient(model="o3-mini", config={"log_usage": True})
        self.model_client_REASONING_4_MINI = OpenAIChatCompletionClient(model="gpt-4o-mini-2024-07-18", config={"log_usage": True})
        
        # Output formats from config
        self.output_formats = OUTPUT_FORMATS

        # Call graph_Agents
        # RGAA_Agent, Finance_Agent, FR_Accounting_Agent, guidelines_Agent, business_domain_Agent = Graph_Agents.define_all_graph_agents( 
        #     jira_project_key, project_folder_path=self.project_folder_path
        # )

        # history_tc_Agent = Graph_Agents.define_TC_History_agent(
        #     jira_project_key, project_folder_path=self.project_folder_path
        # )

        # project_Context_Agent = Graph_Agents.define_project_context_agent(
        #     jira_project_key, project_folder_path=self.project_folder_path
        # )

        # RGAA_Agent, Finance_Agent, FR_Accounting_Agent, guidelines_Agent, business_domain_Agent = Graph_Agents.define_all_graph_agents( 
        #     jira_project_key, project_folder_path=self.project_folder_path
        # )

        # history_tc_Agent = Graph_Agents.define_TC_History_agent(
        #     jira_project_key, project_folder_path=self.project_folder_path
        # )

        # project_Context_Agent = Graph_Agents.define_project_context_agent(
        #     jira_project_key, project_folder_path=self.project_folder_path
        # )


        # self.RGAA_Agent = RGAA_Agent
        # self.Finance_Agent = Finance_Agent      
        # self.FR_Accounting_Agent = FR_Accounting_Agent
        # self.history_tc_Agent = history_tc_Agent
        # self.RGAA_Agent = RGAA_Agent
        # self.Finance_Agent = Finance_Agent      
        # self.FR_Accounting_Agent = FR_Accounting_Agent
        # self.history_tc_Agent = history_tc_Agent
        
        # self.guidelines_Agent = guidelines_Agent
        # self.business_domain_Agent = business_domain_Agent
        # self.project_Context_Agent = project_Context_Agent
        # self.guidelines_Agent = guidelines_Agent
        # self.business_domain_Agent = business_domain_Agent
        # self.project_Context_Agent = project_Context_Agent
        
        # Default test case generation message
        self.tc_gen_msg = '''Tu es un générateur de Cas de Test en Gherkin. Etant donné un User Story, génère les cas de Test qui lui sont associés en tenant 
compte surtout de ses critères d'accpetance, ainsi que des informations pertinentes liées au projet. Fait attention surtout aux règles à respecter pour 
une fonctionnalité donnée qui proviennent d'une autre US mais qui est liée. \n '''
        
        # Apply custom settings if provided
        if custom_settings:
            self._apply_custom_settings(custom_settings)
        
        # Ensure output directories exist
        self._ensure_output_directories()
        
        logger.info(f"FuncEdgeGeneration initialized with project path: {self.project_folder_path}")

    def _apply_custom_settings(self, custom_settings: Dict[str, Any]):
        """Apply custom settings to override defaults."""
        for key, value in custom_settings.items():
            if hasattr(self, key):
                setattr(self, key, value)
                logger.info(f"Custom setting applied: {key} = {value}")

    def _ensure_output_directories(self):
        """Ensure all necessary output directories exist."""
        directories = [
            self.settings.INTERMEDIARY_FUNC_EDGE_GENERATED_TESTS,
            self.settings.GENERATED_EDGE_FUNCTIONAL_TESTS,
       
       
            self.settings.END_TO_END_INTERMEDIARY_FILES
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
        
        logger.info("Output directories ensured")

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

    def get_output_format(self, format_name: str = "Gherkin sans paramètres") -> str:
        """
        Get output format template by name.
        
        Args:
            format_name: Name of the output format
            
        Returns:
            Output format template string
        """
        format_template = self.output_formats.get(format_name, self.output_formats["Gherkin sans paramètres"])
        logger.debug(f"Using output format: {format_name}")
        return format_template

    def save_conversation_logs(
        self,
        collected_messages: List[Any],
        step_name: str,
        output_directory: str,
        include_tool_calls: bool = True,
        file_prefix: str = "conversation_log"
    ) -> tuple[str, str]:
        """
        Save conversation logs to both TXT and JSON files with detailed message information.
        
        Args:
            collected_messages: List of message objects from the conversation stream
            step_name: Name of the conversation step/phase
            output_directory: Directory to save the log files
            include_tool_calls: Whether to include tool call information
            file_prefix: Prefix for the output filenames
        
        Returns:
            tuple: (txt_filepath, json_filepath) - paths to the created files
        """
        
        # Create output directory if it doesn't exist
        os.makedirs(output_directory, exist_ok=True)
        
        # Generate timestamp for unique filenames
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_step_name = step_name.replace(' ', '_').replace('/', '_').replace('\\', '_')
        
        # Define output file paths
        txt_filename = f"{file_prefix}_{safe_step_name}_{timestamp}.txt"
        json_filename = f"{file_prefix}_{safe_step_name}_{timestamp}.json"
        txt_filepath = os.path.join(output_directory, txt_filename)
        json_filepath = os.path.join(output_directory, json_filename)
        
        # Process messages and extract information
        processed_messages = []
        agent_groups = {}
        
        for i, message in enumerate(collected_messages):
            message_data = {
                'index': i,
                'timestamp': datetime.now().isoformat(),
                'source': None,
                'content': None,
                'message_type': str(type(message).__name__),
                'tool_calls': [],
                'raw_attributes': {}
            }
            
            # Extract source/agent name
            if hasattr(message, 'source'):
                message_data['source'] = str(message.source)
                
                # Group messages by agent
                agent_name = message_data['source']
                if agent_name not in agent_groups:
                    agent_groups[agent_name] = []
                agent_groups[agent_name].append(message_data)
            
            # Extract content
            if hasattr(message, 'content'):
                try:
                    if isinstance(message.content, str):
                        message_data['content'] = message.content
                    else:
                        message_data['content'] = str(message.content)
                except Exception as e:
                    message_data['content'] = f"[Error extracting content: {e}]"
                    logger.warning(f"Error extracting content from message {i}: {e}")
            
            # Extract tool calls if present and requested
            if include_tool_calls:
                tool_call_attrs = ['tool_calls', 'function_calls', 'tools_used', 'actions']
                for attr in tool_call_attrs:
                    if hasattr(message, attr):
                        try:
                            tool_data = getattr(message, attr)
                            if tool_data:
                                message_data['tool_calls'].append({
                                    'attribute': attr,
                                    'data': str(tool_data) if not isinstance(tool_data, (dict, list)) else tool_data
                                })
                        except Exception as e:
                            logger.warning(f"Error extracting tool calls from message {i}: {e}")
            
            # Store other relevant attributes
            relevant_attrs = ['role', 'name', 'function_call', 'tool_call_id', 'metadata']
            for attr in relevant_attrs:
                if hasattr(message, attr):
                    try:
                        value = getattr(message, attr)
                        message_data['raw_attributes'][attr] = str(value) if not isinstance(value, (dict, list, str, int, float, bool)) else value
                    except Exception as e:
                        logger.warning(f"Error extracting attribute {attr} from message {i}: {e}")
            
            processed_messages.append(message_data)
        
        # Save to TXT file
        try:
            with open(txt_filepath, "w", encoding="utf-8") as f:
                f.write(f"CONVERSATION LOG - {step_name}\n")
                f.write(f"Generated: {datetime.now().isoformat()}\n")
                f.write(f"Total Messages: {len(collected_messages)}\n")
                f.write("=" * 80 + "\n\n")
                
                # Write messages grouped by agent
                for agent_name, messages in agent_groups.items():
                    f.write(f"=== {agent_name} Messages ({len(messages)} total) ===\n\n")
                    
                    for msg in messages:
                        f.write(f"[Message {msg['index']}] {agent_name}\n")
                        f.write(f"Type: {msg['message_type']}\n")
                        f.write(f"Timestamp: {msg['timestamp']}\n")
                        
                        if msg['content']:
                            f.write(f"Content:\n{msg['content']}\n")
                        
                        if msg['tool_calls']:
                            f.write("Tool Calls:\n")
                            for tool_call in msg['tool_calls']:
                                f.write(f"  - {tool_call['attribute']}: {tool_call['data']}\n")
                        
                        if msg['raw_attributes']:
                            f.write("Additional Attributes:\n")
                            for attr, value in msg['raw_attributes'].items():
                                f.write(f"  - {attr}: {value}\n")
                        
                        f.write("-" * 40 + "\n\n")
                
                # Write chronological view
                f.write("\n\n=== CHRONOLOGICAL VIEW ===\n\n")
                for msg in processed_messages:
                    source = msg['source'] or 'Unknown'
                    content_preview = (msg['content'][:200] + "...") if msg['content'] and len(msg['content']) > 200 else msg['content']
                    f.write(f"[{msg['index']}] {source}: {content_preview}\n")
                    if msg['tool_calls']:
                        f.write(f"    Tool Calls: {len(msg['tool_calls'])} detected\n")
                    f.write("\n")
            
            logger.info(f"TXT conversation log saved to: {txt_filepath}")
            
        except Exception as e:
            logger.error(f"Error saving TXT log: {e}")
            raise
        
        # Save to JSON file
        try:
            json_data = {
                'metadata': {
                    'step_name': step_name,
                    'generated_at': datetime.now().isoformat(),
                    'total_messages': len(collected_messages),
                    'agents': list(agent_groups.keys()),
                    'message_types': list(set(msg['message_type'] for msg in processed_messages))
                },
                'messages': processed_messages,
                'agent_groups': {
                    agent: [msg['index'] for msg in messages] 
                    for agent, messages in agent_groups.items()
                }
            }
            
            with open(json_filepath, "w", encoding="utf-8") as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"JSON conversation log saved to: {json_filepath}")
            
        except Exception as e:
            logger.error(f"Error saving JSON log: {e}")
            raise
        
        logger.info(f"Successfully saved conversation logs for {len(collected_messages)} messages")
        logger.info(f"Agents involved: {', '.join(agent_groups.keys())}")
        
        return txt_filepath, json_filepath

    # Example usage function that integrates with your existing code
    async def process_stream_with_logging(
        self,
        stream_2,
        step_name: str,
        output_directory: str,
        save_intermediate: bool = True,
        log_message_callback=None
    ):
        """
        Process message stream and save comprehensive logs.
        
        Args:
            stream_2: The message stream to process
            step_name: Name of the processing step
            output_directory: Directory to save logs
            save_intermediate: Whether to save intermediate results
            log_message_callback: Optional callback function for logging individual messages
        
        Returns:
            StreamResult object with collected messages
        """
        
        # Collect all messages from the stream
        collected_messages = []
        task_result = None
        
        async for message in stream_2:
            # Check if this is the final TaskResult
            if hasattr(message, '__class__') and 'TaskResult' in str(message.__class__):
                task_result = message
                # TaskResult contains the messages list
                collected_messages = message.messages if hasattr(message, 'messages') else collected_messages
            else:
                collected_messages.append(message)
                
                # Call the existing log_message callback if provided
                if log_message_callback:
                    log_message_callback(message)
                
            # Print message preview (your existing code)
            if hasattr(message, 'source') and hasattr(message, 'content'):
                try:
                    if isinstance(message.content, str):
                        content_preview = message.content
                    else:
                        content_str = str(message.content)
                        content_preview = content_str
                    print(f"Agent: {message.source}, Content: {content_preview}")
                except Exception as e:
                    print(f"Agent: {message.source}, Content: [Error displaying content: {e}]")

        logger.info(f"🐧🐧🐧🐧 Collected {len(collected_messages)} messages from groupchat")
        
        # Save comprehensive conversation logs
        if save_intermediate and collected_messages:
            try:
                txt_path, json_path = self.save_conversation_logs(
                    collected_messages=collected_messages,
                    step_name=step_name,
                    output_directory=output_directory,
                    include_tool_calls=True,
                    file_prefix="conversation_log"
                )
                logger.info(f"Conversation logs saved: TXT={txt_path}, JSON={json_path}")
                
            except Exception as e:
                logger.error(f"Error saving conversation logs: {e}")
        
        # Use the TaskResult if available, otherwise create a wrapper
        if task_result:
            stream_result = task_result
        else:
            # Create a result object with the collected messages
            class StreamResult:
                def __init__(self, messages):
                    self.messages = messages
            stream_result = StreamResult(collected_messages)
        
        logger.info("✅✅ Done message collection; Groupchat executed successfully")
        return stream_result

    def save_intermediate_result(self, content: str, filename: str, result_type: str = "prompt"):
        """
        Save intermediate results to appropriate directories.
        
        Args:
            content: Content to save
            filename: Name of the file
            result_type: Type of result (prompt, tc, etc.)
        """
        if result_type == "prompt":
            output_path = settings.INTERMEDIARY_FUNC_EDGE_GENERATED_TESTS
        elif result_type == "tc":
            output_path = settings.INTERMEDIARY_FUNC_EDGE_GENERATED_TESTS
        else:
            output_path = settings.ALL_INTERMEDIATE_STATE_CONFIG
        
        file_path = output_path / f"{filename}.txt"
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"Intermediate result saved: {file_path}")
        except Exception as e:
            logger.error(f"Failed to save intermediate result: {str(e)}")
    
    def log_message(self, msg):
        log_file_path = f"stream_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"  # .jsonl = JSON Lines
        path = os.path.join(settings.END_TO_END_INTERMEDIARY_FILES_PHASE_I_AG_CONVERSATION, log_file_path)

        # Handle different message types and convert non-serializable objects to strings
        def make_serializable(obj):
            """Convert non-JSON-serializable objects to strings"""
            try:
                json.dumps(obj)  # Test if it's already serializable
                return obj
            except (TypeError, ValueError):
                return str(obj)  # Convert to string if not serializable

        # Extract basic message data with safe serialization
        data = {
            'source': make_serializable(getattr(msg, 'source', 'unknown')),
            'content': make_serializable(getattr(msg, 'content', '')),
            'timestamp': make_serializable(getattr(msg, 'timestamp', None))
        }
        
        # Add additional fields if they exist, making them serializable
        if hasattr(msg, 'type'):
            data['type'] = make_serializable(msg.type)
        if hasattr(msg, 'name'):
            data['name'] = make_serializable(msg.name)
        if hasattr(msg, 'tool_calls'):
            # Handle tool calls specially - convert to string representation
            data['tool_calls'] = make_serializable(msg.tool_calls)
        if hasattr(msg, 'function_call'):
            # Handle function calls specially - convert to string representation
            data['function_call'] = make_serializable(msg.function_call)
        
        with open(path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(data, ensure_ascii=False) + '\n')  # JSON Lines format

    async def collect_stream_messages(self,
        stream, us, conversation_type: str = 'prompt',
        save_intermediate: bool = False,
        content_preview_length: int = 200
    ) -> Any:
        """
        Collect all messages from an async stream and handle TaskResult objects.
        
        Args:
            stream: The async stream to process
            log_message_callback: Optional callback function to log each message
            save_intermediate_callback: Optional callback function to save intermediate results
            save_intermediate: Whether to save intermediate results
            content_preview_length: Maximum length for content preview display
            
        Returns:
            TaskResult object if found in stream, otherwise a StreamResult wrapper
        """
        
        logger.info(f"🐧🐧🐧🐧 starting save of logs")

        class StreamResult:
            def __init__(self, messages: List[Any]):
                self.messages = messages
        
        # Collect all messages from the stream
        collected_messages = []
        task_result = None
        
        async for message in stream:
            # Check if this is the final TaskResult
            if hasattr(message, '__class__') and 'TaskResult' in str(message.__class__):
                task_result = message
                # TaskResult contains the messages list
                collected_messages = message.messages if hasattr(message, 'messages') else collected_messages
            else:
                collected_messages.append(message)
                
                # Log message if callback provided
                self.log_message(message)
                
                # Display message preview
                if hasattr(message, 'source') and hasattr(message, 'content'):
                    try:
                        # Try to get string representation of content
                        if isinstance(message.content, str):
                            content_preview = (
                                message.content[:content_preview_length] + "..." 
                                if len(message.content) > content_preview_length 
                                else message.content
                            )
                        else:
                            # For structured objects, convert to string first
                            content_str = str(message.content)
                            content_preview = content_str
                        
                        print(f"Agent: {message.source}, Content: {content_preview}")
                    except Exception as e:
                        print(f"Agent: {message.source}, Content: [Error displaying content: {e}]")
        
        logger.info(f"🐧🐧🐧🐧 Collected {len(collected_messages)} messages from stream")
        
        # Use the TaskResult if available, otherwise create a wrapper
        if task_result:
            stream_result = task_result
        else:
            stream_result = StreamResult(collected_messages)
        
        # Save intermediate results if requested
        if save_intermediate and collected_messages :
            try:
                # Save the last message content as the result
                last_message = collected_messages[-1]
                last_message_content = (
                    last_message.content 
                    if hasattr(last_message, 'content') 
                    else str(last_message)
                )
                
                logger.info(f"🐧🐧🐧🐧🐧🐧🐧🐧Last message content preview: {last_message_content}")
                
                # Save detailed log
                filename = f"{conversation_type}_generation_{us[:20]}"
                self.save_intermediate_result(last_message_content, filename, conversation_type)
                
                # Save a more detailed conversation log
                chat_log = []
                for i, message in enumerate(collected_messages):
                    agent_name = getattr(message, 'source', 'Unknown')
                    content = getattr(message, 'content', str(message))
                    prefix = f"#{i + 1}, {agent_name}: "
                    # Clean up content for summary
                    content_preview = content.replace("\n", " ")
                    chat_log.append(prefix + content_preview)
                
                # Save the full conversation log
                full_log = "\n".join(chat_log)
                detailed_filename = f"{conversation_type}_conversation_log"
                self.save_intermediate_result(full_log, detailed_filename, conversation_type)
                
                print("✅✅ Intermediate results saved successfully")
                
            except Exception as e:
                logger.error(f"Error saving intermediate results: {e}")
                print(f"❌ Error saving intermediate results: {e}")
        
        return stream_result, collected_messages

    def define_prompt_generation_module(self, jira_project_key, US: str, RG: str, CA: str = "") -> Tuple:
        """
        Define the prompt generation module with various AutoGen agents.
        
        Args:
            US: User Story
            RG: Business Rules (Règles de Gestion)
            graph_US: US graph name
            graph_context: Context graph name
            CA: Acceptance Criteria
            
            project_folder_path: Project folder path
            
        Returns:
            Tuple of all defined agents
        """

        # Define the function with proper type annotations
        async def save_json_excel_file_function(
            data_json: Annotated[str, "JSON string representation of the data to save"], 
            content_type: Annotated[str, "Content description like Test_Steps, Detailed_Test_Steps, etc."]
        ) -> Annotated[bool, "True if save operation executed correctly, False otherwise"]:
            """
            Function to save JSON data to files
            """
            try:
                # Parse JSON string to dict if it's a string
                if isinstance(data_json, str):
                    try:
                        data_dict = json.loads(data_json)
                    except json.JSONDecodeError:
                        # If it's not valid JSON, save as string
                        data_dict = data_json
                else:
                    data_dict = data_json
                
                return self.save_json_excel_file(data_dict, content_type)
            except Exception as e:
                logger.error(f"Error in save_json_excel_file_function: {e}")
                return False

        # Create the FunctionTool with strict schema
        save_json_excel_file_tool = FunctionTool(
            save_json_excel_file_function, 
            description="Save JSON data to Excel and JSON files",
            name="save_json_excel_file_tool",
            strict=True
        )



        enhance_agent_syst_message = '''
        Dans toutes tes réponses, tu Tiens compte des paramètres, nom de boutons dans l'interface utilisateur, ou nom de variables s'ils existent. 
        Sois très détaillé.
        '''

        US_Agent_1 = Graph_Agents.define_us_agent(jira_project_key, self.project_folder_path, enhance_agent_syst_message)
        logger.info(f"US_Agent_1 defined with system message")

        # Related US Synthesizer Agent
        related_us_synthesizer = AssistantAgent(
            name="Related_US_Synthesizer",
            description="Synthesizes related User Stories based on the provided US and RG.",
            system_message=f'''Tu es un analyste intelligent de User stories.
                Tu lis le user story de reference, et tu formules des questions associées à l'US concernant des détails que tu ne comprends pas. Tu passe ces questions sous le nom de variable <query_text> à l'US_Agent.
                Ensuite, Tu fais appel à l'US_Agent en lui posant tes questions dans <query_text>. Tu récupères son retour pour chaque question en une variable <INFORMATION_i>, i caractérise l'ordre de la question.
                Lorsque tu achèves tes questions, tu vas appeler l'US_Agent en lui passant cette query : <query_text> : "Quels sont les Critères d'Acceptance des autres User Stories 
                liés à l'US {US}?". Tu enregistres le contenu retourné par la fonction dans une variable <Related_us_query_INFORMATION>. 
                Tu sythétises le contenu retourné par l'US_Agent dans les variables <Related_us_query_INFORMATION> et les <INFORMATION_i> dans une variable <synthesized_information>.

                Tu compares le contenu original de l'US, avec le contenu que tu as synthétisé <synthesized_information>.

                Tu as accès aux Experts suivants :  Finance_Agent, FR_Accounting_Agent, guidelines_Agent, business_domain_Agent en cas de questions ou ambiguités.
                Tu formules des query_text concernant un sujet donné que tu renvoies à l'agent approprié.
                En cas d'absence de business_domain_Agent, tu fais appel aux autres experts.
                Et tu trouves les relations et les interdépendances entre le contenu que tu lis et le User Story de référence. Tu extrais les critères d'acceptance des user stories du projet qui sont en
                relation avec chaque fonctionnalité du User Story de référence.

                Renvoie seulement le résultat final : les critères d'acceptances et informations pertienentes en relation avec l'US de référence.
                ''',
            
            # tools=[save_json_excel_file_tool],
            model_client=self.model_client_REASONING_4_MINI,

           
        )

        # US synthesizer critic
        us_synthesizer_critic = AssistantAgent(
            name="Related_US_Synthesizer_critic",
            system_message="Tu es un critique du contenu acquéri par Related_US_Synthesizer Agent. Tu evalues si le contenu qu'il a aquéri contient des" 
                "critères d'acceptance liés à une même fonctionnalité provenant d'une autre US. Par exemple: dans l'US de référence, pour accepter l'enregistrement"
                "d'un utilisateur dans le système, il faut qu'il introduise le numero de sa carte nationale. Dans un autre US, on trouve aussi que l'utilisateur"
                "doit renseigner ses informations de compte bancaire, sinon il n'est pas accepté. Le Related_US_Synthesizer Agent doit retourner: "
                "Critères d'acceptance: L'utilisateur doit renseigner son numéro de carte nationale. L'utilisateur doit renseigner ses informations de compte bancaire."
                "Tu évalues le résultat du Related_US_Synthesizer, tu lui attribues une note sur 10." 
                "Tu acceptes le résultat qu'il a retourné s'il a une note > 7."
                "Après, tu suggères une variante de la question dans la variable 'query_text' que l'agent utilise pour faire appel au graph, pour optimiser" 
                "le résultat retourné.",        
            # tools=[save_json_excel_file_tool],
            model_client=self.model_client_REASONING_4_MINI,
        )

        # CA synthesizer Agent
        ca_synthesizer = AssistantAgent(
            name="Acceptance_Criteria_Synthesizer",
            system_message=f'''Tu es un synthétiseur des critères d'acceptance de User Story (US). 
                Etant donné un US {US}, tu lis avec beaucoup d'attention les Critères d'acceptance et les règles de gestion liées au User Story. 
                Ensuite, tu fais une synthèse détaillée des CA et RG et tu retournes un ensemble de critères de gestion détaillés avec les noms 
                des boutons dans l'interface de l'application et les noms des paramètres s'ils existent. Ne donne pas des informations non citées dans les RG et CA. 
                Renvoie seulement le résultat final.
                Inclut tous les détails des exigences fonctionnelles et non fonctionnelles, n'ignore aucune exigence.
            ''',
            # tools=[save_json_excel_file_tool],
            model_client=self.model_client_REASONING_4_MINI,
        )



      
        project_Context_Agent = Graph_Agents.define_project_context_agent(
            jira_project_key, project_folder_path=self.project_folder_path
        )

        # Context retrieval Agent
        context_retrieval = AssistantAgent(
            name="Context_Retrieval",
            system_message=f'''Tu es un context retriever. Etant donné l'US suivante {US}, et des informations correspondantes {CA}, {RG}. Tu réalises les étapes suivantes: 
                1. Tu formules des questions par rapport aux abbréviations ou mots que tu ne comprends pas du projet sous forme de liste de <query_text>.
                2. Ensuite, tu demandes au project_Context_Agent chacune des questions de <query_text> Et tu récupères la réponse sous forme de <response_i>, i étant le numéro de la question.
                3. Tu résumes les informations de l'ensmble des réponses aux query dans <Responses_summary>.Le résumé doit être concis.
                4. En achevant les questions que tu as formulé, tu demandes au project_Context_Agent cette question : <query_text> : "Quelles sont les informations générales et
                    fonctionnelles clés concernant le projet ?"
                5. Tu enregistres le contenu retourné par le project_Context_Agent dans une variable <Global_project_info>.
       
                Finalement, tu as <Responses_summary> et <Global_project_info> relatives aux informations que tu as récupéré par le project_Context_Agent.
                Renvoie seulement le résultat final : 

                <Global_project_info> 
                Informations supplémentaires : 
                <Responses_summary>
                ''',
         
            model_client=self.model_client_REASONING_4_MINI,
        )

        # Context retrieval Critic Agent
        context_retrieval_critic = AssistantAgent(
            name="Context_Retrieval_Critic",
            description="Critique the results of the Context_Retrieval agent.",
            system_message="Tu es un critique de la qualité des résultats retournés par le context retriever agent."
                "Tu évalues le résultat du Context_Retrieval, tu lui attribue une note sur 10." 
                "Tu acceptes le résultat qu'il a retourné s'il a une note > 7."
                "Après, tu suggères une variante de la question pour acquérir des connaissances liées au projet, à des termes techniques liées au domaine métier"
                "spécifique, dans la variable 'query_text'.l'agent Context_Retrieval utilise le paramètre 'query_text' pour faire appel au graph, pour optimiser" 
                "le résultat retourné."
                "Si project_Context_Agent n'est pas disponible, fais appel à l'agent US à sa place.",  
           
            model_client=self.model_client_REASONING_4_MINI,
           
        )

        planner = AssistantAgent(
            name="Planner",
            system_message="Tu es un planificateur des actions à prendre selon la situation." 
                "Etant donné un US (User Story) avec des informations: sa description, ses règles de gestion (RG) et ses critères d'acceptance (CA)," 
                "Extrait le contenu en relation avec le User story en question en faisant appel à: Context_Retrieval. Ensuite, fais appel à Context_retrieval_Critic"
                "et appelle-les 2 fois au plus si le Context_Retrieval_Critic donne une note inférieure à 7 sur 10 au résultat retourné par Context_Retrieval."
                "Ensuite, fais appel à Related_US_Synthesizer suivi de US_Synthesizer_critic et appelle-les 2 fois au plus si le US_Synthesizer_critic donne"
                "une note inférieure à 7 sur 10 au résultat retourné par Related_US_Synthesizer."
                "Extrait le contenu retourné par Related_US_Synthesizer ayant la meilleure note sur 10, et mentionne la note attribuée par US_Synthesizer_critic."
                "Cherche les correlations entre l'ensemble de ces US et notre US."
                "Il est très important de Faire appel à l'agent Acceptance_Criteria_Synthesizer pour synthétiser des critères d'acceptance détaillés."
                "Finalement, crée un prompt contenant l'US, sa description, la synthèse de ses critères d'acceptance retournée par Acceptance_Criteria_Synthesizer," 
                "et les informations synthétisées des US qui lui sont liés retournés par Related_US_Synthesizer et Context_Retrieval."
                "Une fois ces étapes achevées, appelle l'agent RGAA_Agent pour acquérir les règles d'accessibilité en relation avec l'US et rajoute le résultat retourné par RGAA_Agent dans le prompt final"
                "Dans le cas ou le projet est en relation avec de la finance, appelle l'agent Finance_Agent pour acquérir les règles de finance en relation avec l'US et rajoute le résultat retourné par Finance_Agent dans le prompt final"
                "Dans le cas ou le projet est en relation avec de la comptabilité, appelle l'agent FR_Accounting_Agent pour acquérir les règles de comptabilité en relation avec l'US et rajoute le résultat retourné par FR_Accounting_Agent dans le prompt final"
                "Finalement, Renvoie le prompt final avec tout le contexte acquis"
                "Si une étape échoue, ne renvoie pas un résultat vide, renvoie le contenu retourné des agents à succès." 
                "Une fois le prompt final généré, tu dois le retourner, ne dis pas des choses inutiles. Le dernier output doit être le prompt final généré par toi, et pas des commentaires inutiles.",
            model_client=self.model_client_REASONING_4_MINI,
        )



        logger.info("Prompt generation module defined successfully")
        return planner, US_Agent_1, project_Context_Agent, context_retrieval, ca_synthesizer, related_us_synthesizer, us_synthesizer_critic, context_retrieval_critic
 
    async def generate_prompt(self, jira_project_key, US: str, planner, US_Agent_1, project_Context_Agent, context_retrieval, ca_synthesizer, 
                       related_us_synthesizer, us_synthesizer_critic, context_retrieval_critic, 
                        CA='', RG="", max_rounds_chat: int = 20, save_intermediate: bool = True) -> Tuple:
        """
        Generate a prompt using the defined agents in a group chat.
        
        Args:
            US: User Story
            RG: Business Rules
            planner: Planner agent
            context_retrieval: Context retrieval agent
            ca_synthesizer: CA synthesizer agent
            related_us_synthesizer: Related US synthesizer agent
            us_synthesizer_critic: US synthesizer critic agent
            context_retrieval_critic: Context retrieval critic agent
            CA: Acceptance Criteria
            max_rounds: Maximum rounds for group chat
            save_intermediate: Whether to save intermediate results
            
        Returns:
            Tuple of group chat result and summary
        """
        
        def selector_func(messages: Sequence[BaseAgentEvent | BaseChatMessage]) -> str | None:
            if messages[-1].source != planner.name:
                return planner.name
            return None
        
        logger.info("🌀🌀 starting SelectorGroupChat 1")

        try:
            RGAA_Agent, Finance_Agent, FR_Accounting_Agent, guidelines_Agent, business_domain_Agent = Graph_Agents.define_all_graph_agents( 
            jira_project_key, project_folder_path=self.project_folder_path, FUNC_EDGE_message=False)

            RGAA_Agent, Finance_Agent, FR_Accounting_Agent, guidelines_Agent, business_domain_Agent = Graph_Agents.define_all_graph_agents( 
            jira_project_key, project_folder_path=self.project_folder_path, FUNC_EDGE_message=False)

            groupchat = SelectorGroupChat(
                participants=[planner, US_Agent_1, project_Context_Agent, context_retrieval, context_retrieval_critic, 
                       related_us_synthesizer, us_synthesizer_critic, ca_synthesizer, 
                       RGAA_Agent, Finance_Agent, FR_Accounting_Agent, guidelines_Agent, business_domain_Agent],
                model_client=self.model_client_REASONING_4_MINI,
                max_turns=max_rounds_chat,
                selector_func=selector_func,
                )

            logger.info("------------------ SelectorGroupChat 1 created -----------------")
            logger.info("------------------ SelectorGroupChat 1 created -----------------")

            task = f'''Etant donnée l'US (User Story) : {US}, 
            et ses critères d'acceptation (CA) : {CA}
            Tu orchestres la conversation de l'équipe pour aboutir à un prompt final contenant toutes les informations nécessaires à l'US.
            Tu retournes au final un prompt textuel contenant toutes les informations.
            '''
            stream = groupchat.run_stream(task=task)

            # await Console(stream)

            stream_result, collected_messages = await self.collect_stream_messages(stream, US, "prompt")

            # Get the messages list
            messages = getattr(stream_result, 'messages', [])

            if messages:
                final_message = messages[-1]
                final_result = getattr(final_message, 'content', str(final_message))
                logger.info(f"Final message retrieved from stream result messages, content: {final_result}")
            elif len(collected_messages) > 0:
                final_result = collected_messages[-1]
                logger.info(f"Final message retrieved from collected messages, content: {final_result}")
            else :
                final_result = "Aucun résultat récupéré."
                logger.warning("No messages found in stream result or collected messages.")

            logger.info(f"Final generated prompt: {final_result}")


            logger.info("Prompt generation completed successfully")
            return stream, final_result
        
            return stream, final_result
        
        except Exception as e:
            logger.error(f"Error during prompt generation: {str(e)}")
            raise
   
    def define_tc_reflection_module(self, US: str, tc_gen_msg: Optional[str] = None, 
                                  output_format_name: str = "Gherkin sans paramètres", 
                                  CA: str = "",  RG: str = "",
                                  parametres: str = "") -> Tuple:
        """
        Define the test case reflection module with generator and critic agents.
        
        Args:
            US: User Story
            RG: Business Rules
            tc_gen_msg: Test case generation message
            output_format_name: Name of output format to use
            
            
            CA: Acceptance Criteria
            parametres: Additional parameters
            
        Returns:
            Tuple of TC generator, CA critic, and system message
        """
        if tc_gen_msg is None:
            tc_gen_msg = self.tc_gen_msg
        
        output_format = self.get_output_format(output_format_name)
       
       
        if parametres == "":
            tc_gen_sys_msg = (tc_gen_msg + "\n Retourne 'TERMINATE' quand tu termines." + 
                            "Retourne des Cas de Test dans ce format: " + output_format + 
                            " \n Inclut les cas passants et non passants, avec une couverture maximale des cas de test. "
                            "Tiens compte des scénarios outline. Respecte le format d'output présenté."
                            "Lis les critères d'acceptance un à un, et crée des scénarios qui en tiennent compte complétement. "
                            "Soit détaillé ! On vise une couverture exhaustive des cas de test.")
        else:
            tc_gen_sys_msg = (tc_gen_msg + f"Les paramètres à utiliser dans les Test Cases sont: {parametres}" + 
                            "\n Retourne 'TERMINATE' quand tu termines." + 
                            "Retourne des Cas de Test dans ce format: " + output_format)

        # TC Generator Agent
        tc_generator = AssistantAgent(
            name="Test_Cases_Generator",
            system_message=tc_gen_sys_msg,
            model_client=self.model_client_REASONING_4_MINI,
        )

        # Reflection: Critic Agents
        ca_critic = AssistantAgent(
            name="Test_Cases_Acceptance_criteria_Critic",
            system_message="Vous êtes un critique des cas de test d'un User Story, relativement aux critères d'acceptance. Vous évaluez le travail du"
            f"générateur de cas de test et evaluez son respect et sa couverture principalement des critères d'acceptance du User Story et " 
            f"des Règles de gestion.  {US}. N'ignore aucune exigence, si une exigence est manquante, demande que le générateur la rajoute."
            "Vous essayez d'améliorer la couverture des cas de test générés. Vous attrribuez une note sur 10 au Test Cases Generator concernant" 
            "son respect des Critères d'acceptance. Renvoyez votre critique et la note attribuée.", 
            model_client=self.model_client_REASONING_4_MINI,                                    
        )

        logger.info("TC reflection module defined successfully")
        return tc_generator, ca_critic, tc_gen_sys_msg

    async def generate_tc(self, prompt_final: str, tc_generator, ca_critic, nb_turns: int = 4, 
                   save_intermediate: bool = True) -> Tuple:
        """
        Generate test cases using the TC generator and critic agents.
        
        Args:
            prompt_final: Final prompt for test case generation
            tc_generator: Test case generator agent
            ca_critic: Acceptance criteria critic agent
            nb_turns: Number of turns for conversation
            save_intermediate: Whether to save intermediate results
            
        Returns:
            Tuple of conversation result and summary
        """
        try:
            
            
            task = (prompt_final + 
                          " \n Inclut les cas passants et non passants, avec une couverture maximale des cas de test. "
                          "Tiens compte des scénarios outline. Respecte le format d'output présenté."
                          "Lis les critères d'acceptance un à un, et crée des scénarios qui en tiennent compte complétement. "
                          "Soit détaillé ! On vise une couverture exhaustive des cas de test.")
            

            reflectGroupchat = SelectorGroupChat(
                participants=[tc_generator, ca_critic],
                model_client=self.model_client_REASONING_4_MINI,
                max_turns=nb_turns,
            )

            stream = reflectGroupchat.run_stream(task=task)

            # await Console(stream)

            stream_result, collected_messages = await self.collect_stream_messages(stream, prompt_final, "tc")

            # Get the messages list
            messages = getattr(stream_result, 'messages', [])

            if messages:
                final_message = messages[-1]
                final_result = getattr(final_message, 'content', str(final_message))
                logger.info(f"Final message retrieved from stream result messages, content: {final_result}")
            elif len(collected_messages) > 0:
                final_result = collected_messages[-1]
                logger.info(f"Final message retrieved from collected messages, content: {final_result}")
            else :
                final_result = "Aucun résultat récupéré."
                logger.warning("No messages found in stream result or collected messages.")


            logger.info(f"Final generated Test Cases: {final_result}")

       
       
            logger.info("Test case generation completed successfully")
            return stream, final_result
        except Exception as e:
            logger.error(f"Error during test case generation: {str(e)}")
            raise

    async def generate_Accessibility_tc(self, jira_project_key, prompt_final: str, tc_generator, ca_critic, nb_turns: int = 4) -> Tuple:
        """
        Generate test cases using the TC generator and critic agents.
        
        Args:
            prompt_final: Final prompt for test case generation
            tc_generator: Test case generator agent
            ca_critic: Acceptance criteria critic agent
            nb_turns: Number of turns for conversation
            
            
        Returns:
            Tuple of conversation result and summary
        """
        try:
            RGAA_Agent, Finance_Agent, FR_Accounting_Agent, guidelines_Agent, business_domain_Agent = Graph_Agents.define_all_graph_agents( 
            jira_project_key, project_folder_path=self.project_folder_path, FUNC_EDGE_message=True)


        

            
            task = (prompt_final + 
                          " \n Inclut les cas passants et non passants, avec une couverture maximale des cas de test. "
                          "Tiens compte des scénarios outline. Respecte le format d'output présenté."
                          "Lis les critères d'acceptance un à un, et crée des scénarios qui en tiennent compte complétement. "
                          "Soit détaillé ! On vise une couverture exhaustive des cas de test.")
            

            reflectGroupchat = SelectorGroupChat(
                participants=[RGAA_Agent, tc_generator, ca_critic],
                model_client=self.model_client_REASONING_4_MINI,
                max_turns=nb_turns,
            )

            stream = reflectGroupchat.run_stream(task=task)

            # await Console(stream)

            stream_result, collected_messages = await self.collect_stream_messages(stream, prompt_final, "tc")

            # Get the messages list
            messages = getattr(stream_result, 'messages', [])

            if messages:
                final_message = messages[-1]
                final_result = getattr(final_message, 'content', str(final_message))
                logger.info(f"Final message retrieved from stream result messages, content: {final_result}")
            elif len(collected_messages) > 0:
                final_result = collected_messages[-1]
                logger.info(f"Final message retrieved from collected messages, content: {final_result}")
            else :
                final_result = "Aucun résultat récupéré."
                logger.warning("No messages found in stream result or collected messages.")


            logger.info(f"Final generated Test Cases: {final_result}")

       
       
            logger.info("Test case generation completed successfully")
            return stream, final_result
        except Exception as e:
            logger.error(f"Error during test case generation: {str(e)}")
            raise

    async def generate_functional_test_cases(self, user_id: str) -> Dict[str, Any]:
        """
        Async version of generate_functional_test_cases for use in utils.
        Generate functional test cases from previously imported user stories Excel file.
        
        Returns:
            Dict containing generation results or raises Exception on failure
        """
        
        try:
            logger.info(f"Starting functional test case generation for user: {user_id}")
            state = get_processing_state()
            user_paths = user_data_manager._load_data(user_id)
            jira_project_key = user_paths.get('us_project_key')

            if not os.path.exists(settings.US_PATH_TO_GENERATE/jira_project_key/user_id):
                raise Exception("Path not existing")
            
            # Verify the Excel file exists
            if not os.path.exists(settings.US_PATH_TO_GENERATE/jira_project_key/user_id):
                # Try to find the most recent Excel file in the directory
                try:
                   
                    excel_files = glob.glob(os.path.join(settings.US_PATH_TO_GENERATE/jira_project_key/user_id, "user_stories_*.xlsx"))
                    if not excel_files:
                        raise Exception("No user stories Excel files found in the directory. Please import user stories first.")

                    # Get the most recent file
                    state.last_imported_excel_path = max(excel_files, key=os.path.getctime)
                    logger.info(f"Using most recent Excel file: {state.last_imported_excel_path}")                    
                except Exception as e:
                    raise Exception(f"Cannot find user stories Excel file: {str(e)}")
            
            try:
                logger.info(f"Loading user stories from Excel")
                df = pd.read_excel(state.last_imported_excel_path, engine="openpyxl")
                

                if df is None or df.empty:
                    raise Exception("The user stories Excel file is empty")

                logger.info(f"⭕ Loaded {len(df)} user stories from Excel file")

            except Exception as e:
                logger.error(f"Failed to load Excel file: {str(e)}")
                raise Exception(f"Failed to load user stories Excel file: {str(e)}")

            interm_save_path = os.path.join(settings.INTERMEDIARY_FUNC_EDGE_GENERATED_TESTS, jira_project_key)
            logger.warning(f"Intermediary save path: {interm_save_path}")
            os.makedirs(interm_save_path, exist_ok=True)
            logger.warning(f"Intermediary save path Created Successfully : {interm_save_path}")
            tc_json_path = os.path.join(interm_save_path, f"generated_test_cases_history_{user_id}.json")
            existing_cases = []
            if os.path.exists(tc_json_path):
                try:
                    with open(tc_json_path, 'r', encoding='utf-8') as f:
                        existing_cases = json.load(f)
                except json.JSONDecodeError:
                    logger.warning("Existing JSON file was corrupted, starting fresh")
                    existing_cases = []
                        
      
            # Initialize result containers
            result_data = {
                'prompt_list': [],
                'full_prompt_list': [],
                'tc_list': [],
                'costs_list': []
            }

            logger.info("⚡⚡⚡ About to enter generation loop........................................")

            # TC generation message
            tc_gen_msg = '''Tu es un générateur de Cas de Test en Gherkin. Etant donné un User Story, génère les cas de Test qui lui sont associés en tenant 
    compte surtout de ses critères d'accpetance, ainsi que des informations pertinentes liées au projet. Fait attention surtout aux règles à respecter pour 
    une fonctionnalité donnée qui proviennent d'une autre US mais qui est liée. \n '''

            # Process each user story
            for index, row in df.iterrows():
                try:
                    logger.info(f"Processing user story {index + 1}/{len(df)}")
                    
                    # Extract user story data with proper type conversion and null handling
                    us_title = str(row.get('Titre', '')) if row.get('Titre') is not None else ""
                    us_description = str(row.get('Description', '')) if row.get('Description') is not None else ""
                    us = us_title + " " + us_description
                    
                    tc_format_value = user_data_manager.get_field_value("TC_format")

                    rg = str(row.get('Règles de gestion', '')) if row.get('Règles de gestion') is not None else ""
                    ca = str(row.get("Critères d'acceptance", '')) if row.get("Critères d'acceptance") is not None else ""
                    parametres = str(row.get("Paramètres", '')) if (tc_format_value == "Gherkin avec paramètres" and row.get("Paramètres") is not None) else ""

                    # Debug logging to identify any remaining issues
                    logger.debug(f"Debug - Processing row {index + 1}")
                    logger.debug(f"Debug - us type: {type(us)}")
                    logger.debug(f"Debug - rg type: {type(rg)}")
                    logger.debug(f"Debug - ca type: {type(ca)}")

                    # Ensure all variables are strings and not dictionaries
                    if isinstance(us, dict) or isinstance(rg, dict) or isinstance(ca, dict):
                        logger.error(f"Unexpected dict type found in row {index + 1}")
                        logger.error(f"us is dict: {isinstance(us, dict)}")
                        logger.error(f"rg is dict: {isinstance(rg, dict)}")
                        logger.error(f"ca is dict: {isinstance(ca, dict)}")
                        raise ValueError("Unexpected dictionary type in user story data")

                    print("⚡ Defining prompt generation module........................................ ")
                    
                    # Generate prompts and test cases
                    planner, US_Agent_1, project_Context_Agent, context_retrieval, ca_synthesizer, related_us_synthesizer, us_synthesizer_critic, context_retrieval_critic = self.define_prompt_generation_module(
                       jira_project_key, us, rg, ca)
                    
                    logger.info("⚡⚡ Generating prompt and test cases........................................ ")
                    
                    # Run async functions with await
                    prompt_stream, generated_prompt = await self.generate_prompt(jira_project_key,
                        us, planner, US_Agent_1, project_Context_Agent, context_retrieval, ca_synthesizer,
                        related_us_synthesizer, us_synthesizer_critic, 
                        context_retrieval_critic, ca, rg, 4, True
                    )
                    
                    logger.info("⚡⚡⚡ Defining TC reflection module........................................ ")
                    tc_generator, ca_critic, tc_prompt = self.define_tc_reflection_module(
                        us, tc_gen_msg, tc_format_value, ca, rg, parametres)
                    logger.info("⚡⚡⚡⚡ Generating test cases........................................ ")

                    tc_stream, generated_tc = await self.generate_tc(
                        generated_prompt, tc_generator, ca_critic, 3
                    )
                    logger.info("⚡⚡⚡⚡⚡ Test cases generated successfully........................................ ")

                    # Create and save case entry
                    case_entry = {
                        "timestamp": datetime.now().isoformat(),
                        "us_id": str(row.get('US_ID', f"no_id_{index}")),
                        "us_title": str(row.get('Titre', '')),
                        "test_case": generated_tc,
                        "prompt": generated_prompt,
                        "costs": {
                            "prompt_generation": "blank",
                            "tc_generation": "blank",
                        },
                        "metadata": {
                            "format": getattr(state, 'selected_format', 'default'),
                            "source": "Excel_file",
                            "excel_source": state.last_imported_excel_path
                        }
                    }
                    
                    existing_cases.append(case_entry)
                    logger.warning(f"---------- Going to save test cases to: {tc_json_path}")
                    with open(tc_json_path, 'w', encoding='utf-8') as f:
                        json.dump(existing_cases, f, indent=2, ensure_ascii=False)
                    logger.warning(f"---------- Test cases saved successfully to: {tc_json_path}")

                    # Append to result lists - ALWAYS append to maintain consistent list lengths
                    result_data['prompt_list'].append(generated_prompt)
                    result_data['full_prompt_list'].append(tc_prompt + generated_prompt)
                    result_data['tc_list'].append(generated_tc)
                    result_data['costs_list'].append("blank")

                    logger.warning(f"Successfully processed user story {index + 1}")

                except Exception as e:
                    logger.error(f"Failed to process user story {index + 1}: {str(e)}")
                    # CRITICAL FIX: Append placeholder values to maintain list consistency
                    result_data['prompt_list'].append(f"Error processing user story {index + 1}")
                    result_data['full_prompt_list'].append(f"Error processing user story {index + 1}")
                    result_data['tc_list'].append(f"Error: {str(e)}")
                    result_data['costs_list'].append("Error - No cost calculated")
                    continue

            # Verify all lists have the same length before creating DataFrame
            list_lengths = {key: len(value) for key, value in result_data.items()}
            print(f"List lengths: {list_lengths}")
            
            if len(set(list_lengths.values())) > 1:
                logger.error(f"Inconsistent list lengths: {list_lengths}")
                raise ValueError(f"All result lists must have the same length. Current lengths: {list_lengths}")

            # Save Excel output
            output_data = {
                'Row_Generated Prompts': result_data['prompt_list'],
                'Final input prompts': result_data['full_prompt_list'],
                'Test Cases': result_data['tc_list'],
                'Costs': result_data['costs_list']
            }

            # Add IDs and titles from the loaded DataFrame
            if 'US_ID' in df.columns:
                output_data['id_US'] = df['US_ID'].tolist()
            if 'Titre' in df.columns:
                output_data['Title'] = df['Titre'].tolist()

            df_resultat = pd.DataFrame(output_data)
            # output_folder = os.path.join(settings.GENERATED_EDGE_FUNCTIONAL_TESTS, jira_project_key)
            output_folder = os.path.join(settings.GENERATED_EDGE_FUNCTIONAL_TESTS, jira_project_key)
            logger.warning(f"\n \n -------------- Output folder: {output_folder}")
            #  Ensure the directory exists            
            os.makedirs(output_folder, exist_ok=True)
            logger.warning(f"--------------created created Output folder : {output_folder}")


            # Build the file path
            final_output_path = os.path.join(
                output_folder,
                f"Gen_TC_functional_non_functional_{user_id}.xlsx"
            )
            logger.warning(f"--------------final_output_path : {final_output_path}")

            #  Save the Excel file
            df_resultat.to_excel(final_output_path, index=False, engine="openpyxl")

            # Check if Jira integration should be performed (only if original data was from Jira)
            try:
                # Check if we need to get user_paths for Jira integration
                # if os.path.exists(settings.USER_PATHS_JSON_FILE):
                #     with open(settings.USER_PATHS_JSON_FILE, 'r') as f:
                #         user_paths = json.load(f)
                        
                if (getattr(state, 'jira_input', False) and user_paths.get("US_output_name_field")):
                    jira_service.create_link_tickets(user_paths, df_resultat, link_type="Relates")
                    logger.info("Jira tickets created and linked")
            except Exception as e:
                logger.warning(f"Jira integration failed: {str(e)}")

            return {
                "message": "Test cases generated successfully",
                "excel_path": final_output_path,
                "json_path": tc_json_path,
                "source_excel_path": state.last_imported_excel_path,
                "total_cases_generated": len(result_data['tc_list']),
                "total_cases_in_history": len(existing_cases)
            }

        except Exception as e:
            logger.error(f"Critical error in test case generation: {str(e)}")
            raise Exception(f"Test case generation failed: {str(e)}")
        

