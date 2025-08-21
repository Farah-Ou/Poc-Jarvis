import os
from dotenv import load_dotenv
import shutil
import subprocess
import pandas as pd
import json
from jira import JIRA
import pymupdf
import fitz  # after pymupdf is imported

import yaml
from pathlib import Path

import os
import pandas as pd
import json

from fastapi import FastAPI, UploadFile, File, HTTPException
from typing import List, Tuple
import os
import uuid
import shutil
from datetime import datetime
import logging
import stat

logger = logging.getLogger(__name__)

def move_folder_contents(src_folder, dest_folder):
    """Move only files from src_folder to dest_folder, overwriting if they exist."""
    if not os.path.exists(src_folder):
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
                
                # Move the file (this will overwrite automatically)
                shutil.move(src_path, dest_path)
                logger.info(f"✅ Successfully moved: {item}")
                
            except PermissionError as e:
                logger.error(f"❌ Permission error moving {item}: {e}")
            except FileNotFoundError as e:
                logger.error(f"❌ File not found error: {e}")
            except Exception as e:
                logger.error(f"❌ Error moving {item}: {e}")
def copy_folder_contents(src_folder, dest_folder):
    """Copy only files from src_folder to dest_folder, overwriting if they exist."""
    if not os.path.exists(src_folder):
        logger.warning(f"Source folder does not exist: {src_folder}")
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
                logger.info(f"✅ Successfully copied: {item}")
                
            except PermissionError as e:
                logger.error(f"❌ Permission error copying {item}: {e}")
            except FileNotFoundError as e:
                logger.error(f"❌ File not found error: {e}")
            except Exception as e:
                logger.error(f"❌ Error copying {item}: {e}")

# Alternative version using copy + remove for more control
def move_folder_contents_safe(src_folder, dest_folder):
    """Move files with explicit copy and delete for better control."""
    if not os.path.exists(src_folder):
        logger.info(f"Source folder does not exist: {src_folder}")
        return
    
    logger.info("Passed the first check, proceeding with moving files...")
    
    os.makedirs(dest_folder, exist_ok=True)
    
    for item in os.listdir(src_folder):
        src_path = os.path.join(src_folder, item)
        dest_path = os.path.join(dest_folder, item)
        
        if os.path.isfile(src_path):
            try:
                # Handle read-only destination files
                if os.path.exists(dest_path):
                    if not os.access(dest_path, os.W_OK):
                        os.chmod(dest_path, stat.S_IWRITE)
                    os.remove(dest_path)
                
                # Copy the file first
                shutil.copy2(src_path, dest_path)
                
                # Remove source file only after successful copy
                os.remove(src_path)
                
            except Exception as e:
                logger.error(f"❌ Error processing {item}: {e}")
                # If copy succeeded but source removal failed, 
                # we still have the file in destination
                if os.path.exists(dest_path):
                    logger.error(f"⚠️ File copied but source not removed: {item}")




def get_excel_file_paths(directory_path):
    """Get all Excel file paths (.xlsx, .xls) from a directory."""
    excel_extensions = ('.xlsx', '.xls')
    return [
        os.path.join(directory_path, file)
        for file in os.listdir(directory_path)
        if os.path.isfile(os.path.join(directory_path, file)) and file.lower().endswith(excel_extensions)
    ]

def get_file_paths(directory_path):
    """Get all file paths from a directory."""
    file_paths = []
    for root, dirs, files in os.walk(directory_path):
        for file in files:
            full_path = os.path.join(root, file)
            file_paths.append(full_path)
    return file_paths

