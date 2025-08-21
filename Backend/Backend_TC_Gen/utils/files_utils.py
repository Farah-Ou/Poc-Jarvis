import os
import json
import logging
import ast
from sympy import content
from typing_extensions import Annotated
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, List
from Backend_TC_Gen.utils.config import settings, LLM_CONFIGS
from openai import OpenAI
import re

logger = logging.getLogger(__name__)




class GeneralFileUtils():
    def Extract_RG_CA_US_from_Description(self, description_to_separate, jira_project_key, user_id):
        """
        Simple function to evaluate content using OpenAI and save the cleaned result.
        
        Args:
            content_to_evaluate: Content to evaluate
            output_format_str: Target output format description
            save_filename: Name of file to save
            save_type: Type of save ("Test_Steps" or "High_Level_Tests")
            
        Returns:
            str: Success message with save location
        """
    
        
        # Prepare input prompt
        prompt = f'''Given this content {description_to_separate}, it will include a description and explanations of a user story, its acceptance criteria, and business rules.

        Reformat the textual description into 3 distinct sections: User Story Description, Acceptance Criteria, and Business Rules.

        Output Format : 

        {settings.us_output_format}

        Return the original integral text and don't make any modifications. It's simple data formatting.
        Any information that's not "Acceptance Criteria" or  "Business Rules"  belongs to "User Story Description".

        Response (valid JSON only, no other text), don't write ''json, don't write anything at all other than the json as the output format. Your output will be directly saved to a json file with no other processing.
        '''

        # Define openai llm call
        client = OpenAI()
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.1
        )
        
        logger.info(f"---------------------- OpenAI response: {response} ------------------------")
        pre_cleaned_content = response.choices[0].message.content.strip()

        cleaned_content = self.clean_llm_json_response(pre_cleaned_content)
        logger.info(f"------------------------ Cleaning result: {cleaned_content[:]} -------------------------") 

        final_path_txt = os.path.join(settings.GENERATED_EDGE_FUNCTIONAL_TESTS, jira_project_key,f"RG_CA_US_{user_id}.txt")
        final_path = os.path.join(settings.GENERATED_EDGE_FUNCTIONAL_TESTS, jira_project_key,f"RG_CA_US_{user_id}.json")

        # Save TXT to file
        try:
            with open(final_path_txt, "w", encoding="utf-8") as f:
                f.write(str(cleaned_content))

            with open(final_path, 'w', encoding='utf-8') as f:
                json.dump(cleaned_content, f, ensure_ascii=False, indent=4)
            logger.info(f"Saved cleaned content to: {final_path}")
        except Exception as e:
            logger.error(f"Failed to save JSON file: {e}")        

        return cleaned_content, final_path
    

    def evaluate_and_save_content(self, content_to_evaluate, output_format_str, save_filename, save_type):
        """
        Simple function to evaluate content using OpenAI and save the cleaned result.
        
        Args:
            content_to_evaluate: Content to evaluate
            output_format_str: Target output format description
            save_filename: Name of file to save
            save_type: Type of save ("Test_Steps" or "High_Level_Tests")
            
        Returns:
            str: Success message with save location
        """
        
        # Convert content_to_evaluate to string if it's not already
        if isinstance(content_to_evaluate, (list, dict)):
            content_str = json.dumps(content_to_evaluate, indent=2, ensure_ascii=False)
        else:
            content_str = str(content_to_evaluate)
        
        # Prepare input prompt
        prompt = f'''Given this content {content_str}, format it to correspond to the target output {output_format_str}, and return a final response that contains only the formatted output to be saved. Don't add any other text or message.

        Output Format : 
        {output_format_str}

        Response (valid JSON only, no other text), don't write ''json, don't write anything at all other than the json as the output format Your output will be directly saved to a json file with no other processing.
        '''

        # Define openai llm call
        client = OpenAI()
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.1
        )
        
        logger.info(f"---------------------- OpenAI response: {response} ------------------------")
        logger.info(f"---------------------- OpenAI response: {response} ------------------------")
        pre_cleaned_content = response.choices[0].message.content.strip()

        cleaned_content = self.clean_llm_json_response(pre_cleaned_content)
        logger.info(f"------------------------ Cleaning result: {cleaned_content[:]} -------------------------") 
        logger.info(f"------------------------ Cleaning result: {cleaned_content[:]} -------------------------") 
        
        final_path = self.save_intermediate_result(cleaned_content, save_filename, save_type)
        
        return f"Successfully saved {save_filename} to {final_path}"

    def save_intermediate_result(self, cleaned_content, save_filename, save_type):
        # Create target_save_folder
        if save_type == "Test_Steps":
            save_file = settings.END_TO_END_INTERMEDIARY_CLEAN_FILES
        elif save_type == "High_Level_Tests":
            save_file = settings.END_TO_END_INTERMEDIARY_CLEAN_FILES
        elif save_type == "Detailed_Test_Steps":
            save_file = settings.END_TO_END_INTERMEDIARY_CLEAN_FILES
        elif save_type == "US_contextualized_test_steps":
            save_file = settings.END_TO_END_INTERMEDIARY_CLEAN_FILES
        elif save_type == "US_List_":
            save_file = settings.END_TO_END_INTERMEDIARY_FILES_BLOC_II
        elif save_type == "refined_tests_":
            save_file = settings.END_TO_END_INTERMEDIARY_FILES_BLOC_III
        else:
            save_file = settings.END_TO_END_INTERMEDIARY_FILES_TRACE_FILES
        
        # Create directory if it doesn't exist
        os.makedirs(save_file, exist_ok=True)
        
        # Save operation in json format
        final_path = os.path.join(save_file, save_filename)
        
        # Ensure filename has .json extension
        if not final_path.endswith('.json'):
            final_path += '.json'
        
        # Parse and save as JSON
        try:
            # cleaned_content should already be a dict/list from clean_llm_json_response
            if isinstance(cleaned_content, (dict, list)):
                json_content = cleaned_content
            else:
                # Try to parse as JSON if it's still a string
                json_content = json.loads(cleaned_content)
                
            with open(final_path, 'w', encoding='utf-8') as f:
                json.dump(json_content, f, indent=2, ensure_ascii=False)
        except json.JSONDecodeError:
            # If not valid JSON, save as string wrapped in JSON
            with open(final_path, 'w', encoding='utf-8') as f:
                json.dump({"content": cleaned_content}, f, indent=2, ensure_ascii=False)
        return final_path



    def get_messages_by_agent(self, messages: List, agent_name: str) -> List:
        """Extract messages from a specific agent."""
        return [m for m in messages 
                if hasattr(m, 'source') and agent_name in m.source]
    
    def extract_message_content(self, message) -> str:
        """Extract content from a single message."""
        content = getattr(message, 'content', '')
        
        # Convert to string if it's not already
        if isinstance(content, (list, dict)):
            return json.dumps(content, indent=2, ensure_ascii=False)
        return str(content)
    
    def iterative_content_extraction_with_formatting(self, messages: List, agent_name: str, 
                                                   output_format: str, save_filename: str, 
                                                   save_type: str) -> Optional[str]:
        """
        Iteratively extract content from agent messages (starting from last) and format using evaluate_and_save_content.
        
        Args:
            messages: List of all messages
            agent_name: Name of the agent to extract messages from
            output_format: Target output format description
            save_filename: Name of file to save
            save_type: Type of save ("Test_Steps" or "High_Level_Tests")
            main_processor: Reference to main class that has evaluate_and_save_content method
            
        Returns:
            str: Success message if content was found and formatted, None otherwise
        """
        agent_msgs = self.get_messages_by_agent(messages, agent_name)
        
        if not agent_msgs:
            logger.warning(f"No messages found from agent: {agent_name}")
            return None
        
        # Start from the last message and work backwards
        for i in range(len(agent_msgs) - 1, -1, -1):
            try:
                message = agent_msgs[i]
                content = self.extract_message_content(message)
                
                # Skip empty content
                if not content or content.strip() == "":
                    continue
                
                logger.info(f"Attempting to format content from message {i+1}/{len(agent_msgs)} from {agent_name}")
                
                # Try to format the content using the existing function
                result = self.evaluate_and_save_content(
                    content_to_evaluate=content,
                    output_format_str=output_format,
                    save_filename=save_filename,
                    save_type=save_type
                )
                
                logger.info(f"Successfully formatted content from message {i+1}: {result}")
                return result
                
            except Exception as e:
                logger.warning(f"Failed to format content from message {i+1} from {agent_name}: {str(e)}")
                continue
        
        logger.error(f"Could not extract and format valid content from any {agent_name} messages")
        return None
    
    def _process_content(self, content: Any) -> List[Dict]:
        """Process content from various formats into a list of dictionaries."""
        processed_tests = []
        
        if isinstance(content, list):
            processed_tests = self._process_list_content(content)
        elif hasattr(content, 'model_dump'):
            # Single Pydantic v2 model
            processed_tests = [content.model_dump()]
        elif hasattr(content, 'dict'):
            # Single Pydantic v1 model
            processed_tests = [content.dict()]
        elif isinstance(content, str):
            processed_tests = self._parse_string_content(content)
        else:
            logger.warning(f"Unexpected content type: {type(content)}")
        
        return processed_tests
    
    def _process_list_content(self, content: List) -> List[Dict]:
        """Process list content into dictionaries."""
        processed_tests = []
        
        for item in content:
            if hasattr(item, 'model_dump'):
                # Pydantic v2 model
                processed_tests.append(item.model_dump())
            elif hasattr(item, 'dict'):
                # Pydantic v1 model
                processed_tests.append(item.dict())
            elif hasattr(item, '__dict__'):
                # Regular object
                processed_tests.append(item.__dict__)
            elif isinstance(item, dict):
                # Already a dictionary
                processed_tests.append(item)
            else:
                logger.warning(f"Unexpected item type in tests: {type(item)}")
        
        return processed_tests
    
    def _parse_string_content(self, content: str) -> List[Dict]:
        """Parse string content as JSON or Python literal."""
        try:
            # Remove markdown code block formatting
            content = content.strip()
            if content.startswith('```json'):
                content = content[7:]
            if content.endswith('```'):
                content = content[:-3]
            content = content.strip()
            
            # Parse as JSON
            return json.loads(content)
        except json.JSONDecodeError:
            # Try ast.literal_eval as backup
            try:
                return ast.literal_eval(content)
            except (ValueError, SyntaxError):
                logger.warning(f"Could not parse content: {content}")
                return []
    
    def validate_test_structure(self, tests: List[Dict], flow_title: str) -> bool:
        """Validate that tests have the expected structure."""
        if not tests or not isinstance(tests, list):
            logger.warning(f"No tests found for flow '{flow_title}'")
            return False
        
        if not isinstance(tests[0], dict) or 'Test_Id' not in tests[0]:
            logger.warning(f"Test structure is not as expected for flow '{flow_title}': {tests}")
            return False
        
        return True
    
    def add_flow_context(self, tests: List[Dict], flow_title: str) -> List[Dict]:
        """Add flow context to each test for traceability."""
        for test in tests:
            test["Original_Flow_Title"] = flow_title
        return tests
    
    def save_tests_to_file(self, tests: List[Dict], filename: str) -> str:
        """Save tests to JSON file and return the file path."""
        file_path = os.path.join(settings.END_TO_END_INTERMEDIARY_FILES, filename)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(tests, f, indent=2, ensure_ascii=False)
        return file_path
    
    def save_conversation_log(self, messages, flow_title: str, refined_agent: str, us_agent: str):
        """Save conversation log to file."""
        refined_msgs = self.get_messages_by_agent(messages, refined_agent)
        us_agent_msgs = self.get_messages_by_agent(messages, us_agent)
        
        filename = f"refined_tests_conversation_{flow_title.replace(' ', '_')}.txt"
        output_file = os.path.join(settings.END_TO_END_INTERMEDIARY_FILES, filename)
        
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(f"=== {refined_agent} Messages ===\n\n")
            self._write_messages_to_file(f, refined_msgs, refined_agent)
            
            f.write(f"\n\n=== {us_agent} Messages ===\n\n")
            self._write_messages_to_file(f, us_agent_msgs, us_agent)
    
    def _write_messages_to_file(self, file_handle, messages: List, agent_name: str):
        """Helper method to write messages to file."""
        for msg in messages:
            content = getattr(msg, 'content', str(msg))
            
            if isinstance(content, list):
                file_handle.write(f"{agent_name}: {len(content)} tests generated\n")
                for i, item in enumerate(content):
                    formatted_item = self._format_item_for_logging(item)
                    file_handle.write(f"  {i+1}. {formatted_item}\n")
            else:
                formatted_content = self._format_item_for_logging(content)
                file_handle.write(f"{agent_name}: {formatted_content}\n")
            
            file_handle.write("\n")
    
    def _format_item_for_logging(self, item: Any) -> str:
        """Format an item for logging purposes."""
        if hasattr(item, 'model_dump'):
            return str(item.model_dump())
        elif hasattr(item, 'dict'):
            return str(item.dict())
        elif hasattr(item, '__dict__'):
            return str(item.__dict__)
        else:
            return str(item)

    

    def clean_llm_json_response(self, llm_response):
        """
        Clean LLM JSON response by removing markdown formatting, extra wrappers, and extracting pure JSON.
        
        Args:
            llm_response (str or dict): Raw LLM response that may contain markdown or wrapper objects
            
        Returns:
            dict or list: Clean JSON object ready to be saved
        """
        try:
            # If input is already a dict or list, check if it has a 'content' wrapper
            if isinstance(llm_response, dict):
                if 'content' in llm_response:
                    content = llm_response['content']
                else:
                    # Already clean JSON
                    return llm_response
            elif isinstance(llm_response, list):
                # Already a clean list
                return llm_response
            else:
                # Input is a string
                content = str(llm_response)
            
            # Step 1: Remove markdown code block formatting
            content = self._remove_markdown_formatting(content)
            
            # Step 2: Remove common LLM prefixes/suffixes
            content = self._remove_llm_artifacts(content)
            
            # Step 3: Clean up whitespace and newlines
            content = self._clean_whitespace(content)
            
            # Step 4: Extract JSON from the cleaned content
            json_content = self._extract_json_content(content)
            
            # Step 5: Parse and validate JSON
            cleaned_json = json.loads(json_content)
            
            logger.info("Successfully cleaned LLM JSON response")
            
            return cleaned_json
            
        except json.JSONDecodeError as e:
            logger.error(f" (1) -------------------- JSON parsing failed after cleaning: {e} ----------------------- ")
            logger.error(f"Problematic content: {content[:500]}...")
            raise ValueError(f"Could not parse cleaned content as JSON: {e}")
        except Exception as e:
            logger.error(f" (2) ------------------------ Unexpected error in JSON cleaning: {e} ----------------------")
            raise ValueError(f"JSON cleaning failed: {e}")


    def _remove_markdown_formatting(self, content):
        """Remove markdown code block formatting."""
        content = content.strip()
        
        # Remove opening markdown blocks
        markdown_patterns = [
            r'^```json\s*',
            r'^```\s*',
            r'^`json\s*',
            r'^`\s*'
        ]
        
        for pattern in markdown_patterns:
            content = re.sub(pattern, '', content, flags=re.MULTILINE)
        
        # Remove closing markdown blocks
        if content.endswith('```'):
            content = content[:-3]
        elif content.endswith('`'):
            content = content[:-1]
        
        return content.strip()


    def _remove_llm_artifacts(self, content):
        """Remove common LLM response artifacts and prefixes."""
        
        # Common LLM prefixes to remove
        prefixes_to_remove = [
            r'^Here\'s the.*?:\s*',
            r'^Here is the.*?:\s*',
            r'^The JSON.*?:\s*',
            r'^Response:\s*',
            r'^Output:\s*',
            r'^Result:\s*',
            r'^JSON:\s*',
            r'^.*?json.*?:\s*'
        ]
        
        for pattern in prefixes_to_remove:
            content = re.sub(pattern, '', content, flags=re.IGNORECASE | re.MULTILINE)
        
        # Common suffixes to remove
        suffixes_to_remove = [
            r'\s*This is the.*?$',
            r'\s*Hope this helps.*?$',
            r'\s*Let me know.*?$'
        ]
        
        for pattern in suffixes_to_remove:
            content = re.sub(pattern, '', content, flags=re.IGNORECASE | re.MULTILINE)
        
        return content.strip()


    def _clean_whitespace(self, content):
        """Clean up excessive whitespace while preserving JSON structure."""
        # Replace multiple newlines with single newlines
        content = re.sub(r'\n\s*\n', '\n', content)
        
        # Remove leading/trailing whitespace from each line while preserving structure
        lines = content.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Keep indentation for JSON structure, but remove excessive spaces
            if line.strip():
                cleaned_lines.append(line.rstrip())
            elif cleaned_lines and cleaned_lines[-1].strip():
                # Keep empty lines that separate JSON blocks
                cleaned_lines.append('')
        
        return '\n'.join(cleaned_lines).strip()


    def _extract_json_content(self, content):
        """Extract the JSON content from the cleaned text."""
        
        # Try to find JSON content between braces or brackets
        json_patterns = [
            r'(\[.*\])',  # Array pattern
            r'(\{.*\})'   # Object pattern
        ]
        
        for pattern in json_patterns:
            matches = re.findall(pattern, content, re.DOTALL)
            if matches:
                # Return the longest match (most likely to be the complete JSON)
                longest_match = max(matches, key=len)
                return longest_match
        
        # If no pattern matches, return the original content
        return content


    def save_cleaned_json(self,cleaned_json, filepath):
        """
        Save the cleaned JSON to a file.
        
        Args:
            cleaned_json (dict or list): Clean JSON object
            filepath (str): Path where to save the file
        """
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(cleaned_json, f, indent=2, ensure_ascii=False)
            logger.info(f"Cleaned JSON saved successfully to: {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to save cleaned JSON to {filepath}: {e}")
            return False


    # Example usage and test function
    def test_json_cleaner(self):
        """Test the JSON cleaner with the provided example."""
        
        # Your example input
        test_input = {
            "content": "```json\n[\n    {\n        \"Test_Title\": \"Simulateur de Deal\",\n        \"Test_Steps\": [\n            {\n                \"Step_Name\": \"Entrée des conditions normales de deal\",\n                \"Step_Features\": [\"Simulation de Deal\"],\n                \"Step_Status\": \"Passing\"\n            },\n            {\n                \"Step_Name\": \"Vérifier la simulation\",\n                \"Step_Features\": [\"Simulation de Deal\"],\n                \"Step_Status\": \"Passing\"\n            }\n        ]\n    }\n]\n```"
        }
        
        try:
            cleaned = self.clean_llm_json_response(test_input)
            logger.info("✅ Cleaning successful!" , json.dumps(cleaned, indent=2, ensure_ascii=False))
            return cleaned
        except Exception as e:
            logger.error(f"❌ Cleaning failed: {e}")
            return None


    # Simple wrapper for your use case
    def clean_and_save_llm_json(self, llm_response, save_path):
        """
        Clean LLM JSON response and save it directly to a file.
        
        Args:
            llm_response: Raw LLM response (string or dict)
            save_path: Path where to save the cleaned JSON
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            cleaned_json = self.clean_llm_json_response(llm_response)
            return self.save_cleaned_json(cleaned_json, save_path)
        except Exception as e:
            logger.error(f"Clean and save operation failed: {e}")
            return False


class FilesGraphs():

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

        

        # Ensure output directories exist
        self._ensure_output_directories()
        
        logger.info(f"FuncEdgeGeneration initialized with project path: {self.project_folder_path}")

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



class TestFlows():
    """
    Service class for handling file operations related to end-to-end test generation.
    Inherits from FilesGraphs to utilize common file handling methods.
    """
    def __init__(self, custom_settings: Optional[Dict[str, Any]] = None):
        """
        Initialize the TestFlows class with configurations from FilesGraphs.
        
        Args:
            custom_settings: Optional dictionary to override default settings
        """
        self.files_graphs = FilesGraphs(custom_settings)
        self.logger = logging.getLogger(__name__)

    def extract_flows_from_dict(self, test_flows, logger):
        """
        Extract test flows from dictionary structure.
        
        Args:
            test_flows (dict): Dictionary containing test flows
            logger: Logger instance
            
        Returns:
            list: Extracted test flows
        """
        # Look for keys that might contain the actual test flows
        possible_keys = [
            "test_flows", "flows", "Test_Flows", "tests", "data", 
            "Tests de bout en bout", "Tests bout en bout", 
            "End to End Tests", "End to End tests"
        ]
        
        for key in possible_keys:
            if key in test_flows and isinstance(test_flows[key], list):
                test_flows = test_flows[key]
                logger.info(f"Extracted test_flows from '{key}' key")
                return test_flows
        
        # If no standard key found, try to find any list value
        for key, value in test_flows.items():
            if isinstance(value, list) and value:
                # Check if the list contains dict-like objects
                if isinstance(value[0], dict) or isinstance(value[0], str):
                    test_flows = value
                    logger.info(f"Extracted test_flows from '{key}' key (auto-detected)")
                    return test_flows
        
        # Convert nested dict structure to list of flows
        return self.convert_nested_dict_to_flows(test_flows, logger)


    def convert_nested_dict_to_flows(self, test_flows, logger):
        """
        Convert nested dictionary structure to list of flows.
        
        Args:
            test_flows (dict): Nested dictionary structure
            logger: Logger instance
            
        Returns:
            list: Converted flows
        """
        logger.info("Converting nested dict structure to flow list")
        converted_flows = []
        
        # Handle structure like: {"Tests bout en bout": {"Simulateur de Deal": {"Passant": "...", "Non Passant": "..."}}}
        for main_category, category_content in test_flows.items():
            logger.info(f"Processing main category: {main_category}")
            if isinstance(category_content, dict):
                for feature_name, feature_tests in category_content.items():
                    logger.info(f"Processing feature: {feature_name}")
                    if isinstance(feature_tests, dict):
                        # Each feature becomes a flow with multiple steps
                        flow_steps = []
                        
                        for test_type, test_description in feature_tests.items():
                            logger.info(f"Creating step for test type: {test_type}")
                            # Create a step for each test type (Passant/Non Passant)
                            step = {
                                "Step_Name": f"{test_type}",
                                "Step_Features": [feature_name],  # Use feature name as feature ID
                                "Step_Description": test_description,
                                "Step_Type": test_type
                            }
                            flow_steps.append(step)
                        
                        # Create the flow
                        flow = {
                            "Test_Title": f"{main_category} - {feature_name}",
                            "Test_Steps": flow_steps
                        }
                        converted_flows.append(flow)
                        logger.info(f"Converted feature '{feature_name}' to flow with {len(flow_steps)} steps")
                    
                    elif isinstance(feature_tests, str):
                        # Single test description
                        flow = {
                            "Test_Title": f"{main_category} - {feature_name}",
                            "Test_Steps": [{
                                "Step_Name": feature_name,
                                "Step_Features": [feature_name],
                                "Step_Description": feature_tests
                            }]
                        }
                        converted_flows.append(flow)
                        logger.info(f"Converted simple feature '{feature_name}' to flow")
        
        logger.info(f"Successfully converted nested structure to {len(converted_flows)} flows")
        
        if not converted_flows:
            logger.error("Could not convert nested dict structure to flows")
        
        return converted_flows


    def validate_individual_flows(self, test_flows, logger):
        """
        Validate individual flows in the test flows list.
        
        Args:
            test_flows (list): List of test flows to validate
            logger: Logger instance
            
        Returns:
            list: Validated flows
        """
        validated_flows = []
        
        for i, flow in enumerate(test_flows):
            logger.info(f"Processing flow {i}: type={type(flow)}")
            
            if isinstance(flow, str):
                logger.warning(f"Flow {i} is a string, attempting to parse: {flow[:100]}...")
                try:
                    flow = json.loads(flow)
                    logger.info(f"Successfully parsed flow {i} from string")
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse flow {i} as JSON: {e}")
                    continue
            
            if isinstance(flow, dict):
                # Validate that the flow has the expected structure
                if "Test_Title" in flow or "titre" in flow:
                    validated_flows.append(flow)
                    logger.info(f"Flow {i} validated successfully")
                else:
                    logger.warning(f"Flow {i} missing expected keys. Keys found: {list(flow.keys())}")
                    # Try to fix common naming issues
                    if "title" in flow:
                        flow["Test_Title"] = flow.pop("title")
                    if "steps" in flow:
                        flow["Test_Steps"] = flow.pop("steps")
                    validated_flows.append(flow)
            else:
                logger.error(f"Flow {i} is neither string nor dict: {type(flow)}")
        
        logger.info(f"Validation complete. {len(validated_flows)} valid flows found.")
        return validated_flows


    def process_and_validate_test_flows(self, test_flows, logger):
        """
        Process and validate test flows retrieved from JSON storage.
        
        Args:
            test_flows: Raw test flows data from retrieve_json
            logger: Logger instance for debugging
            
        Returns:
            list: Validated and processed test flows, empty list if processing fails
        """
        try:
            # Debug: Check what we actually retrieved
            logger.info(f"Retrieved test_flows type: {type(test_flows)}")
            if test_flows:
                logger.info(f"test_flows content preview: {str(test_flows)[:200]}...")
                
                # Handle case where test_flows might be a string instead of parsed JSON
                if isinstance(test_flows, str):
                    logger.warning("test_flows is a string, attempting to parse as JSON")
                    try:
                        test_flows = json.loads(test_flows)
                        logger.info("Successfully parsed test_flows from string to object")
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse test_flows as JSON: {e}")
                        return []
                
                # Validate that test_flows is a list
                if not isinstance(test_flows, list):
                    logger.warning(f"test_flows is not a list, it's: {type(test_flows)}")
                    # If it's a dict, try to convert it to the expected format
                    if isinstance(test_flows, dict):
                        test_flows = self.extract_flows_from_dict(test_flows, logger)
                    else:
                        return []
                
                # Validate each flow in test_flows
                if isinstance(test_flows, list):
                    test_flows = self.validate_individual_flows(test_flows, logger)
            
            if not test_flows:
                logger.warning("------------------------ No test flows found after validation, cannot proceed with BLOC II -----------------")
                logger.warning("------------------------ No test flows found after validation, cannot proceed with BLOC II -----------------")
                return []

            # Final validation log
            logger.info(f"Final test_flows validation: type={type(test_flows)}, length={len(test_flows) if isinstance(test_flows, list) else 'N/A'}")
            if test_flows and isinstance(test_flows, list):
                logger.info(f"First flow structure: {test_flows[0] if test_flows else 'Empty'}")
                
            return test_flows

        except Exception as e:
            logger.error(f"Failed to process test flows: {e}")
            return []
        

class USExtractor:
    """Class for extracting US (User Story) information from groupchat results."""
    
    def extract_us_information(self, groupchat_result_2, step):
        """
        Extract US information from groupchat result for a given step.
        
        Args:
            groupchat_result_2: The groupchat result object containing messages
            step (dict): The step dictionary containing step information (must have 'name' key)
            
        Returns:
            list: List of US information dictionaries
        """
        US_List = []
        
        if not hasattr(groupchat_result_2, 'messages') or not groupchat_result_2.messages:
            logger.warning(f"No messages found in groupchat result for step '{step.get('Step_Name', 'Unknown Step')}'")
            return US_List
        
        # Try to extract US information from US_Linker messages
        us_linker_messages = self._get_us_linker_messages(groupchat_result_2.messages)
        
        if us_linker_messages:
            US_List = self._extract_from_us_linker_messages(us_linker_messages, step.get("Step_Name", "Unknown Step"))
        else:
            # Fallback: try to get content from the last message
            US_List = self._extract_from_last_message(groupchat_result_2.messages)
        
        # Validate and log results
        self._validate_and_log_results(US_List, step.get("Step_Name", "Unknown Step"))
        
        return US_List
    
    def _get_us_linker_messages(self, messages):
        """
        Filter messages to get only US_Linker messages.
        
        Args:
            messages: List of message objects
            
        Returns:
            list: Filtered list of US_Linker messages
        """
        return [msg for msg in messages 
                if hasattr(msg, 'source') and 'US_Linker' in msg.source]
    
    def _extract_from_us_linker_messages(self, us_linker_messages, step_name):
        """
        Extract US information from US_Linker messages.
        
        Args:
            us_linker_messages: List of US_Linker message objects
            step_name (str): Name of the current step for logging
            
        Returns:
            list: List of US information dictionaries
        """
        # Use the last US_Linker message as it likely contains the final US list
        last_us_linker_msg = us_linker_messages[-1]
        content = getattr(last_us_linker_msg, 'content', [])
        
        # Since output_content_type = List[USLinker], content should already be a list
        if isinstance(content, list):
            return self._convert_objects_to_dicts(content)
        else:
            # Fallback: try to parse as string (shouldn't happen with typed output)
            return self._parse_string_content(content, step_name)
    
    def _convert_objects_to_dicts(self, content):
        """
        Convert USLinker objects to dictionaries.
        
        Args:
            content: List of objects to convert
            
        Returns:
            list: List of dictionaries
        """
        US_List = []
        for item in content:
            if hasattr(item, 'model_dump'):
                # Pydantic v2 model - use model_dump() method
                US_List.append(item.model_dump())
            elif hasattr(item, 'dict'):
                # Pydantic v1 model - use dict() method
                US_List.append(item.dict())
            elif hasattr(item, '__dict__'):
                # Regular object - convert to dictionary
                US_List.append(item.__dict__)
            elif isinstance(item, dict):
                # Already a dictionary
                US_List.append(item)
            else:
                logger.warning(f"Unexpected item type in US list: {type(item)}")
        
        return US_List
    
    def _parse_string_content(self, content, step_name):
        """
        Parse string content as JSON.
        
        Args:
            content: String content to parse
            step_name (str): Name of the current step for logging
            
        Returns:
            list: Parsed US list or empty list if parsing fails
        """
        if not isinstance(content, str):
            logger.warning(f"Unexpected content type from US_Linker for step '{step_name}': {type(content)}")
            return []
        
        try:
            # Remove any markdown code block formatting if present
            cleaned_content = self._clean_markdown_formatting(content)
            
            # Parse as JSON
            return json.loads(cleaned_content)
        except json.JSONDecodeError:
            logger.warning(f"Could not parse US_Linker content for step '{step_name}': {content}")
            return []
    
    def _clean_markdown_formatting(self, content):
        """
        Remove markdown code block formatting from content.
        
        Args:
            content (str): Content to clean
            
        Returns:
            str: Cleaned content
        """
        content = content.strip()
        if content.startswith('```json'):
            content = content[7:]  # Remove ```json
        if content.endswith('```'):
            content = content[:-3]  # Remove ```
        return content.strip()
    
    def _extract_from_last_message(self, messages):
        """
        Fallback method to extract content from the last message.
        
        Args:
            messages: List of message objects
            step_name (str): Name of the current step for logging
            
        Returns:
            list: Content from last message or empty list
        """
        if not messages:
            return []
        
        last_message = messages[-1]
        content = getattr(last_message, 'content', [])
        
        if isinstance(content, list):
            return content
        else:
            return []
    
    def _validate_and_log_results(self, US_List, step_name):
        """
        Validate US_List structure and log results.
        
        Args:
            US_List: List of US information to validate
            step_name (str): Name of the current step for logging
        """
        if US_List and isinstance(US_List, list):
            # Check if the first item has the expected structure
            if US_List and isinstance(US_List[0], dict) and 'US' in US_List[0]:
                logger.info(f"✅ US linked to test steps generated successfully for step '{step_name}'")
                logger.info(f"⏳ US List for step '{step_name}': {len(US_List)} US found")
                logger.info(f"✅ US linked to test steps generated successfully for step '{step_name}'")
                logger.info(f"⏳ US List for step '{step_name}': {len(US_List)} US found")
            else:
                logger.warning(f"US_List structure is not as expected for step '{step_name}': {US_List}")
        else:
            logger.warning(f"US_List is empty or not a list for step '{step_name}': {US_List}")