"""
src/utils/file_utils.py - File management service
"""
import os
import shutil
import stat
import json
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from fastapi import UploadFile, HTTPException
import logging
import aiofiles
from datetime import datetime
import uuid
import pandas as pd
import fitz 

logger = logging.getLogger(__name__)
from src.utils.config import settings

class FileService:
    """Service for file operations and management"""
    
    def __init__(self):
        self.allowed_extensions = {'.xlsx', '.xls', '.json', '.txt', '.csv', '.pdf', '.docx', '.doc'}
        self.max_file_size = 50 * 1024 * 1024 
    
    async def save_file(
        self,
        file: UploadFile,
        destination_path: Path,
        filename: Optional[str] = None
    ) -> Path:
        """
        Save an uploaded file to the specified destination.
        
        Args:
            file: FastAPI UploadFile object
            destination_path: Directory path to save the file
            filename: Optional custom filename, if not provided uses original filename
            
        Returns:
            Path: Full path to the saved file
            
        Raises:
            HTTPException: If file save fails
        """
        try:
            # Validate file
            if not file.filename:
                raise HTTPException(status_code=400, detail="No filename provided")
            
            # Check file extension
            file_extension = Path(file.filename).suffix.lower()
            if file_extension not in self.allowed_extensions:
                raise HTTPException(
                    status_code=400,
                    detail=f"File type not allowed. Allowed types: {', '.join(self.allowed_extensions)}"
                )
            
            # Check file size
            file_content = await file.read()
            if len(file_content) > self.max_file_size:
                raise HTTPException(
                    status_code=400,
                    detail=f"File too large. Maximum size: {self.max_file_size / (1024*1024):.1f}MB"
                )
            
            # Reset file pointer
            await file.seek(0)
            
            # Ensure destination directory exists
            destination_path.mkdir(parents=True, exist_ok=True)
            
            # Use provided filename or generate unique filename if file already exists
            if filename:
                saved_filename = filename
            else:
                base_name = Path(file.filename).stem
                extension = Path(file.filename).suffix
                counter = 1
                saved_filename = file.filename
                
                while (destination_path / saved_filename).exists():
                    saved_filename = f"{base_name}_{counter}{extension}"
                    counter += 1
            
            # Save file
            file_path = destination_path / saved_filename
            
            async with aiofiles.open(file_path, 'wb') as f:
                content = await file.read()
                await f.write(content)
            
            logger.info(f"File saved successfully: {saved_filename}")
            return file_path
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error saving file: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to save file: {str(e)}"
            )
    
    async def upload_files(
        self,
        files: List[UploadFile],
        upload_dir: str,
        allowed_extensions: List[str],
        category: str,
        jira_project_key: str = None,
        user_id: str = None
    ) -> Dict[str, List[str]]:
        """
        Upload files and encode jira_project_key and user_id into the filename.
        Format: {original_name}__{project}__{user}__.{ext}
        """
        saved_files = []
        invalid_files = []

        os.makedirs(upload_dir, exist_ok=True)

        # Clean and shorten project/user if needed
        safe_project = (jira_project_key or "NO_PROJECT")[:20]  # Limit length
        safe_user = (user_id or "UNKNOWN")[:15]

        for file in files:
            filename = file.filename.strip()
            ext = os.path.splitext(filename)[1].lower()

            if ext not in allowed_extensions:
                invalid_files.append(f"{filename} (unsupported extension)")
                continue

            try:
                # Extract name without extension
                name_without_ext = os.path.splitext(filename)[0]

                # Sanitize to avoid filesystem issues
                name_without_ext = "".join(c for c in name_without_ext if c.isalnum() or c in " _-.")
                safe_project_clean = "".join(c for c in safe_project if c.isalnum())
                safe_user_clean = "".join(c for c in safe_user if c.isalnum())

                # Build new filename
                timestamp = datetime.now().strftime("%Y%m%d")
                new_filename = f"{name_without_ext}__{safe_project_clean}__{safe_user_clean}__{timestamp}__{ext}"
                file_path = os.path.join(upload_dir, new_filename)

                # Avoid overwrites with timestamp if needed
                counter = 1
                original_new_filename = new_filename
                while os.path.exists(file_path):
                    name_part = f"{name_without_ext}__{safe_project_clean}__{safe_user_clean}"
                    new_filename = f"{name_part}_({counter})__{ext}"
                    file_path = os.path.join(upload_dir, new_filename)
                    counter += 1

                # Save file
                with open(file_path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)

                saved_files.append(new_filename)
                logger.info(f"Saved file with embedded metadata: {new_filename}")

            except Exception as e:
                logger.error(f"Failed to save file {filename}: {str(e)}")
                invalid_files.append(f"{filename}: {str(e)}")

        return {
            "saved_files": saved_files,
            "invalid_files": invalid_files
        }
    def delete_file(self, file_path: Path) -> bool:
        """
        Delete a file.
        
        Args:
            file_path: Path to the file to delete
            
        Returns:
            bool: True if deleted, False if not found
        """
        try:
            if file_path.exists():
                file_path.unlink()
                logger.info(f"File deleted: {file_path}")
                return True
            else:
                logger.warning(f"File not found for deletion: {file_path}")
                return False
        except Exception as e:
            logger.error(f"Error deleting file {file_path}: {e}")
            raise
    def move_file(self, source_path, destination_path) -> bool:
        """
        Move a file from source to destination.
        
        Args:
            source_path: Source file path (str or Path)
            destination_path: Destination file path (str or Path)
            
        Returns:
            bool: True if moved successfully
        """
        try:
            # Convert to Path objects if they're strings
            source_path = Path(source_path) if isinstance(source_path, str) else source_path
            destination_path = Path(destination_path) if isinstance(destination_path, str) else destination_path
            
            if not source_path.exists():
                logger.warning(f"Source file not found: {source_path}")
                return False
            
            # Ensure destination directory exists
            destination_path.parent.mkdir(parents=True, exist_ok=True)
            
            shutil.move(str(source_path), str(destination_path))
            logger.info(f"File moved from {source_path} to {destination_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error moving file from {source_path} to {destination_path}: {e}")
            raise

    def move_folder_contents(self, src_folder: str, dest_folder: str) -> None:
        """
        Move files from src_folder to dest_folder, overwriting existing files
        and making read-only files writable if needed.

        Args:
            src_folder: Path to source directory
            dest_folder: Path to destination directory

        Raises:
            FileNotFoundError: If source folder doesn't exist
            Exception: For any file-specific errors during the move
        """
        if not os.path.exists(src_folder):
            raise FileNotFoundError(f"Source folder does not exist: {src_folder}")
        
        os.makedirs(dest_folder, exist_ok=True)

        for item in os.listdir(src_folder):
            src_path = os.path.join(src_folder, item)
            dest_path = os.path.join(dest_folder, item)

            if os.path.isfile(src_path):
                try:
                    self.move_file(src_path, dest_path)
                except Exception as e:
                    logger.error(f"Failed to move {item}: {e}")

    def list_files(self, directory_path: Path, extension_filter: Optional[str] = None) -> List[Path]:
        """
        List files in a directory with optional extension filter.
        
        Args:
            directory_path: Path to directory
            extension_filter: Optional file extension to filter by (e.g., '.pdf')
            
        Returns:
            List[Path]: List of file paths
        """
        try:
            if not directory_path.exists():
                return []
            
            files = []
            for file_path in directory_path.iterdir():
                if file_path.is_file():
                    if extension_filter is None or file_path.suffix.lower() == extension_filter.lower():
                        files.append(file_path)
            
            return sorted(files)
            
        except Exception as e:
            logger.error(f"Error listing files in {directory_path}: {e}")
            return []
    
    def get_file_info(self, file_path: Path) -> Dict[str, Any]:
        """
        Get file information.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dict with file information
        """
        try:
            if not file_path.exists():
                return {"exists": False}
            
            stat = file_path.stat()
            return {
                "exists": True,
                "name": file_path.name,
                "size": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_ctime),
                "modified": datetime.fromtimestamp(stat.st_mtime),
                "extension": file_path.suffix.lower()
            }
            
        except Exception as e:
            logger.error(f"Error getting file info for {file_path}: {e}")
            return {"exists": False, "error": str(e)}

    def copy_folder_contents(self, src_folder: str, dest_folder: str) -> None:
        """
        Copy only files from src_folder to dest_folder, overwriting if they exist.
        
        Args:
            src_folder: Source folder path
            dest_folder: Destination folder path
        """
        if not os.path.exists(src_folder):
            logger.warning(f"Source folder does not exist: {src_folder}")
            logger.info(f"Source folder does not exist: {src_folder}")
            return
        
        os.makedirs(dest_folder, exist_ok=True)
        
        for item in os.listdir(src_folder):
            src_path = os.path.join(src_folder, item)
            dest_path = os.path.join(dest_folder, item)
            
            # Only process files (skip directories)
            if os.path.isfile(src_path):
                try:
                    # Check if destination exists and handle read-only files
                    if os.path.exists(dest_path):
                        # Make file writable if it's read-only
                        if not os.access(dest_path, os.W_OK):
                            os.chmod(dest_path, stat.S_IWRITE)
                        logger.info(f"Overwriting existing file: {dest_path}")
                    
                    # Copy the file (this will overwrite automatically)
                    shutil.copy2(src_path, dest_path)
                    logger.info(f" Successfully copied: {item}")
                    logger.info(f"Successfully copied: {item}")
                    
                except PermissionError as e:
                    error_msg = f"❌ Permission error copying {item}: {e}"
                    logger.info(error_msg)
                    logger.error(error_msg)
                except FileNotFoundError as e:
                    error_msg = f"❌ File not found error: {e}"
                    logger.info(error_msg)
                    logger.error(error_msg)
                except Exception as e:
                    error_msg = f"❌ Error copying {item}: {e}"
                    logger.info(error_msg)
                    logger.error(error_msg)

    def excel_to_json(self, input_folder_path: str) -> None:
        """
        Convert Excel files to JSON format in the same directory.
        Note: This method should be implemented based on your existing excel_to_json logic.
        
        Args:
            input_folder_path: Path to folder containing Excel files
        """
        # Placeholder for excel_to_json implementation
        # This should be implemented based on your existing logic
        logger.info(f"Converting Excel files to JSON in: {input_folder_path}")
        pass

    def concatenate_json_files_to_text(self, input_folder_path: str) -> Tuple[pd.DataFrame, str, Optional[str]]:
        """
        Concatenate JSON files to text format with comprehensive error handling.
        
        Args:
            input_folder_path: Path to folder containing JSON files
            
        Returns:
            Tuple of (DataFrame, json_output_path, txt_output_path)
        """
        combined_data = []
        output_file_path_json = ""
        df = pd.DataFrame()  # Initialize df
        
        

        input_path_str = str(input_folder_path)

        parent_path =  os.path.dirname(os.path.dirname(input_folder_path))
        parent_path_str = str(parent_path)
        logger.warning("input_folder_path: ", input_folder_path)
        logger.warning("parent_path: ", parent_path) 



        if (parent_path_str == str(settings.CURRENT_US_PATH) or parent_path_str == str(settings.US_PATH_TO_GENERATE)):
            txt_file_name = "combined_US_files.txt"
        elif parent_path_str == str(settings.HISTORY_TC_PATH):
            txt_file_name = "combined_TC_files.txt"
        else:
            # This should not happen based on your use case, but adding for safety
            logger.warning(f"🚨 Warning: Unexpected input_folder_path: {input_path_str}")
            logger.warning(f"🚨 Expected paths: {str(settings.CURRENT_US_PATH)} or {str(settings.US_PATH_TO_GENERATE)} or {str(settings.HISTORY_TC_PATH)}")
            txt_file_name = "combined_files.txt"  # Fallback

        # Define the output path where the combined text file will be stored
        output_file_path_txt = os.path.join(input_folder_path, txt_file_name)
        # Tentatively set to None, will be updated if a file is successfully written
        final_output_txt_path = None
        
        nb = 0

        # Transform excel files into json to be processed
        self.excel_to_json(input_folder_path)

        # Loop through all files in the input folder
        for file_name in os.listdir(input_folder_path):
            # Only process JSON files
            if file_name.endswith(".json"):
                nb += 1
                file_path = os.path.join(input_folder_path, file_name)
                
                # Open and read each JSON file
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if isinstance(data, list):  # Ensure data is a list for extend
                            combined_data.extend(data)
                        elif isinstance(data, dict):  # Handle case where a single JSON object is loaded
                            combined_data.append(data)
                except json.JSONDecodeError:
                    logger.warning(f"Warning: Could not decode JSON from {file_path}. Skipping.")
                    logger.warning(f"Could not decode JSON from {file_path}")
                    nb -= 1  # Decrement count of valid JSON files
                except Exception as e:
                    logger.error(f"Warning: Error reading {file_path}: {e}. Skipping.")
                    logger.error(f"Error reading {file_path}: {e}")
                    nb -= 1

        if nb > 0:  # Proceed only if valid JSON files were found and processed
            if nb != 1:
                # Write the combined content to a new JSON file
                output_file_path_json = os.path.join(input_folder_path, "Combined_json_file.json")
                with open(output_file_path_json, 'w', encoding='utf-8') as output_file:
                    json.dump(combined_data, output_file, ensure_ascii=False, indent=4)
                logger.info(f"Ensemble json US or TC concatenated and saved to path {output_file_path_json}")
                
                ## Turn into txt combined file
                if os.path.exists(output_file_path_json) and os.path.getsize(output_file_path_json) > 0:
                    try:
                        df = pd.read_json(output_file_path_json)
                    except ValueError:  # Handles empty or invalid JSON
                        logger.warning(f"Warning: Combined JSON file {output_file_path_json} is empty or invalid. Cannot create DataFrame.")
                        logger.warning(f"Combined JSON file {output_file_path_json} is empty or invalid")
                        df = pd.DataFrame()  # Ensure df is an empty DataFrame
                else:
                    df = pd.DataFrame()
            
            elif nb == 1:  # Exactly one valid JSON file
                # file_path here refers to the last JSON file processed in the loop
                if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                    try:
                        df = pd.read_json(file_path)
                    except ValueError:
                        logger.warning(f"Warning: Single JSON file {file_path} is empty or invalid. Cannot create DataFrame.")
                        logger.warning(f"Single JSON file {file_path} is empty or invalid")
                        df = pd.DataFrame()
                else:
                    df = pd.DataFrame()

            if not df.empty:
                content_as_text = df.to_string(index=False)
                if content_as_text.strip():  # Ensure content is not just whitespace
                    with open(output_file_path_txt, 'w', encoding='utf-8') as f:
                        f.write(content_as_text)
                    logger.info(f"Textual US saved to path {output_file_path_txt} from JSON data.")
                    logger.info(f"Textual US saved to path {output_file_path_txt}")
                    final_output_txt_path = output_file_path_txt  # Mark as successfully written
                else:
                    logger.warning(f"DataFrame was empty or produced empty string. No initial text file written from JSONs to {output_file_path_txt}")
                    logger.warning("DataFrame was empty or produced empty string")
            else:
                logger.error(f"No DataFrame created from JSONs. No initial text file written to {output_file_path_txt}")
                logger.warning("No DataFrame created from JSONs")

        else:
            logger.error(f"Aucun fichier json valide n'existe dans le chemin fourni {input_folder_path}.")
            logger.warning(f"No valid JSON files in {input_folder_path}")
        
        ## Appending text files from created json text and jira import
        # List the files in the input folder
        input_files = os.listdir(input_folder_path)
        # Include the potentially just-created file if it's valid
        existing_txt_files = [f for f in input_files if f.endswith('.txt') and f != os.path.basename(output_file_path_txt)]
        
        source_txt_files_for_concatenation = []
        if final_output_txt_path and os.path.exists(final_output_txt_path) and os.path.getsize(final_output_txt_path) > 0:
            source_txt_files_for_concatenation.append(os.path.basename(final_output_txt_path))
        
        txt_files_in_dir = [file for file in input_files if file.endswith('.txt')]

        if len(txt_files_in_dir) >= 1:  # If there is at least one .txt file
            other_txt_files = [f for f in input_files if f.endswith('.txt') and f != os.path.basename(output_file_path_txt)]

            if final_output_txt_path:  # JSONs created Combined_us_file.txt
                if other_txt_files:
                    with open(final_output_txt_path, 'a', encoding='utf-8') as output_file:  # Append mode
                        file_to_append_path = os.path.join(input_folder_path, other_txt_files[0])
                        if os.path.exists(file_to_append_path) and os.path.getsize(file_to_append_path) > 0:
                            with open(file_to_append_path, 'r', encoding='utf-8') as input_file:
                                content = input_file.read()
                                if content.strip():
                                    output_file.write("\n" + content)  # Add newline and content
                                    logger.info(f"Appended {other_txt_files[0]} to {final_output_txt_path}")
                                    logger.info(f"Appended {other_txt_files[0]} to {final_output_txt_path}")
                                else:
                                    logger.warning(f"{other_txt_files[0]} is empty, not appended.")
                        else:
                            logger.error(f"{other_txt_files[0]} is empty or does not exist, not appended.")
            
            elif len(other_txt_files) >= 1:  # JSONs did NOT create a file, but other .txt exist
                # Use the first other text file as the base if it has content
                first_other_txt_path = os.path.join(input_folder_path, other_txt_files[0])
                if os.path.exists(first_other_txt_path) and os.path.getsize(first_other_txt_path) > 0:
                    shutil.copy(first_other_txt_path, output_file_path_txt)
                    final_output_txt_path = output_file_path_txt
                    logger.info(f"Using {other_txt_files[0]} as base for {output_file_path_txt}")
                    logger.info(f"Using {other_txt_files[0]} as base for {output_file_path_txt}")
                    if len(other_txt_files) >= 2:  # Append the second if it exists and has content
                        second_other_txt_path = os.path.join(input_folder_path, other_txt_files[1])
                        if os.path.exists(second_other_txt_path) and os.path.getsize(second_other_txt_path) > 0:
                            with open(final_output_txt_path, 'a', encoding='utf-8') as output_file:
                                with open(second_other_txt_path, 'r', encoding='utf-8') as input_file:
                                    content = input_file.read()
                                    if content.strip():
                                        output_file.write("\n" + content)
                                        logger.info(f"Appended {other_txt_files[1]} to {final_output_txt_path}")
                                        logger.info(f"Appended {other_txt_files[1]} to {final_output_txt_path}")
                                    else:
                                        logger.warning(f"{other_txt_files[1]} is empty, not appended.")
                        else:
                            logger.warning(f"Second other text file {other_txt_files[1]} is empty or does not exist, not appended.")
                else:
                    logger.warning(f"First other .txt file {other_txt_files[0]} is empty. No base for concatenation.")
            else:
                logger.warning("No JSON content and not enough other text files to process.")

        else:  # nb is 0 and also no other text files to process from the start
            logger.warning("No JSON files processed and no other text files found to create a combined file.")

        # Final check on the designated output file
        if final_output_txt_path and os.path.exists(final_output_txt_path) and os.path.getsize(final_output_txt_path) > 0:
            pass
        else:
            final_output_txt_path = None  # Explicitly set to None if file is empty/doesn't exist
            logger.error(f"Final combined file {output_file_path_txt} is empty or was not created.")
            logger.warning(f"Final combined file {output_file_path_txt} is empty or was not created")

        return df, output_file_path_json, final_output_txt_path

    def concatenate_text_pdf_files(self, input_folder_path: str) -> str:
        """
        Concatenate text and PDF files into a single combined file.

        Args:
            input_folder_path: Path to folder containing text and PDF files

        Returns:
            str: Path to the combined file
        """
        txt_file_name = None
        description = None

        parent_path = os.path.dirname(input_folder_path)
        logger.warning("input_folder_path: ", input_folder_path)
        logger.warning("parent_path: ", parent_path)  

        if parent_path == str(settings.INTERNAL_COMPANY_GUIDELINES_PATH):
            txt_file_name = "Combined_Guidelines_file.txt"
            description = "Internal Company Guidelines"
        elif parent_path == str(settings.BUSINESS_DOMAIN_PATH):
            txt_file_name = "Combined_Business_Domain_file.txt"
            description = "Business Domain"
        elif parent_path == str(settings.PROJECT_SPEC_PATH):
            txt_file_name = "Combined_Context_file.txt"
            description = "Project Specifications"
        else:
            logger.warning(f"Unknown folder path: {parent_path}. Skipping concatenation.")
            return ""
        

        combined_file_path = os.path.join(input_folder_path, txt_file_name)
        logger.info(f"📄 Starting concatenation for: {description}")
        logger.debug(f"Input folder: {input_folder_path}")
        logger.debug(f"Output combined file: {combined_file_path}")

        try:
            file_count = 0
            if txt_file_name:
                with open(combined_file_path, 'w', encoding="utf-8") as combined_file:
                    for entry_name in os.listdir(input_folder_path):
                        input_path = os.path.join(input_folder_path, entry_name)

                        # Process .txt files
                        if os.path.isfile(input_path) and entry_name.lower().endswith('.txt'):
                            try:
                                with open(input_path, 'r', encoding="utf-8") as input_file:
                                    content = input_file.read()
                                    combined_file.write(content + "\n")
                                logger.info(f" Added text file: {entry_name} ({len(content)} chars)")
                                file_count += 1
                            except Exception:
                                logger.exception(f"❌ Failed to read text file: {entry_name}")

                        # Process .pdf files
                        elif os.path.isfile(input_path) and entry_name.lower().endswith('.pdf'):
                            try:
                                with fitz.open(input_path) as pdf_file:
                                    for page_num in range(pdf_file.page_count):
                                        page = pdf_file.load_page(page_num)
                                        combined_file.write(page.get_text("text") + "\n")
                                logger.info(f" Added PDF file: {entry_name} ({pdf_file.page_count} pages)")
                                file_count += 1
                            except Exception:
                                logger.exception(f"❌ Failed to read PDF file: {entry_name}")

                logger.info(f"🎯 Concatenation complete for {description}: {file_count} files added.")
            else:
                logger.info("Skipping concatenation: JSON file processing for TC/US pipeline.")

            return combined_file_path

        except Exception:
            logger.exception(f"Critical error creating combined file for {description}")
            raise


    def save_uploaded_files(self, files: List[UploadFile], destination_path: str) -> Tuple[List[str], List[str]]:
        """
        Legacy function for backward compatibility.
        Save uploaded files to destination path and return saved/invalid file lists.
        
        Args:
            files: List of UploadFile objects
            destination_path: String path to destination directory
            
        Returns:
            Tuple of (saved_files, invalid_files) lists
        """
        saved_files = []
        invalid_files = []
        
        # Ensure destination directory exists
        os.makedirs(destination_path, exist_ok=True)
        
        for file in files:
            try:
                # Validate file extension
                if not file.filename.lower().endswith(('.pdf', '.txt')):
                    invalid_files.append(f"{file.filename}: Only PDF and TXT files are allowed")
                    continue
                
                # Generate unique filename if needed
                base_name = os.path.splitext(file.filename)[0]
                extension = os.path.splitext(file.filename)[1]
                counter = 1
                filename = file.filename
                
                while os.path.exists(os.path.join(destination_path, filename)):
                    filename = f"{base_name}_{counter}{extension}"
                    counter += 1
                
                # Save file
                file_path = os.path.join(destination_path, filename)
                with open(file_path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)
                
                saved_files.append(filename)
                logger.info(f"File saved: {filename}")
                
            except Exception as e:
                invalid_files.append(f"{file.filename}: {str(e)}")
                logger.error(f"Error saving file {file.filename}: {e}")
            finally:
                file.file.close()
        
        return saved_files, invalid_files
    
    def excel_to_json(self, directory_path):
        """
        Converts the first sheet of all Excel files in a directory to JSON files.
        
        Parameters:
            directory_path (str): Path to the directory containing Excel files.
            
        Returns:
            None
        """
        # Ensure the provided path exists
        if not os.path.exists(directory_path):
            logger.warning(f"The directory {directory_path} does not exist.")
            logger.error(f"Directory does not exist: {directory_path}")
            return
            
        # Iterate over files in the directory
        for file_name in os.listdir(directory_path):
            if file_name.endswith(('.xls', '.xlsx')):
                file_path = os.path.join(directory_path, file_name)
                
                # Load the first sheet of the Excel file
                try:
                    data = pd.read_excel(file_path, sheet_name=0)  # Read only the first sheet
                    # Replace NaN values with empty strings
                    data = data.fillna("")
                    json_data = data.to_dict(orient='records')
                    
                    # Write to a JSON file
                    json_file_name = os.path.splitext(file_name)[0] + '.json'
                    json_file_path = os.path.join(directory_path, json_file_name)
                    
                    with open(json_file_path, 'w', encoding='utf-8') as json_file:
                        json.dump(json_data, json_file, indent=4, ensure_ascii=False)
                    
                    logger.info(f"Converted {file_name} (first sheet only) to {json_file_name}")
                    logger.info(f"Converted {file_name} to {json_file_name}")
                except Exception as e:
                    logger.error(f"Failed to process {file_name}: {e}")
                    logger.error(f"Failed to process {file_name}: {e}")

    def excel_to_json_multiple_sheets(self, directory_path):
        """
        Converts all Excel files in a directory to JSON files.
        
        Parameters:
            directory_path (str): Path to the directory containing Excel files.
        
        Returns:
            None
        """
        # Ensure the provided path exists
        if not os.path.exists(directory_path):
            logger.warning(f"The directory {directory_path} does not exist.")
            logger.error(f"Directory does not exist: {directory_path}")
            return

        # Iterate over files in the directory
        for file_name in os.listdir(directory_path):
            if file_name.endswith(('.xls', '.xlsx')):
                file_path = os.path.join(directory_path, file_name)
                
                # Load Excel file
                try:
                    excel_data = pd.read_excel(file_path, sheet_name=None)  # Read all sheets
                    json_data = {}
                    
                    # Process each sheet
                    for sheet_name, data in excel_data.items():
                        # Replace NaN values with empty strings
                        data = data.fillna("")
                        json_data[sheet_name] = data.to_dict(orient='records')
                    
                    # Write to a JSON file
                    json_file_name = os.path.splitext(file_name)[0] + '.json'
                    json_file_path = os.path.join(directory_path, json_file_name)
                    
                    with open(json_file_path, 'w', encoding='utf-8') as json_file:
                        json.dump(json_data, json_file, indent=4, ensure_ascii=False)
                    
                    logger.info(f"Converted {file_name} to {json_file_name}")
                    logger.info(f"Converted {file_name} (all sheets) to {json_file_name}")
                except Exception as e:
                    logger.error(f"Failed to process {file_name}: {e}")
                    logger.error(f"Failed to process {file_name}: {e}")