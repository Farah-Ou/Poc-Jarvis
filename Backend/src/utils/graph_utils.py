"""
src/utils/graph_utils.py - GraphService implementation
"""
import os
import sys
import shutil
import subprocess
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from dotenv import load_dotenv

from src.utils.file_utils import FileService
from src.utils.config import settings

logger = logging.getLogger(__name__)

class GraphService:
    """Service for managing graph operations including creation, updates, and status management."""
    
    def __init__(self):
        """Initialize GraphService with environment setup."""
        self._setup_environment()
    
    def _setup_environment(self) -> None:
        """Set up environment variables and encoding."""
        os.environ["PYTHONIOENCODING"] = "utf-8"
        
        # Load environment file
        env_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
        load_dotenv(env_file_path)
        
        # Retrieve and validate API key
        api_key = os.getenv("GRAPHRAG_API_KEY")
        if api_key is None:
            raise ValueError("GRAPHRAG_API_KEY environment variable is not set.")
        
        os.environ["GRAPHRAG_API_KEY"] = api_key
        logger.info("Environment setup completed successfully")
    
    def auto_tune_graph_prompt(self, graphs_specific_folder_path: str) -> bool:
        """
        Auto-tune graph prompts for optimal performance.
        
        Args:
            graphs_specific_folder_path: Path to the specific graph folder
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            working_directory = graphs_specific_folder_path
            settings_yaml_path = os.path.join(working_directory, "settings.yaml")
            
            logger.info("Starting auto tuning command launch...")
            
            # Set up the command arguments
            command = [
                'graphrag', 'prompt-tune',
                '--root', working_directory,
                '--config', settings_yaml_path
            ]
            
            logger.debug(f"Executing command: {' '.join(command)}")
            
            # Execute the command and capture the output
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                encoding='utf-8',
                timeout=3600  # 1 hour timeout
            )
            
            logger.info("Command executed, capturing output...")
            
            if result.returncode == 0:
                logger.info("✅ Auto-tuned prompts created successfully!")
                return True
            else:
                logger.error(f"Auto-tune failed with return code {result.returncode}")
                logger.error(f"Error output: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("Auto-tune command timed out")
            return False
        except Exception as e:
            logger.error(f"Error during auto-tune: {str(e)}")
            return False
    
    def _get_combined_file_info(self, graph_name: str, input_folder_path: str) -> Tuple[Optional[str], str]:
        """
        Get the combined file path and name based on graph type.
        
        Args:
            graph_name: Name/type of the graph
            input_folder_path: Path to input folder
            
        Returns:
            Tuple of (output_file_path_from_concat, output_file_name)
        """
        
        logger.info(f"Getting combined file info for graph: {graph_name}")
        logger.debug(f"Input folder path: {input_folder_path}")
        logger.debug(f"settings.GRAPH_CONTEXT: {settings.GRAPH_CONTEXT}")

        file_service = FileService()

        if graph_name == settings.GRAPH_US:
            _, _, output_file_path_from_concat = file_service.concatenate_json_files_to_text(input_folder_path)
            output_file_name = "Combined_US_file.txt"
            
        elif graph_name == settings.GRAPH_CONTEXT:
            output_file_path_from_concat = file_service.concatenate_text_pdf_files(input_folder_path)
            output_file_name = "Combined_Context_file.txt"
            
        elif graph_name == settings.GRAPH_GUIDELINES:
            output_file_path_from_concat = file_service.concatenate_text_pdf_files(input_folder_path)
            output_file_name = "Combined_Guidelines_file.txt"

        elif graph_name == settings.GRAPH_BUSINESS_DOMAIN:
            output_file_path_from_concat = file_service.concatenate_text_pdf_files(input_folder_path)
            output_file_name = "Combined_Business_Domain_file.txt"
            
        elif graph_name == settings.GRAPH_HISTORY_TC:
            _, _, output_file_path_from_concat = file_service.concatenate_json_files_to_text(input_folder_path)
            output_file_name = "Combined_History_TC_file.txt"
        else:
            logger.error(f"Unknown graph type: {graph_name}")
            return None, ""
            
        return output_file_path_from_concat, output_file_name
    
    def _initialize_graphrag_project(self, working_directory: str, graph_folder_path: str) -> bool:
        """
        Initialize GraphRAG project if not already initialized.
        
        Args:
            working_directory: Working directory path
            graph_folder_path: Graph folder path for env file copying
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            settings_yaml_path = os.path.join(working_directory, "settings.yaml")
            
            if not os.path.exists(settings_yaml_path):
                logger.info("-------- Starting GraphRAG initialization...")
                subprocess.run(
                    ["graphrag", "init", "--root", working_directory], 
                    check=True,
                    timeout=300  # 5 minute timeout
                )
                logger.info("✅ GraphRAG initialization completed successfully")
            else:
                logger.info(f"Project at {working_directory} already initialized (settings.yaml found). Skipping init.")
                
                # Copy environment file
                logger.info("Copying GraphRAG key to correct environment")
                env_file_initial_path = os.path.join(os.path.dirname(graph_folder_path), ".env")
                env_file_target_path = os.path.join(working_directory, ".env")
                
                logger.debug(f"Source env file: {env_file_initial_path}")
                logger.debug(f"Target env file: {env_file_target_path}")
                
                if os.path.exists(env_file_initial_path):
                    shutil.copyfile(env_file_initial_path, env_file_target_path)
                    logger.info("GraphRAG key copied successfully")
                else:
                    logger.warning(f"Source env file not found: {env_file_initial_path}")
                    
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"GraphRAG initialization failed: {str(e)}")
            return False
        except subprocess.TimeoutExpired:
            logger.error("GraphRAG initialization timed out")
            return False
        except Exception as e:
            logger.error(f"Error during GraphRAG initialization: {str(e)}")
            return False
    
    def _setup_custom_tc_prompts(self, working_directory: str, settings_yaml_path: str) -> bool:
        """
        Set up custom prompts for TC history graph.
        
        Args:
            working_directory: Working directory path
            settings_yaml_path: Path to settings.yaml file
            
        Returns:
            bool: True if successful, False otherwise
        """
        file_service = FileService()

        try:
            logger.info("📌 Starting tailored history graph prompt setup...")
            
            # base_dir_parent = os.path.abspath(os.path.normpath(".."))
            source_folder_custom_prompts_tc = settings.Custom_prompts_tc
     
            target_folder_tc_prompts = os.path.join(working_directory, "prompts")
          
            custom_yaml_source_path = os.path.join(
                settings.Custom_yaml_tc, 
                "settings.yaml"
            )
            
            logger.debug(f"Source custom prompts: {source_folder_custom_prompts_tc}")
            logger.debug(f"Target prompts folder: {target_folder_tc_prompts}")
            logger.debug(f"Custom YAML source: {custom_yaml_source_path}")
            
            if not os.path.exists(source_folder_custom_prompts_tc):
                logger.error(f"Source custom prompts folder not found: {source_folder_custom_prompts_tc}")
                return False
                
            if not os.path.exists(custom_yaml_source_path):
                logger.error(f"Custom YAML file not found: {custom_yaml_source_path}")
                return False
            
            # Copy custom prompts and settings
            file_service.copy_folder_contents(source_folder_custom_prompts_tc, target_folder_tc_prompts)
            shutil.copy(custom_yaml_source_path, settings_yaml_path)
            
            logger.info("✅ Manual tailored TC tune graph prompt completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error setting up custom TC prompts: {str(e)}")
            return False
    
    def _run_graphrag_indexing(self, working_directory: str) -> bool:
        """
        Run GraphRAG indexing process.
        
        Args:
            working_directory: Working directory path
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info("------- Starting GraphRAG indexing...")
            subprocess.run(
                ["graphrag", "index", "--root", working_directory], 
                check=True,
                timeout=7200  # 2 hour timeout
            )
            logger.info("✅ GraphRAG indexing completed successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"GraphRAG indexing failed: {str(e)}")
            return False
        except subprocess.TimeoutExpired:
            logger.error("GraphRAG indexing timed out")
            return False
        except Exception as e:
            logger.error(f"Error during GraphRAG indexing: {str(e)}")
            return False
    
    def _copy_graph_artifacts(self, working_directory: str, artifacts_graph_visualizer_path: str, graph_name: str) -> None:
        """
        Copy graph artifacts to visualizer directory.
        
        Args:
            working_directory: Working directory path
            artifacts_graph_visualizer_path: Target artifacts path
            graph_name: Name of the graph
        """
        try:
            graph_parquets = os.path.join(working_directory, "output")
            
            if os.path.exists(graph_parquets) and any(os.scandir(graph_parquets)):
                for file_name in os.listdir(graph_parquets):
                    source_path = os.path.join(graph_parquets, file_name)
                    target_path = os.path.join(artifacts_graph_visualizer_path, file_name)
                    
                    if os.path.isfile(source_path):
                        os.makedirs(os.path.dirname(target_path), exist_ok=True)
                        shutil.copy2(source_path, target_path)
                        logger.debug(f"Copied: {source_path} -> {target_path}")
                        
                logger.info(f"----- Graph artifacts copied to {artifacts_graph_visualizer_path}")
            else:
                logger.warning(f"Skipping visual graph artifacts copy for {graph_name} as no output parquets found in {graph_parquets}")
                
        except Exception as e:
            logger.error(f"Error copying graph artifacts: {str(e)}")
    def create_folder():
        pass
    def create_graph(
        self,
        graph_folder_path: str,
        graphs_specific_folder_path: str,
        graph_name: str,
        input_folder_path: str,
        output_folder: str,
        artifacts_graph_visualizer_path: str
    ) -> bool:
        """
        Create a new graph folder with all necessary components.
        
        Args:
            graph_folder_path: Base graph folder path
            graphs_specific_folder_path: Specific graph folder path
            graph_name: Name/type of the graph
            input_folder_path: Path to input data
            output_folder: Output folder name
            artifacts_graph_visualizer_path: Path for visualization artifacts
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            working_directory = graphs_specific_folder_path
            
            # Ensure output folder exists
            os.makedirs(os.path.join(working_directory, output_folder), exist_ok=True)
            
            # Ensure input folder exists
            if not os.path.isdir(input_folder_path):
                os.makedirs(input_folder_path, exist_ok=True)
                logger.info(f"Created input folder: {input_folder_path}")
            
            # Get combined file information
            output_file_path_from_concat, output_file_name = self._get_combined_file_info(graph_name, input_folder_path)
            
            if not output_file_name:
                logger.error(f"Failed to determine output file name for graph: {graph_name}")
                return False
            
            # Define the path for the output file in the output folder
            graphrag_input_target_path = os.path.join(working_directory, output_folder, output_file_name)
            
            # Check if we have valid concatenated data
            if (output_file_path_from_concat and 
                os.path.exists(output_file_path_from_concat) and 
                os.path.getsize(output_file_path_from_concat) > 0):
                
                # Copy the combined file to the output folder for graphrag
                shutil.copy(output_file_path_from_concat, graphrag_input_target_path)
                logger.info(f"Source file {output_file_path_from_concat} copied to graphrag input {graphrag_input_target_path}")
                
                # Initialize GraphRAG project
                if not self._initialize_graphrag_project(working_directory, graph_folder_path):
                    return False
                
                settings_yaml_path = os.path.join(working_directory, "settings.yaml")
                
                # Handle different graph types
                if graph_name == settings.GRAPH_HISTORY_TC:
                    if not self._setup_custom_tc_prompts(working_directory, settings_yaml_path):
                        return False
                else:
                    logger.info("------ using gpt-4o-mini for indexing and tuning ...")
                    custom_yaml_source_path = os.path.join(
                        settings.Custom_yaml_light_model, 
                        "settings.yaml"
                    )
                    shutil.copy(custom_yaml_source_path, settings_yaml_path)
                    logger.info("------ Starting auto tune graph prompt...")
                    if not self.auto_tune_graph_prompt(str(graphs_specific_folder_path)):
                        logger.error("Auto-tune failed, but continuing with indexing...")
                    else:
                        logger.info("✅ Auto tune graph prompt completed successfully")
                
                # Run indexing
                if not self._run_graphrag_indexing(working_directory):
                    return False
                
                logger.info(f"✅ Graph created in {working_directory}")
                
                # Copy visualization artifacts
                self._copy_graph_artifacts(working_directory, artifacts_graph_visualizer_path, graph_name)
                
                return True
                
            else:
                logger.warning(f"Skipping graph creation for {graph_name} as source data is empty or missing")
                
                # Still copy existing artifacts if available
                self._copy_graph_artifacts(working_directory, artifacts_graph_visualizer_path, graph_name)
                return False
                
        except Exception as e:
            logger.error(f"Error creating graph folder: {str(e)}")
            return False
    
    def graph_update(
        self,
        graphs_specific_folder_path: str,
        graph_name: str,
        input_folder_path: str,
        artifacts_graph_visualizer_path: str,
        imported_source_updated_tickets_path: str
    ) -> str:
        """
        Update an existing graph with new data.
        
        Args:
            
            graph_folder_path: Base graph folder path
            graphs_specific_folder_path: Specific graph folder path
            graph_name: Name/type of the graph
            input_folder_path: Path to input data
            output_folder: Output folder name
            artifacts_graph_visualizer_path: Path for visualization artifacts
            
        Returns:
            str: Result message or error description
        """
        try:
            working_directory = graphs_specific_folder_path
            
            # Construct the output folder path
            graphrag_input_folder = os.path.join(working_directory, "input")
            
            # List all .txt files in the input folder
            txt_files = [f for f in os.listdir(input_folder_path) if f.endswith(".txt")]
            
            if not txt_files:
                raise FileNotFoundError(f"No .txt file found in {input_folder_path}")
            
            # Use the first .txt file
            graphrag_input_target_path = os.path.join(graphrag_input_folder, txt_files[0])
            # final_input_folder_path = os.path.join(input_folder_path, txt_files[0])
            
            logger.warning(f"GraphRAG input target path: {graphrag_input_target_path}")
            logger.warning(f"Final input folder path: {imported_source_updated_tickets_path}")
            
            # Archive existing files
            
            if graph_name ==  str(settings.GRAPH_HISTORY_TC) :
                archived_graph_files_directory = settings.ARCHIVED_GRAPH_TC_FILES_DIRECTORY
            elif graph_name == str(settings.GRAPH_US):
                archived_graph_files_directory = settings.ARCHIVED_CURRENT_US_FILES_DIRECTORY

            file_service = FileService()

            # Move old files to archive
            file_service.move_folder_contents(graphrag_input_folder, archived_graph_files_directory)
            logger.warning(f"Moved contents from {graphrag_input_folder} to {archived_graph_files_directory}")
            
            # Copy new file
            if (imported_source_updated_tickets_path and 
                os.path.exists(imported_source_updated_tickets_path) and 
                os.path.getsize(imported_source_updated_tickets_path) > 0):
                
                shutil.copy(imported_source_updated_tickets_path, graphrag_input_target_path)
                logger.warning(f"Source file {imported_source_updated_tickets_path} copied to graphrag input {graphrag_input_target_path}")
            else:
                return "Error: Source file is empty or does not exist"
            
            # Run update command

            logger.warning("Starting GraphRAG update command...")
            working_directory_str = str(working_directory)
            command = ['graphrag', 'update', '--root', working_directory_str]

            logger.debug(f"Executing command: {' '.join(command)}")
            
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                encoding='utf-8',
                timeout=7200  # 2 hour timeout
            )

            logger.warning("GraphRAG update command executed")

            if result.returncode == 0:
                logger.warning("✅ Graph updated successfully!")

                # Copy updated artifacts
                self._copy_graph_artifacts(working_directory, artifacts_graph_visualizer_path, graph_name)
                
                return result.stdout
            else:
                error_msg = f"GraphRAG update failed with return code {result.returncode}: {result.stderr}"
                logger.error(error_msg)
                return f"Error: {result.stderr}"
                
        except subprocess.TimeoutExpired:
            error_msg = "GraphRAG update command timed out"
            logger.error(error_msg)
            return f"Error: {error_msg}"
        except FileNotFoundError as e:
            logger.error(f"File not found error: {str(e)}")
            return f"Error: {str(e)}"
        except Exception as e:
            error_msg = f"Error during graph update: {str(e)}"
            logger.error(error_msg)
            return f"Error: {error_msg}"