def save_uploaded_files(files: List[UploadFile], destination_path: str):
    """Helper function to save uploaded files to the specified directory"""
    saved_files = []
    invalid_files = []
    
    for file in files:
        # Check if file is PDF or TXT
        if not file.filename.lower().endswith(('.pdf', '.txt')):
            invalid_files.append({
                "filename": file.filename,
                "reason": "Invalid file format. Only PDF and TXT files are allowed."
            })
            continue
        
        # Create unique filename to prevent collisions
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        filename = f"{timestamp}_{unique_id}_{file.filename}"
        file_path = os.path.join(destination_path, filename)
        
        # Save the uploaded file
        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
                
            saved_files.append({
                "original_filename": file.filename,
                "saved_as": filename,
                "size_bytes": os.path.getsize(file_path)
            })
            
        except Exception as e:
            invalid_files.append({
                "filename": file.filename,
                "reason": f"Failed to save file: {str(e)}"
            })
        finally:
            file.file.close()
    
    return saved_files, invalid_files

async def save_uploaded_file_async(file: UploadFile, destination_path: Path) -> Tuple[str, int]:
    """Asynchronously saves a single uploaded file."""
    file_extension = file.filename.split('.')[-1].lower()
    unique_filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}.{file_extension}"
    file_path =  os.path.join(destination_path,unique_filename)
    try:
        with open(file_path, "wb") as buffer:
            while content := await file.read(1024 * 1024):  # Read in chunks
                buffer.write(content)
        file_size = os.path.getsize(file_path)
        return unique_filename, file_size
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file {file.filename}: {str(e)}")
    finally:
        await file.close()


def excel_to_json(directory_path):
    """
    Converts the first sheet of all Excel files in a directory to JSON files.
    
    Parameters:
        directory_path (str): Path to the directory containing Excel files.
    
    Returns:
        None
#     """
    # Ensure the provided path exists
    if not os.path.exists(directory_path):
        logger.error(f"The directory {directory_path} does not exist.")
        

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
            except Exception as e:
                logger.error(f"Failed to process {file_name}: {e}")



def excel_to_json_multiple_sheets(directory_path):
    """
    Converts all Excel files in a directory to JSON files.
    
    Parameters:
        directory_path (str): Path to the directory containing Excel files.
    
    Returns:
        None
    """
    # Ensure the provided path exists
    if not os.path.exists(directory_path):
        logger.error(f"The directory {directory_path} does not exist.")
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
                    json_data[sheet_name] = data.to_dict(orient='records')
                
                # Write to a JSON file
                json_file_name = os.path.splitext(file_name)[0] + '.json'
                json_file_path = os.path.join(directory_path, json_file_name)
                
                with open(json_file_path, 'w', encoding='utf-8') as json_file:
                    json.dump(json_data, json_file, indent=4, ensure_ascii=False)
                
                logger.info(f"Converted {file_name} to {json_file_name}")
            except Exception as e:
                logger.error(f"Failed to process {file_name}: {e}")


def move_files(input_folder, target_folder):
    """
    Move all files from input_folder to target_folder.
    
    Args:
    input_folder (str): Path to the source folder containing files to be moved
    target_folder (str): Path to the destination folder where files will be moved
    
    Returns:
    int: Number of files successfully moved
    """
    # Ensure the target folder exists
    os.makedirs(target_folder, exist_ok=True)
    
    # Counter for successfully moved files
    files_moved = 0
    
    # Iterate through all files in the input folder
    for filename in os.listdir(input_folder):
        # Create full file paths
        source_path = os.path.join(input_folder, filename)
        destination_path = os.path.join(target_folder, filename)
        
        # Skip if it's a directory
        if os.path.isdir(source_path):
            continue
        
        try:
            # Move the file
            shutil.move(source_path, destination_path)
            files_moved += 1
        except Exception as e:
            logger.error(f"Error moving {filename}: {e}")
    
    return files_moved


def concatenate_json_files_to_text(input_folder_path):
    combined_data = []
    output_file_path_json=""
    df = pd.DataFrame() # Initialize df
    
    # Define the output path where the combined text file will be stored
    output_file_path_txt = os.path.join(input_folder_path, "Combined_us_file.txt")
    # Tentatively set to None, will be updated if a file is successfully written
    final_output_txt_path = None
    
    nb=0

    # Transform excel files into json to be procecssed
    excel_to_json(input_folder_path)

    
    # Loop through all files in the input folder
    for file_name in os.listdir(input_folder_path):
        # Only process JSON files
        if file_name.endswith(".json"):
            nb+=1
            file_path = os.path.join(input_folder_path, file_name)
            
            # Open and read each JSON file
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list): # Ensure data is a list for extend
                        combined_data.extend(data)
                    elif isinstance(data, dict): # Handle case where a single JSON object is loaded
                        combined_data.append(data)
            except json.JSONDecodeError:
                logger.warning(f"Warning: Could not decode JSON from {file_path}. Skipping.")
                nb -= 1 # Decrement count of valid JSON files
            except Exception as e:
                logger.warning(f"Warning: Error reading {file_path}: {e}. Skipping.")
                nb -=1

    if nb > 0: # Proceed only if valid JSON files were found and processed
        if nb != 1:
            # Write the combined content to a new JSON file
            output_file_path_json = os.path.join(input_folder_path, "Combined_json_file.json")
            with open(output_file_path_json, 'w', encoding='utf-8') as output_file:
                json.dump(combined_data, output_file, ensure_ascii=False, indent=4)
            logger.info(f"Ensemble json US concatenated and saved to path {output_file_path_json}")
            
            ## Turn into txt combined file
            if os.path.exists(output_file_path_json) and os.path.getsize(output_file_path_json) > 0:
                try:
                    df = pd.read_json(output_file_path_json)
                except ValueError: # Handles empty or invalid JSON
                    logger.warning(f"Warning: Combined JSON file {output_file_path_json} is empty or invalid. Cannot create DataFrame.")
                    df = pd.DataFrame() # Ensure df is an empty DataFrame
            else:
                df = pd.DataFrame()
        
        elif nb==1: # Exactly one valid JSON file
            # file_path here refers to the last JSON file processed in the loop
            if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                try:
                    df = pd.read_json(file_path)
                except ValueError:
                    logger.warning(f"Warning: Single JSON file {file_path} is empty or invalid. Cannot create DataFrame.")
                    df = pd.DataFrame()
            else:
                 df = pd.DataFrame()

        if not df.empty:
            content_as_text = df.to_string(index=False)
            if content_as_text.strip(): # Ensure content is not just whitespace
                with open(output_file_path_txt, 'w', encoding='utf-8') as f:
                    f.write(content_as_text)
                logger.warning(f"Textual US saved to path {output_file_path_txt} from JSON data.")
                final_output_txt_path = output_file_path_txt # Mark as successfully written
            else:
                logger.warning(f"DataFrame was empty or produced empty string. No initial text file written from JSONs to {output_file_path_txt}")
        else:
            logger.error(f"No DataFrame created from JSONs. No initial text file written to {output_file_path_txt}")

    else : 
        logger.error(f"Aucun fichier json valide n\\'existe dans le chemin fourni {input_folder_path}.")
    
    ## Appending text files from created json text and jira import
    # List the files in the input folder
    input_files = os.listdir(input_folder_path)
    # Include the potentially just-created file if it's valid
    existing_txt_files = [f for f in input_files if f.endswith('.txt') and f != os.path.basename(output_file_path_txt)]
    
    source_txt_files_for_concatenation = []
    if final_output_txt_path and os.path.exists(final_output_txt_path) and os.path.getsize(final_output_txt_path) > 0:
        source_txt_files_for_concatenation.append(os.path.basename(final_output_txt_path))
    
    txt_files_in_dir = [file for file in input_files if file.endswith('.txt')]

    if len(txt_files_in_dir) >= 1: # If there is at least one .txt file (could be the one we just made or others)
       
        other_txt_files = [f for f in input_files if f.endswith('.txt') and f != os.path.basename(output_file_path_txt)]

        if final_output_txt_path: # JSONs created Combined_us_file.txt
            if other_txt_files:
                with open(final_output_txt_path, 'a', encoding='utf-8') as output_file: # Append mode
                    file_to_append_path = os.path.join(input_folder_path, other_txt_files[0])
                    if os.path.exists(file_to_append_path) and os.path.getsize(file_to_append_path) > 0:
                        with open(file_to_append_path, 'r', encoding='utf-8') as input_file:
                            content = input_file.read()
                            if content.strip():
                                output_file.write("\\n" + content) # Add newline and content
                                logger.info(f"Appended {other_txt_files[0]} to {final_output_txt_path}")
                            else:
                                logger.warning(f"{other_txt_files[0]} is empty, not appended.")
                    else:
                        logger.error(f"{other_txt_files[0]} is empty or does not exist, not appended.")

            # final_output_txt_path is already set if we are here.
        
        elif len(other_txt_files) >= 1: # JSONs did NOT create a file, but other .txt exist
            # Use the first other text file as the base if it has content
            first_other_txt_path = os.path.join(input_folder_path, other_txt_files[0])
            if os.path.exists(first_other_txt_path) and os.path.getsize(first_other_txt_path) > 0:
                shutil.copy(first_other_txt_path, output_file_path_txt)
                final_output_txt_path = output_file_path_txt
                logger.info(f"Using {other_txt_files[0]} as base for {output_file_path_txt}")
                if len(other_txt_files) >= 2: # Append the second if it exists and has content
                    second_other_txt_path = os.path.join(input_folder_path, other_txt_files[1])
                    if os.path.exists(second_other_txt_path) and os.path.getsize(second_other_txt_path) > 0:
                       with open(final_output_txt_path, 'a', encoding='utf-8') as output_file:
                           with open(second_other_txt_path, 'r', encoding='utf-8') as input_file:
                               content = input_file.read()
                               if content.strip():
                                   output_file.write("\\n" + content)
                                   logger.info(f"Appended {other_txt_files[1]} to {final_output_txt_path}")
                               else:
                                   logger.warning(f"{other_txt_files[1]} is empty, not appended.")
                    else:
                        logger.error(f"Second other text file {other_txt_files[1]} is empty or does not exist, not appended.")
            else:
                logger.error(f"First other .txt file {other_txt_files[0]} is empty. No base for concatenation.")
        else:
            logger.error("No JSON content and not enough other text files to process.")

    else: # nb is 0 (no valid JSONs initially) and also no other text files to process from the start
        logger.error("No JSON files processed and no other text files found to create a combined file.")


    # Final check on the designated output file
    if final_output_txt_path and os.path.exists(final_output_txt_path) and os.path.getsize(final_output_txt_path) > 0:
      pass
    else:
        final_output_txt_path = None # Explicitly set to None if file is empty/doesn't exist
        logger.warning(f"Final combined file {output_file_path_txt} is empty or was not created.")

    return df, output_file_path_json, final_output_txt_path   # Return final_output_txt_path

def concatenate_text_pdf_files(input_folder_path):
    # Define the path for storing the combined files
    _, output_file_path_json_one, output_file_path_txt_one = concatenate_json_files_to_text(input_folder_path)
    combined_file_path = os.path.join(input_folder_path, "combined_context_files.txt")
    
    # Concatenate contents of all files in input folder into the combined file
    with open(combined_file_path, 'w', encoding="utf-8") as combined_file:
        for file_name in os.listdir(input_folder_path):
            input_path = os.path.join(input_folder_path, file_name)
            
            # Process text files
            if os.path.isfile(input_path) and file_name.endswith('.txt'):
                with open(input_path, 'r', encoding="utf-8") as input_file:
                    # Write file content to the combined file with a newline separator
                    combined_file.write(input_file.read() + "\n")
                    
            # Process PDF files
            elif os.path.isfile(input_path) and file_name.endswith('.pdf'):
                with fitz.open(input_path) as pdf_file:
                    for page_num in range(pdf_file.page_count):
                        page = pdf_file.load_page(page_num)
                        combined_file.write(page.get_text("text") + "\n")
    return combined_file_path