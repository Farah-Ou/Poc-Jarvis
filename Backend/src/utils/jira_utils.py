import os
import pandas as pd
from jira import JIRA
from datetime import datetime
import pytz
from pathlib import Path
from typing import Optional, Dict, List, Tuple
import logging
from src.models.jira import JiraCredentials
import re
from Backend_TC_Gen.utils.files_utils import GeneralFileUtils


logger = logging.getLogger(__name__)

files_service = GeneralFileUtils()

class JiraService:
    """Service for JIRA integration and ticket management"""
    
    def __init__(self, api_token: Optional[str] = None):
        """
        Initialize JiraService with optional API token.
        If no token provided, will try to get from environment variables.
        """
        self.api_token = api_token or os.getenv("JIRA_TOKEN")
        self.jira = None
    
    def test_connection(self, credentials: JiraCredentials) -> bool:
        """
        Test JIRA connection using provided credentials and stored API token.
        """
        try:
            jira = JIRA(
                server=credentials.jira_server_url,
                basic_auth=(credentials.jira_username, self.api_token)
            )
            current_user = jira.myself()
            return current_user is not None
        except Exception as e:
            logger.error(f"Failed to connect to JIRA: {e}")
            return False
    
    def test_project_access(self, credentials: JiraCredentials) -> bool:
        """
        Test if the user can access a specific Jira project.
        Only called if project_key is provided.
        """
        if not credentials.jira_project_key:
            return True  # No project to check → pass

        try:
            jira = JIRA(
                server=credentials.jira_server_url,
                basic_auth=(credentials.jira_username, self.api_token)
            )
            project = jira.project(credentials.jira_project_key)
            logger.info(f"✅ Project '{project.name}' ({credentials.jira_project_key}) is accessible")
            return True
        except Exception as e:
            logger.error(f"❌ Cannot access project {credentials.jira_project_key}: {e}")
            return False
    
    def _connect_to_jira(self, user_paths: Dict[str, str]) -> bool:
        """Initialize JIRA connection using credentials from user_paths and API token from settings"""
        try:
            if not user_paths:
                raise ValueError("user_paths dictionary is required")
                
            # Get required credentials
            jira_url = user_paths.get("jira_url")
            jira_user = user_paths.get("jira_username")
            jira_token = self.api_token  # Always use from settings
            
            # Validate all required fields are present
            if not jira_url:
                raise ValueError("Missing JIRA URL in user_paths")
            if not jira_user:
                raise ValueError("Missing JIRA username in user_paths")
            if not jira_token:
                raise ValueError("Missing JIRA API token in settings/environment")
            
            self.jira = JIRA(server=jira_url, basic_auth=(jira_user, jira_token))

            ####

            # project_statuses = self.jira._get_json(f"/rest/api/3/project/P7P/statuses")
            url = f"https://geniatestcase-talan.atlassian.net/rest/api/3/project/P7P/statuses"

            response = self.jira._session.get(url)

            if response.status_code == 200:
                data = response.json()
                all_statuses = set()
                for issue_type in data:
                    for status in issue_type.get("statuses", []):
                        all_statuses.add(status["name"])
                logger.info(f"All available statuses in project P7P:")
                for status in sorted(all_statuses):
                    logger.info(f"- {status}")
            else:
                logger.error(f"Failed to get statuses: {response.status_code} - {response.text}")
            


            logger.info("Successfully connected to JIRA")
            return True
            

        except Exception as e:
            logger.error(f"Error connecting to JIRA: {e}")
            return False
   
        
    def Jira_import_Epics_Feat_US(
        self,
        user_paths: Dict[str, str],
        project_folder_path: str,
        credentials: Optional[Dict] = None
    ) -> Tuple[Optional[str], List[str], List[str], pd.DataFrame, Optional[datetime]]:
        """
        Importe tous les tickets 'User Story' d'un projet Jira Xray.
        
        Args:
            user_paths (dict): Chemins de configuration Jira
            project_folder_path (str): Dossier où sauvegarder les résultats
            credentials (dict, optional): Identifiants supplémentaires
        
        Returns:
            tuple: 
                - chemin du fichier généré
                - liste des IDs
                - liste des titres
                - dataframe complet
                - date la plus récente
        """
        try:
            if not self.jira:
                self._connect_to_jira(user_paths)

            # Récupération de la clé du projet
            project_key = user_paths.get('US_project_key')
            if not project_key:
                logger.error("❌ Clé de projet non définie dans user_paths")
                return None, [], [], pd.DataFrame(), None

            # Liste des projets disponibles (pour debug)
            try:
                all_projects = self.jira.projects()
                logger.info("Projets disponibles dans votre instance Jira :")
                for proj in all_projects:
                    logger.info(f"  - {proj.key}, {proj.name}")
            except Exception as e:
                logger.warning(f"⚠️ Impossible de récupérer la liste des projets : {e}")

            # Accès au projet
            try:
                project = self.jira.project(project_key)
                logger.info(f"✅ Projet '{project.name}' ({project_key}) accessible")
            except Exception as e:
                logger.error(f"❌ Erreur lors de l'accès au projet : {e}")
                return None, [], [], pd.DataFrame(), None

            # Définition du chemin du fichier de sortie
            imported_US = Path(project_folder_path) / "Imported_User_Stories.txt"
            imported_US_json = Path(project_folder_path) / "Imported_User_Stories.json"
            imported_US_excel = Path(project_folder_path) / "Imported_User_Stories.xlsx"
            logger.debug(f"Fichier de sortie : {imported_US}")

            # Initialisation des listes de données
            ids_list = []
            titles_list = []
            description_list = []
            field_type_list = []  
            parent_titles_list = []
            parent_ids_list = []
            related_issues_list = []
            created_list = []
            updated_list = []
            
            jql_query = f'project = "{project_key}" AND issuetype IN ("Epic", "Feature","Story")'
            logger.info(f"🔍 Requête JQL : {jql_query}")

            try:
                tickets = self.jira.search_issues(jql_query, maxResults=1000)
                logger.info(f"{len(tickets)} User Stories trouvées")
                if len(tickets) == 0:
                    logger.warning("⚠️ Aucune User Story trouvée. Vérifiez :")
                    logger.warning("1. Le projet ne contient peut-être pas de User Stories")
                    logger.warning("2. Le type de ticket pourrait être différent (ex: 'Story')")
                    logger.warning("3. Vous n'avez peut-être pas les droits nécessaires")

                   
            except Exception as e:
                logger.error(f"❌ Échec de la recherche des tickets : {e}")
                return None, [], [], pd.DataFrame(), None

            # Création du fichier de sortie
            try:
                with open(imported_US, "w", encoding='utf-8') as file:
                   
                    # Traitement de chaque ticket
                    for i, ticket in enumerate(tickets, 1):
                        logger.debug(f"Traitement du ticket {i}/{len(tickets)} : {ticket.key}")
                        try:
                            ticket_key = ticket.key
                            title = ticket.fields.summary
                            description = ticket.fields.description or ""
                            # status = ticket.fields.status.name
                            issue_type = ticket.fields.issuetype.name

                            # Extract and store created/updated dates
                            try:
                                created_str = ticket.fields.created
                                updated_str = ticket.fields.updated
                                
                                # Parse datetime strings with timezone info
                                created_dt = datetime.fromisoformat(created_str.replace('Z', '+00:00'))
                                updated_dt = datetime.fromisoformat(updated_str.replace('Z', '+00:00'))
                                
                                created_list.append(created_dt)
                                updated_list.append(updated_dt)
                            except Exception as e:
                                logger.warning(f"Error parsing dates for ticket {ticket_key}: {e}")
                                created_list.append(pd.NaT)
                                updated_list.append(pd.NaT)

                            # Récupération du parent si disponible
                            parent_key = ""
                            parent_summary = ""
                            if hasattr(ticket.fields, 'parent'):
                                parent_key = ticket.fields.parent.key
                                parent_summary = ticket.fields.parent.fields.summary


                            # 🔗 Récupération des tickets liés
                            related_issues = []
                            if hasattr(ticket.fields, "issuelinks"):
                                for link in ticket.fields.issuelinks:
                                    if hasattr(link, "outwardIssue"):
                                        related_issue = link.outwardIssue
                                        relation_type = link.type.outward
                                    elif hasattr(link, "inwardIssue"):
                                        related_issue = link.inwardIssue
                                        relation_type = link.type.inward
                                    else:
                                        continue

                                    related_issues.append({
                                        "key": related_issue.key,
                                        "summary": related_issue.fields.summary,
                                        "relationship": relation_type
                                    })

                            # Stockage des données
                            ids_list.append(ticket_key)
                            titles_list.append(title)
                            description_list.append(description)
                            field_type_list.append(issue_type)
                            parent_ids_list.append(parent_key)
                            parent_titles_list.append(parent_summary)
                            related_issues_list.append(related_issues)

                            
                            # Écriture dans le fichier
                            # file.write(f"Ticket ID: {ticket_key}\n")
                            file.write(f"Titre: {title}\n")
                            file.write(f"Description: {description}\n")
                            # file.write(f"Statut: {status}\n")
                            file.write(f"Type de ticket: {issue_type}\n")
                            if len(created_list) > 0 and not pd.isna(created_list[-1]):
                                file.write(f"Created: {created_list[-1]}\n")
                            if len(updated_list) > 0 and not pd.isna(updated_list[-1]):
                                file.write(f"Updated: {updated_list[-1]}\n")
                            file.write(f"Parent Ticket: {parent_summary}\n")
                            file.write(f"Related Tickets: {related_issues}\n")
                            file.write("-" * 40 + "\n\n")

                        except Exception as e:
                            logger.error(f"❌ Échec du traitement du ticket {ticket.key} : {e}")
                            # Ensure list consistency even if ticket processing fails
                            if len(ids_list) > len(created_list):
                                created_list.append(pd.NaT)
                            if len(ids_list) > len(updated_list):
                                updated_list.append(pd.NaT)
                            
            except Exception as e:
                logger.error(f"❌ Échec de l'écriture dans le fichier : {e}")
                return None, [], [], pd.DataFrame(), None

            # Création du DataFrame
            try:
                # Convert timezone-aware datetimes to timezone-unaware for Excel compatibility
                created_list_naive = [dt.replace(tzinfo=None) if not pd.isna(dt) else dt for dt in created_list]
                updated_list_naive = [dt.replace(tzinfo=None) if not pd.isna(dt) else dt for dt in updated_list]
                
                df = pd.DataFrame({
                    'US_ID': ids_list,
                    'Titre': titles_list,
                    'Description': description_list,
                    'Type de ticket': field_type_list,
                    'Parent ID': parent_ids_list,
                    'Parent Titre': parent_titles_list,
                    'Related Tickets': related_issues_list,
                    'Created': created_list_naive,
                    'Updated': updated_list_naive
                })

                # Extract most recent dates if data exists
                most_recent_date = None
                if len(created_list) > 0 or len(updated_list) > 0:
                    try:
                        valid_created = [d for d in created_list if not pd.isna(d)]
                        valid_updated = [d for d in updated_list if not pd.isna(d)]
                        
                        most_recent_created = max(valid_created) if valid_created else None
                        most_recent_updated = max(valid_updated) if valid_updated else None
                        
                        if most_recent_created and most_recent_updated:
                            most_recent_date = max(most_recent_created, most_recent_updated)
                        elif most_recent_created:
                            most_recent_date = most_recent_created
                        elif most_recent_updated:
                            most_recent_date = most_recent_updated
                        
                        if most_recent_created:
                            logger.info(f"Most recent creation date: {most_recent_created}")
                        if most_recent_updated:
                            logger.info(f"Most recent update date: {most_recent_updated}")
                        if most_recent_date:
                            logger.info(f"Most recent date overall: {most_recent_date}")
                            
                    except Exception as e:
                        logger.warning(f"Error calculating most recent dates: {e}")

                logger.info(f"Résumé de l'extraction :")
                logger.info(f"Nombre de User Stories : {len(ids_list)}")
                logger.info(f"Shape du DataFrame : {df.shape}")
                logger.info(f"Détails sauvegardés dans : {imported_US}")
            except Exception as e:
                logger.error(f"❌ Échec de la création du DataFrame : {e}")
                df = pd.DataFrame()
                most_recent_date = None

            df.to_json(imported_US_json, orient='records', lines=False, indent=2)
            df.to_excel(imported_US_excel, index=False)
            return str(imported_US), ids_list, titles_list, df, most_recent_date

        except Exception as e:
            logger.error(f"❌ Erreur globale dans Jira_import_Epics_Features_US : {e}")
            return None, [], [], pd.DataFrame(), None

        
    async def import_gherkin_tests_with_jdd(
        self,
        user_paths: Dict[str, str],
        credentials: Optional[JiraCredentials] = None
    ) -> Tuple[List[str], List[str], pd.DataFrame]:
        """
        Import Gherkin tests with associated 'Jeu de donnees' and save Excel attachments.
        
        Args:
            user_paths: Dictionary containing user configuration paths and settings
            credentials: Optional JIRA credentials
            
        Returns:
            Tuple containing:
            - List of ticket IDs
            - List of ticket titles  
            - DataFrame with test case information
        """
        try:
            if not self.jira:
                self._connect_to_jira(user_paths)

            # Get configuration from user_paths
            jira_url = user_paths.get("jira_url")
            jira_user = user_paths.get("jira_username")
            input_ticket_name_field = user_paths.get("Tests_to_automate_name_field")
            project_key = user_paths.get("US_project_key")
            
            # Validate project access
            try:
                project = self.jira.project(project_key)
                logger.info(f"Successfully accessed project: {project.name} ({project_key})")
            except Exception as e:
                logger.error(f"Error accessing project {project_key}: {e}")
                raise

            # Ensure Excel output directory exists
            excel_output_dir = Path("../User_Data/Excels")
            excel_output_dir.mkdir(parents=True, exist_ok=True)

            # Initialize data storage
            TC_ids_list = []
            TC_titles_list = []
            TC_Gherkin_description_list = []
            JDD_list = []

            # Get field mappings
            fields = self.jira.fields()
            field_name_to_id = {field['name']: field['id'] for field in fields}
            logger.info("Retrieved JIRA field mappings")

            # Define the custom field names to retrieve
            custom_field_names = ["Jeu de donnees"]
            
            # Check for missing fields
            missing_fields = [name for name in custom_field_names if name not in field_name_to_id]
            if missing_fields:
                logger.warning(f"The following custom fields are not found: {missing_fields}")

            # Define the JQL query for the project
            jql_query = f'project = {project_key}'
            tickets = self.jira.search_issues(jql_query, maxResults=1000)
            logger.info(f"Found {len(tickets)} tickets in project {project_key}")

            # Process each ticket
            for ticket in tickets:
                try:
                    logger.debug(f"Processing ticket: {ticket.key}")
                    
                    # Check if ticket status matches the required field
                    if ticket.fields.status.name == input_ticket_name_field:
                        # Retrieve basic ticket information
                        ticket_key = ticket.key
                        title = ticket.fields.summary
                        description = ticket.fields.description if ticket.fields.description else ""
                        
                        # Add to lists for DataFrame
                        TC_ids_list.append(ticket_key)
                        TC_titles_list.append(title)
                        TC_Gherkin_description_list.append(description)
                        
                        # Retrieve custom field values
                        for field_name in custom_field_names:
                            field_id = field_name_to_id.get(field_name)
                            
                            if field_id:
                                try:
                                    field_value = getattr(ticket.fields, field_id, None)
                                    logger.debug(f"Field {field_name} ({field_id}): {field_value}")
                                    
                                    # Handle None values
                                    field_value = field_value if field_value is not None else "Field not found"
                                    
                                    if field_name == "Jeu de donnees":
                                        JDD_list.append(field_value)
                                        
                                except Exception as e:
                                    logger.error(f"Error retrieving field {field_name}: {e}")
                                    if field_name == "Jeu de donnees":
                                        JDD_list.append("Error retrieving field")
                            else:
                                logger.warning(f"Field {field_name} not found in JIRA")
                                if field_name == "Jeu de donnees":
                                    JDD_list.append("Field not found")
                        
                        # Process Excel attachments
                        for attachment in ticket.fields.attachment:
                            if attachment.filename.endswith(".xlsx"):
                                try:
                                    # Create safe filename
                                    safe_title = re.sub(r'[^\w\s-]', '_', title)
                                    excel_filename = f'{ticket_key}_{safe_title}_{attachment.filename}'
                                    excel_save_path = excel_output_dir / excel_filename
                                    
                                    # Download and save Excel file
                                    with open(excel_save_path, "wb") as f:
                                        f.write(attachment.get())
                                    
                                    logger.info(f"Saved Excel attachment to: {excel_save_path}")
                                    
                                except Exception as e:
                                    logger.error(f"Error downloading attachment {attachment.filename}: {e}")
                    
                except Exception as e:
                    logger.error(f"Error processing ticket {ticket.key}: {e}")
                    # Maintain list consistency by adding error placeholders
                    if len(TC_ids_list) > len(JDD_list):
                        JDD_list.append("Error processing ticket")

            # Create DataFrame
            df = pd.DataFrame({
                'TC_ID': TC_ids_list,
                'TC_Titre': TC_titles_list,
                'TC_Gherkin_Description': TC_Gherkin_description_list,
                'Jeu de Donnees': JDD_list,
            })

            logger.info(f"Successfully processed {len(TC_ids_list)} test cases")
            return TC_ids_list, TC_titles_list, df

        except Exception as e:
            logger.error(f"Error importing Gherkin tests with JDD: {e}")
            raise

    def Jira_import_Test_Case_Cucumber(
        self, 
        user_paths: Dict[str, str], 
        project_folder_path: str
    ) -> Tuple[Optional[str], List[str], List[str], pd.DataFrame, Optional[datetime]]:
        """
        Import all Test Case Cucumber tickets from an Xray Jira project
        
        Args:
            user_paths (dict): Dictionary containing Jira configuration paths
            project_folder_path (str): Path to the project folder where files will be saved
            credentials: Optional JIRA credentials
            
        Returns:
            tuple: (imported_TC_file_path, ids_list, titles_list, dataframe, most_recent_date)
        """
        try:
            if not self.jira:
                self._connect_to_jira(user_paths)
            
            # Access the project by project key
            project_key = user_paths.get('US_project_key')
            
            # First, let's list all available projects to help with debugging
            try:
                all_projects = self.jira.projects()
                logger.info("Available projects in your Jira instance:")
                for proj in all_projects:
                    logger.info(f"  - Key: {proj.key}, Name: {proj.name}")
            except Exception as e:
                logger.warning(f"Could not retrieve project list: {e}")
            
            try:
                project = self.jira.project(project_key)
                logger.info(f"Successfully accessed project: {project.name} ({project_key})")
            except Exception as e:
                logger.error(f"Error accessing project {project_key}: {e}")
                logger.error(f"Please check if the project key '{project_key}' exists in the list above.")
                return None, [], [], pd.DataFrame(), None

            # Define path where the text file of Test Case Cucumber will be saved
            imported_TC = os.path.join(project_folder_path, "Imported_Test_Case_Cucumber.txt")
            
            # Initialize lists to store extracted data
            ids_list = []
            titles_list = []
            feature_list = []
            description_list = []
            test_data_list = []
            created_list = []
            updated_list = []

            # Retrieve JIRA FIELDS AND MAP THEM
            try:
                fields = self.jira.fields()
                field_name_to_id = {field['name']: field['id'] for field in fields}
                logger.info("Successfully retrieved Jira field mappings")
            except Exception as e:
                logger.error(f"Error retrieving Jira fields: {e}")
                return None, [], [], pd.DataFrame(), None

            # Define the custom field names for Test Case Cucumber
            custom_field_names = ["Feature", "Jeu de Donnees"]
            
            # Check for missing custom fields and try alternatives
            missing_fields = [name for name in custom_field_names if name not in field_name_to_id]
            if missing_fields:
                logger.warning(f"The following custom fields are not found: {missing_fields}")
                # Try alternative field names
                alternative_field_names = ["Feature", "Jeu de Donnees", "Jeu de données", "Test Data"]
                for i, missing_field in enumerate(missing_fields):
                    for alt_name in alternative_field_names:
                        if alt_name in field_name_to_id:
                            if missing_field == "Jeu de Donnees" and ("donnees" in alt_name.lower() or "data" in alt_name.lower()):
                                custom_field_names[custom_field_names.index(missing_field)] = alt_name
                                logger.info(f"Using alternative field name: {alt_name}")
                                break
                            elif missing_field == "Feature" and alt_name == "Feature":
                                custom_field_names[custom_field_names.index(missing_field)] = alt_name
                                logger.info(f"Using alternative field name: {alt_name}")
                                break

            # Define JQL query to get all Test Case Cucumber tickets from the project
            jql_query = f'project = "{project_key}" AND issuetype = "Test"'
            logger.info(f"JQL Query: {jql_query}")
            
            try:
                # Search for Test Case Cucumber tickets
                tickets = self.jira.search_issues(jql_query, maxResults=1000)
                logger.info(f"Found {len(tickets)} Test tickets")
                
                if len(tickets) == 0:
                    logger.warning("No Test tickets found. This could mean:")
                    logger.warning("1. The project has no Test tickets")
                    logger.warning("2. The issue type name might be different")
                    logger.warning("3. You might not have permission to view these tickets")
                    
                    # Try alternative issue type names
                    alternative_queries = [
                        f'project = "{project_key}" AND issuetype = "Test"',
                        f'project = "{project_key}" AND issuetype = "Test Case"',
                        f'project = "{project_key}"'  # Get all tickets to see what's available
                    ]
                    
                    for alt_query in alternative_queries:
                        try:
                            logger.info(f"Trying alternative query: {alt_query}")
                            alt_tickets = self.jira.search_issues(alt_query, maxResults=10)
                            if len(alt_tickets) > 0:
                                logger.info(f"Found {len(alt_tickets)} tickets with alternative query")
                                logger.info("Issue types found:")
                                issue_types = set(ticket.fields.issuetype.name for ticket in alt_tickets)
                                for issue_type in issue_types:
                                    logger.info(f"  - {issue_type}")
                                break
                        except Exception as e:
                            logger.error(f"Alternative query failed: {e}")
                            
                    return None, [], [], pd.DataFrame(), None
                            
            except Exception as e:
                logger.error(f"Error searching for Test tickets: {e}")
                logger.error("This might be due to:")
                logger.error("1. Invalid project key")
                logger.error("2. No permission to access the project")
                logger.error("3. Network connectivity issues")
                return None, [], [], pd.DataFrame(), None
            
            # Open the file to write the Test Case Cucumber information with proper encoding
            try:
                with open(imported_TC, "w", encoding='utf-8') as file:
                    file.write(f"Test extracted from Xray Project: {project_key}\n")
                    file.write(f"Total Test found: {len(tickets)}\n")
                    file.write("=" * 60 + "\n\n")
                    
                    # Process each Test Case Cucumber ticket
                    for i, ticket in enumerate(tickets, 1):
                        logger.debug(f"Processing Test {i}/{len(tickets)}: {ticket.key}")
                        
                        try:
                            # Extract basic ticket information
                            ticket_key = ticket.key
                            title = ticket.fields.summary
                            description = ticket.fields.description if ticket.fields.description else ""
                            
                            # Store basic information in lists
                            ids_list.append(ticket_key)
                            titles_list.append(title)
                            description_list.append(description)

                            # Extract and store created/updated dates
                            try:
                                created_str = ticket.fields.created
                                updated_str = ticket.fields.updated
                                
                                # Parse datetime strings with timezone info
                                created_dt = datetime.fromisoformat(created_str.replace('Z', '+00:00'))
                                updated_dt = datetime.fromisoformat(updated_str.replace('Z', '+00:00'))
                                
                                created_list.append(created_dt)
                                updated_list.append(updated_dt)
                            except Exception as e:
                                logger.warning(f"Error parsing dates for ticket {ticket_key}: {e}")
                                created_list.append(pd.NaT)
                                updated_list.append(pd.NaT)
                            
                            # Write basic information to file
                            file.write(f"Ticket ID: {ticket_key}\n")
                            file.write(f"Scenario (Title): {title}\n")
                            file.write(f"Steps (Description): {description}\n")
                            file.write(f"Status: {ticket.fields.status.name}\n")
                            file.write(f"Issue Type: {ticket.fields.issuetype.name}\n")
                            if len(created_list) > 0 and not pd.isna(created_list[-1]):
                                file.write(f"Created: {created_list[-1]}\n")
                            if len(updated_list) > 0 and not pd.isna(updated_list[-1]):
                                file.write(f"Updated: {updated_list[-1]}\n")
                            
                            # Process custom fields
                            current_feature = ""
                            current_test_data = ""
                            
                            for field_name in custom_field_names:
                                field_id = field_name_to_id.get(field_name)
                                
                                if field_id:
                                    try:
                                        field_value = getattr(ticket.fields, field_id, None)
                                        field_value = field_value if field_value is not None else "Field not found"
                                        
                                        file.write(f"{field_name} ({field_id}): {field_value}\n")
                                        
                                        # Store values in respective variables
                                        if field_name == "Feature":
                                            current_feature = field_value
                                        elif "donnees" in field_name.lower() or "data" in field_name.lower():
                                            current_test_data = field_value
                                            
                                    except Exception as e:
                                        logger.error(f"Error retrieving custom field {field_name} for ticket {ticket_key}: {e}")
                                        file.write(f"{field_name}: Error retrieving field\n")
                                        
                                        # Add error values to maintain consistency
                                        if field_name == "Feature":
                                            current_feature = "Error retrieving field"
                                        elif "donnees" in field_name.lower() or "data" in field_name.lower():
                                            current_test_data = "Error retrieving field"
                                else:
                                    file.write(f"{field_name}: Field not found in Jira\n")
                                    
                                    # Add default values for missing fields
                                    if field_name == "Feature":
                                        current_feature = "Field not found"
                                    elif "donnees" in field_name.lower() or "data" in field_name.lower():
                                        current_test_data = "Field not found"
                            
                            # Append values to lists
                            feature_list.append(current_feature)
                            test_data_list.append(current_test_data)
                            
                            file.write("\n" + "=" * 40 + "\n\n")
                            
                        except Exception as e:
                            logger.error(f"Error processing ticket {ticket.key}: {e}")
                            # Ensure list consistency even if ticket processing fails
                            if len(ids_list) > len(feature_list):
                                feature_list.append("Error processing ticket")
                            if len(ids_list) > len(test_data_list):
                                test_data_list.append("Error processing ticket")
                            if len(ids_list) > len(created_list):
                                created_list.append(pd.NaT)
                            if len(ids_list) > len(updated_list):
                                updated_list.append(pd.NaT)
                    
                    file.write(f"\nTotal Test processed: {len(ids_list)}\n")
                    file.write(f"File generated on: {pd.Timestamp.now()}\n")
                    
            except Exception as e:
                logger.error(f"Error writing to file {imported_TC}: {e}")
                return None, [], [], pd.DataFrame(), None

            # Create DataFrame with all extracted Test Case Cucumber data
            try:
                df = pd.DataFrame({
                    'id': ids_list,
                    'Feature': feature_list,
                    'Scenario': titles_list,
                    'Steps': description_list,
                    'Test Data': test_data_list,
                    'Created': created_list,
                    'Updated': updated_list
                })

                # Extract most recent dates if data exists
                most_recent_date = None
                if len(created_list) > 0 or len(updated_list) > 0:
                    try:
                        valid_created = [d for d in created_list if not pd.isna(d)]
                        valid_updated = [d for d in updated_list if not pd.isna(d)]
                        
                        most_recent_created = max(valid_created) if valid_created else None
                        most_recent_updated = max(valid_updated) if valid_updated else None
                        
                        if most_recent_created and most_recent_updated:
                            most_recent_date = max(most_recent_created, most_recent_updated)
                        elif most_recent_created:
                            most_recent_date = most_recent_created
                        elif most_recent_updated:
                            most_recent_date = most_recent_updated
                        
                        if most_recent_created:
                            logger.info(f"Most recent creation date: {most_recent_created}")
                        if most_recent_updated:
                            logger.info(f"Most recent update date: {most_recent_updated}")
                        if most_recent_date:
                            logger.info(f"Most recent date overall: {most_recent_date}")
                            
                    except Exception as e:
                        logger.warning(f"Error calculating most recent dates: {e}")
                
                logger.info(f"Extraction Summary:")
                logger.info(f"Test extracted: {len(ids_list)}")
                logger.info(f"DataFrame shape: {df.shape}")
                logger.info(f"Test details saved to: {imported_TC}")
                
            except Exception as e:
                logger.error(f"Error creating DataFrame: {e}")
                df = pd.DataFrame()
                most_recent_date = None

            return imported_TC, ids_list, titles_list, df, most_recent_date
            
        except Exception as e:
            logger.error(f"Error in Jira_import_Test_Case_Cucumber: {e}")
            return None, [], [], pd.DataFrame(), None
        
    def jira_import_tickets_by_date(
        self, 
        user_paths: Dict[str, str], 
        project_folder_path: str, 
        ticket_type: str, 
        reference_date: str
    ) -> Tuple[Optional[str], List[str], List[str], pd.DataFrame, Optional[str]]:
        
        """
        Import Jira tickets of a specific type that were created or updated after a reference date.
        Returns the most recent date among all extracted tickets.
        
        Args:
            user_paths: Dictionary containing Jira configuration paths
            project_folder_path: Path to the project folder where files will be saved
            ticket_type: Type of tickets to import (e.g., "Test Case Cucumber", "Story")
            reference_date: Reference date in format 'YYYY-MM-DD' or 'YYYY-MM-DD HH:MM'
            credentials: Optional JIRA credentials
            
        Returns:
            tuple: (imported_file_path, ids_list, titles_list, dataframe, most_recent_date_formatted)
        """
        try:
            if not self.jira:
                self._connect_to_jira(user_paths)
            
            # Access the project by project key
            project_key = user_paths.get('US_project_key')
            
            # Validate project access
            try:
                project = self.jira.project(project_key)
                logger.info(f"Successfully accessed project: {project.name} ({project_key})")
            except Exception as e:
                logger.error(f"Error accessing project {project_key}: {e}")
                return None, [], [], pd.DataFrame(), None

            # Define path where the text file will be saved
            safe_ticket_type = ticket_type.replace(" ", "_").replace("/", "_")
            safe_ref_date = reference_date.replace('-', '_').replace(':', '_').replace(' ', '_')
            imported_file = os.path.join(
                project_folder_path, 
                f"Imported_{safe_ticket_type}_Since_{safe_ref_date}.txt"
            )
            
            # Initialize lists to store extracted data
            ids_list = []
            titles_list = []
            feature_list = []
            description_list = []
            test_data_list = []
            third_field_list = []
            creation_dates = []
            update_dates = []
            all_datetime_objects = []

            # Retrieve JIRA FIELDS AND MAP THEM
            try:
                fields = self.jira.fields()
                field_name_to_id = {field['name']: field['id'] for field in fields}
                logger.info("Successfully retrieved Jira field mappings")
            except Exception as e:
                logger.error(f"Error retrieving Jira fields: {e}")
                return None, [], [], pd.DataFrame(), None

            # Define the custom field names based on ticket type
            if "Test" in ticket_type:
                custom_field_names = ["Feature", "Jeu de Donnees"]
            elif "Story" in ticket_type:
                custom_field_names = ["Regles de Gestion", "Criteres d'Acceptance", "Parametres"]
            else:
                custom_field_names = []

            # Check for missing custom fields and find alternatives
            missing_fields = [name for name in custom_field_names if name not in field_name_to_id]
            if missing_fields:
                logger.warning(f"The following custom fields are not found: {missing_fields}")
                if "Test" in ticket_type:
                    alternative_field_names = ["Feature", "Jeu de Donnees", "Jeu de données", "Test Data"]
                    for i, missing_field in enumerate(missing_fields):
                        for alt_name in alternative_field_names:
                            if alt_name in field_name_to_id:
                                if missing_field == "Jeu de Donnees" and ("donnees" in alt_name.lower() or "data" in alt_name.lower()):
                                    custom_field_names[i] = alt_name
                                    logger.info(f"Using alternative field name: {alt_name}")
                                    break

            # Convert reference date to timezone-aware datetime for comparison
            try:
                if len(reference_date) == 10:  # YYYY-MM-DD format
                    ref_datetime = datetime.strptime(reference_date, '%Y-%m-%d')
                else:  # YYYY-MM-DD HH:MM format
                    ref_datetime = datetime.strptime(reference_date, '%Y-%m-%d %H:%M')
                
                # Make timezone-aware (UTC) for comparison with Jira dates
                ref_datetime_utc = pytz.UTC.localize(ref_datetime)
                
                logger.info(f"Using reference date: {reference_date}")
                logger.info(f"Reference datetime for comparison: {ref_datetime_utc}")
                
            except ValueError as e:
                logger.error(f"Error parsing reference date '{reference_date}': {e}")
                logger.error("Please use format 'YYYY-MM-DD' or 'YYYY-MM-DD HH:MM'")
                return None, [], [], pd.DataFrame(), None

             # Define JQL query to get tickets created or updated after reference date
            if ticket_type == "Test" : 
                jql_query = f'project = "{project_key}" AND issuetype = "{ticket_type}" AND (created >= "{reference_date}" OR updated >= "{reference_date}")'
            elif ticket_type == "Story":
                jql_query = f'project = "{project_key}" AND issuetype IN ("Epic", "Feature","Story") AND (created >= "{reference_date}" OR updated >= "{reference_date}")'
            logger.info(f"JQL Query: {jql_query}")
            
            try:
                # Search for tickets matching criteria
                tickets = self.jira.search_issues(jql_query, maxResults=1000, expand='changelog')
                logger.warning(f"Found {len(tickets)} {ticket_type} tickets created or updated since {reference_date}")
                
                if len(tickets) == 0:
                    logger.info(f"No {ticket_type} tickets found that were created or updated since {reference_date}")
                    return imported_file, [], [], pd.DataFrame(), None
                    
            except Exception as e:
                logger.error(f"Error searching for {ticket_type} tickets: {e}")
                return None, [], [], pd.DataFrame(), None
            
            # Open the file to write the ticket information with proper encoding
            try:
                with open(imported_file, "w", encoding='utf-8') as file:
                    file.write(f"{ticket_type} tickets extracted from Xray Project: {project_key}\n")
                    file.write(f"Reference date: {reference_date}\n")
                    file.write(f"Total {ticket_type} tickets found (created or updated since reference date): {len(tickets)}\n")
                    file.write("=" * 80 + "\n\n")
                    
                    # Process each ticket
                    for i, ticket in enumerate(tickets, 1):
                        logger.debug(f"Processing {ticket_type} {i}/{len(tickets)}: {ticket.key}")
                        
                        try:
                            # Extract basic ticket information
                            ticket_key = ticket.key
                            title = ticket.fields.summary
                            description = ticket.fields.description if ticket.fields.description else ""
                            
                            # Extract and parse dates
                            created_date = ticket.fields.created
                            updated_date = ticket.fields.updated
                            
                            created_formatted = "N/A"
                            updated_formatted = "N/A"
                            created_after_ref = False
                            updated_after_ref = False
                            
                            if created_date:
                                created_dt = pd.to_datetime(created_date)
                                created_formatted = created_dt.strftime('%Y-%m-%d %H:%M:%S')
                                if created_dt.tz is None:
                                    created_dt = pytz.UTC.localize(created_dt)
                                created_after_ref = created_dt >= ref_datetime_utc
                                all_datetime_objects.append(created_dt)
                            
                            if updated_date:
                                updated_dt = pd.to_datetime(updated_date)
                                updated_formatted = updated_dt.strftime('%Y-%m-%d %H:%M:%S')
                                if updated_dt.tz is None:
                                    updated_dt = pytz.UTC.localize(updated_dt)
                                updated_after_ref = updated_dt >= ref_datetime_utc
                                all_datetime_objects.append(updated_dt)
                            
                            # Determine inclusion reason
                            trigger_reason = []
                            if created_after_ref:
                                trigger_reason.append("CREATED")
                            if updated_after_ref:
                                trigger_reason.append("UPDATED")
                            trigger_status = " & ".join(trigger_reason) + f" after {reference_date}"
                            
                            # Store basic information in lists
                            ids_list.append(ticket_key)
                            titles_list.append(title)
                            description_list.append(description)
                            creation_dates.append(created_formatted)
                            update_dates.append(updated_formatted)
                            
                            # Write basic information to file
                            file.write(f"Ticket ID: {ticket_key}\n")
                            file.write(f"Title/Scenario: {title}\n")
                            file.write(f"Description/Steps: {description}\n")
                            file.write(f"Status: {ticket.fields.status.name}\n")
                            file.write(f"Issue Type: {ticket.fields.issuetype.name}\n")
                            file.write(f"Created: {created_formatted}\n")
                            file.write(f"Updated: {updated_formatted}\n")
                            file.write(f"Inclusion Reason: {trigger_status}\n")
                            
                            # Process custom fields
                            current_feature = ""
                            current_test_data = ""
                            current_third_field = ""
                            
                            for field_name in custom_field_names:
                                field_id = field_name_to_id.get(field_name)
                                
                                if field_id:
                                    try:
                                        field_value = getattr(ticket.fields, field_id, None)
                                        field_value = field_value if field_value is not None else ""
                                        
                                        file.write(f"{field_name} ({field_id}): {field_value}\n")
                                        
                                        # Map field values based on ticket type
                                        if "Test" in ticket_type:
                                            if field_name == "Feature":
                                                current_feature = field_value
                                            elif "donnees" in field_name.lower() or "data" in field_name.lower():
                                                current_test_data = field_value
                                        elif "Story" in ticket_type:
                                            if field_name == "Regles de Gestion":
                                                current_feature = field_value
                                            elif field_name == "Criteres d'Acceptance":
                                                current_test_data = field_value
                                            elif field_name == "Parametres":
                                                current_third_field = field_value
                                        else:
                                            # Generic handling for other ticket types
                                            if len(custom_field_names) > 0 and field_name == custom_field_names[0]:
                                                current_feature = field_value
                                            elif len(custom_field_names) > 1 and field_name == custom_field_names[1]:
                                                current_test_data = field_value
                                            elif len(custom_field_names) > 2 and field_name == custom_field_names[2]:
                                                current_third_field = field_value
                                                
                                    except Exception as e:
                                        logger.error(f"Error retrieving custom field {field_name} for ticket {ticket_key}: {e}")
                                        file.write(f"{field_name}: Error retrieving field\n")
                                        
                                        # Add error values to maintain list consistency
                                        self._set_error_values_for_ticket_type(
                                            ticket_type, field_name, 
                                            current_feature, current_test_data, current_third_field
                                        )
                                else:
                                    file.write(f"{field_name}: Field not found in Jira\n")
                                    
                                    # Add default values for missing fields
                                    self._set_default_values_for_ticket_type(
                                        ticket_type, field_name,
                                        current_feature, current_test_data, current_third_field
                                    )
                            
                            # Set default values if no custom fields were defined
                            if not custom_field_names:
                                current_feature = "No custom fields defined"
                                current_test_data = "No custom fields defined"
                                current_third_field = "No custom fields defined"
                            
                            # Append values to lists
                            feature_list.append(current_feature)
                            test_data_list.append(current_test_data)
                            third_field_list.append(current_third_field)
                            
                            file.write("\n" + "=" * 50 + "\n\n")
                            
                        except Exception as e:
                            logger.error(f"Error processing ticket {ticket.key}: {e}")
                            # Ensure list consistency even if ticket processing fails
                            self._ensure_list_consistency(
                                ids_list, feature_list, test_data_list, third_field_list,
                                creation_dates, update_dates
                            )
                    
                    file.write(f"\nTotal {ticket_type} tickets processed: {len(ids_list)}\n")
                    file.write(f"Reference date used: {reference_date}\n")
                    file.write(f"File generated on: {pd.Timestamp.now()}\n")
                    
            except Exception as e:
                logger.error(f"Error writing to file {imported_file}: {e}")
                return None, [], [], pd.DataFrame(), None

            # Find the most recent date among all creation and update dates
            most_recent_date_formatted = None
            try:
                if all_datetime_objects:
                    most_recent_date = max(all_datetime_objects)
                    most_recent_date_formatted = most_recent_date.strftime('%Y-%m-%d %H:%M:%S')
                    logger.info(f"Most recent date found: {most_recent_date_formatted}")
                else:
                    logger.info("No valid dates found in extracted tickets")
            except Exception as e:
                logger.error(f"Error finding most recent date: {e}")

            # Create DataFrame with all extracted ticket data
            try:
                df = self._create_dataframe_for_ticket_type(
                    ticket_type, ids_list, titles_list, description_list,
                    feature_list, test_data_list, third_field_list,
                    creation_dates, update_dates
                )
                
                logger.info(f"\nExtraction Summary:")
                logger.info(f"{ticket_type} tickets extracted: {len(ids_list)}")
                logger.info(f"Reference date: {reference_date}")
                logger.info(f"Most recent date among all tickets: {most_recent_date_formatted or 'None'}")
                logger.info(f"DataFrame shape: {df.shape}")
                logger.info(f"Ticket details saved to: {imported_file}")
                
            except Exception as e:
                logger.error(f"Error creating DataFrame: {e}")
                df = pd.DataFrame()

            return imported_file, ids_list, titles_list, df, most_recent_date_formatted
            
        except Exception as e:
            logger.error(f"Error in jira_import_tickets_by_date: {e}")
            return None, [], [], pd.DataFrame(), None

    def _set_error_values_for_ticket_type(self, ticket_type: str, field_name: str, current_feature: str, current_test_data: str, current_third_field: str):
        """Helper method to set error values based on ticket type and field name."""
        if "Test" in ticket_type:
            if field_name == "Feature":
                current_feature = "Error retrieving field"
            elif "donnees" in field_name.lower() or "data" in field_name.lower():
                current_test_data = "Error retrieving field"
        elif "Story" in ticket_type:
            if field_name == "Regles de Gestion":
                current_feature = "Error retrieving field"
            elif field_name == "Criteres d'Acceptance":
                current_test_data = "Error retrieving field"
            elif field_name == "Parametres":
                current_third_field = "Error retrieving field"

    def _set_default_values_for_ticket_type(self, ticket_type: str, field_name: str, current_feature: str, current_test_data: str, current_third_field: str):
        """Helper method to set default values based on ticket type and field name."""
        if "Test" in ticket_type:
            if field_name == "Feature":
                current_feature = "Field not found"
            elif "donnees" in field_name.lower() or "data" in field_name.lower():
                current_test_data = "Field not found"
        elif "Story" in ticket_type:
            if field_name == "Regles de Gestion":
                current_feature = "Field not found"
            elif field_name == "Criteres d'Acceptance":
                current_test_data = "Field not found"
            elif field_name == "Parametres":
                current_third_field = "Field not found"

    def _ensure_list_consistency(self, ids_list: List[str], feature_list: List[str], test_data_list: List[str], 
                            third_field_list: List[str], creation_dates: List[str], update_dates: List[str]):
        """Helper method to ensure all lists maintain the same length."""
        target_length = len(ids_list)
        
        if len(feature_list) < target_length:
            feature_list.append("Error processing ticket")
        if len(test_data_list) < target_length:
            test_data_list.append("Error processing ticket")
        if len(third_field_list) < target_length:
            third_field_list.append("Error processing ticket")
        if len(creation_dates) < target_length:
            creation_dates.append("Error processing ticket")
        if len(update_dates) < target_length:
            update_dates.append("Error processing ticket")

    def _create_dataframe_for_ticket_type(self, ticket_type: str, ids_list: List[str], titles_list: List[str], 
                                        description_list: List[str], feature_list: List[str], test_data_list: List[str],
                                        third_field_list: List[str], creation_dates: List[str], update_dates: List[str]) -> pd.DataFrame:
        """Helper method to create DataFrame based on ticket type."""
        if "Test" in ticket_type:
            return pd.DataFrame({
                'id': ids_list,
                'Feature': feature_list,
                'Scenario': titles_list,
                'Steps': description_list,
                'Test Data': test_data_list,
                'Created': creation_dates,
                'Updated': update_dates
            })
        elif "Story" in ticket_type:
            return pd.DataFrame({
                'US_ID': ids_list,
                'Titre': titles_list,
                'Description': description_list,
                'Règles de gestion': feature_list,
                "Critères d'acceptance": test_data_list,
                'Paramètres': third_field_list,
                'Created': creation_dates,
                'Updated': update_dates
            })
        else:
            return pd.DataFrame({
                'id': ids_list,
                'Custom_Field_1': feature_list,
                'Title': titles_list,
                'Description': description_list,
                'Custom_Field_2': test_data_list,
                'Custom_Field_3': third_field_list,
                'Created': creation_dates,
                'Updated': update_dates
            })
                
    def extract_scenarios_and_titles_description(self, test_case):
        """
        Extract scenarios and their titles/descriptions from test case text.
        Supports multiple scenario formats including French and English patterns.
        
        Args:
            test_case (str): The test case text containing scenarios
            
        Returns:
            list: List of dictionaries with 'title' and 'description' keys for each scenario
        """
        # Improved regular expression to match scenarios
        # pattern = r"(Scenario \d+ : [^\n]+\n(?:.*?))(?=\n*Scenario \d+ :|\Z)"
        pattern = r"((?:Scenario|Scénario|TC|Test Case|Cas de Test|Cas Passant|Cas non Passant)\s*\d+\s*(?:\s*:)?\s*[^\n]+\n(?:.*?))(?=\n*(?:Scenario|Scénario|TC|Test Case|Cas de Test|Cas Passant|Cas non Passant)\s*\d+|\Z)"
    
        # Extracting all scenarios
        scenarios = re.findall(pattern, test_case, re.DOTALL)
    
        scenario_data = []
        for scenario in scenarios:
            # Clean up the scenario text
            scenario_text = scenario.strip()
        
            # Split the first line (title) from the rest (description)
            lines = scenario_text.split('\n', 1)
        
            title = lines[0].strip()  # First line is the title
            description = lines[1].strip() if len(lines) > 1 else ""
        
            scenario_data.append({
                "title": title,
                "description": description
            })
    
        return scenario_data
    
    def update_issue_priority(self, issue_id: str, priority: str) -> bool:
        """
        Update the priority of a JIRA issue.
        
        Args:
            issue_id: The JIRA issue key or ID
            priority: The priority name to set
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not self.jira:
                raise ValueError("JIRA connection not established. Call connect_to_jira() first.")
                
            issue = self.jira.issue(issue_id)
            issue.update(fields={"priority": {"name": priority}})
            logger.info(f"Successfully updated priority for issue {issue_id} to {priority}")
            return True
        except Exception as e:
            logger.error(f"Failed to update priority for issue {issue_id}: {e}")
            return False

    def create_link_tickets(self, user_paths, df_res: pd.DataFrame, 
                        link_type: str = "Relates") -> bool:
        """
        Create and link test case tickets based on DataFrame content.
        
        Args:
            credentials: JIRA credentials configuration
            df_res: DataFrame containing test case data with columns 'id_US' and 'Test Cases'
            link_type: Type of link to create between issues
            
        Returns:
            bool: True if all operations successful, False otherwise
        """
        try:
            # Establish connection
            if not self.jira:
                self._connect_to_jira(user_paths)
                
            project_key = user_paths['US_project_key']
            issue_type = getattr(user_paths, 'issue_type', 'Test')
            output_status = getattr(user_paths, 'output_ticket_status', None)
            
            logger.info("Starting to create and link tickets...")
            
            # Validate project connection
            try:
                project = self.jira.project(project_key)
                logger.info(f"Connected to project: {project_key}")
            except Exception as e:
                logger.error(f"Failed to connect to project {project_key}: {e}")
                return False

            success_count = 0
            total_scenarios = 0
            
            # Process each row in the DataFrame
            for index, row in df_res.iterrows():
                try:
                    target_issue_key = row['id_US']
                    test_case_content = row['Test Cases']
                    
                    # Extract scenarios (assuming this function exists elsewhere)
                    scenario_data = self.extract_scenarios_and_titles_description(test_case_content)
                    total_scenarios += len(scenario_data)
                    
                    logger.info(f"Processing row {index + 1} with {len(scenario_data)} scenarios")
                    
                    for idx, data in enumerate(scenario_data, start=1):
                        if self._create_and_link_test_case(
                            data, project_key, issue_type, output_status, 
                            target_issue_key, link_type
                        ):
                            success_count += 1
                            
                except Exception as e:
                    logger.error(f"Error processing row {index + 1}: {e}")
                    continue
            
            logger.info(f"Successfully created and linked {success_count}/{total_scenarios} test cases")
            return success_count == total_scenarios
            
        except Exception as e:
            logger.error(f"Failed to create and link tickets: {e}")
            return False

    def create_endtoend_tickets(self, user_paths, 
                            df_main_flow: pd.DataFrame, 
                            df_edge_cases: pd.DataFrame) -> bool:
        """
        Create End-to-End test tickets from main flow and edge cases DataFrames.
        
        Args:
            credentials: JIRA credentials configuration
            df_main_flow: DataFrame containing main flow test cases
            df_edge_cases: DataFrame containing edge case test cases
            
        Returns:
            bool: True if all tickets created successfully, False otherwise
        """
        try:
            # Establish connection
            if not self.jira:
                self._connect_to_jira(user_paths)
                
            project_key = user_paths['US_project_key']
            issue_type = getattr(user_paths, 'issue_type', 'Test')
            
            logger.info("Starting to create EndToEnd Jira tickets...")
            
            def create_tickets_from_df(df: pd.DataFrame, sheet_name: str) -> int:
                """Helper function to create tickets from a DataFrame"""
                success_count = 0
                logger.info(f"Processing sheet: {sheet_name}")
                
                for index, row in df.iterrows():
                    try:
                        summary = row.get('title', f"E2E Test Case {index + 1}")
                        description = row.get('detailed_steps', 'No description provided')
                        
                        issue_dict = {
                            'project': {'key': project_key},
                            'summary': summary,
                            'description': description,
                            'issuetype': {'name': issue_type},
                            'labels': ['EndToEnd'],  # Sets the "Etiquette" field via labels
                        }
                        
                        new_issue = self.jira.create_issue(fields=issue_dict)
                        logger.info(f"Created Jira issue {new_issue.key} from sheet '{sheet_name}'")
                        success_count += 1
                        
                    except Exception as e:
                        logger.error(f"Failed to create issue for row {index + 1} in sheet '{sheet_name}': {e}")
                        continue
                        
                return success_count
            
            # Create tickets from both sheets
            main_flow_count = create_tickets_from_df(df_main_flow, "E2E Main Flow")
            edge_cases_count = create_tickets_from_df(df_edge_cases, "E2E Edge Cases")
            
            total_created = main_flow_count + edge_cases_count
            total_expected = len(df_main_flow) + len(df_edge_cases)
            
            logger.info(f"Ticket creation completed. Created {total_created}/{total_expected} tickets")
            return total_created == total_expected
            
        except Exception as e:
            logger.error(f"Failed to create EndToEnd tickets: {e}")
            return False

    def _create_and_link_test_case(self, scenario_data: Dict, project_key: str, 
                                issue_type: str, output_status: Optional[str],
                                target_issue_key: str, link_type: str) -> bool:
        """
        Helper method to create a single test case and link it to a target issue.
        
        Args:
            scenario_data: Dictionary containing 'title' and 'description'
            project_key: JIRA project key
            issue_type: Type of issue to create
            output_status: Status to transition the issue to (optional)
            target_issue_key: Key of the issue to link to
            link_type: Type of link to create
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            summary = scenario_data.get('title', 'Test Case')
            description = scenario_data.get('description', 'No description provided')
            
            # Create the new issue
            issue_dict = {
                'project': {'key': project_key},
                'summary': summary,
                'description': description,
                'issuetype': {'name': issue_type},
            }
            
            new_issue = self.jira.create_issue(fields=issue_dict)
            logger.info(f"Test case '{summary}' created with key: {new_issue.key}")
            
            # Transition to desired status if specified
            if output_status:
                self._transition_issue_to_status(new_issue, output_status)
            
            # Link the new issue to the target issue
            self._create_issue_link(new_issue.key, target_issue_key, link_type)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to create and link test case '{scenario_data.get('title', 'Unknown')}': {e}")
            return False

    def _transition_issue_to_status(self, issue, target_status: str) -> bool:
        """
        Helper method to transition an issue to a specific status.
        
        Args:
            issue: JIRA issue object
            target_status: Status name to transition to
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            transitions = self.jira.transitions(issue)
            logger.debug(f"Available transitions for issue {issue.key}: {[t['name'] for t in transitions]}")
            
            for transition in transitions:
                if transition['name'] == target_status:
                    self.jira.transition_issue(issue, transition['id'])
                    logger.info(f"Transitioned issue {issue.key} to status: {target_status}")
                    return True
            
            logger.warning(f"No transition found for status: {target_status}")
            return False
            
        except Exception as e:
            logger.error(f"Failed to transition issue {issue.key}: {e}")
            return False

    def _create_issue_link(self, source_issue_key: str, target_issue_key: str, 
                        link_type: str) -> bool:
        """
        Helper method to create a link between two issues.
        
        Args:
            source_issue_key: Key of the source issue
            target_issue_key: Key of the target issue
            link_type: Type of link to create
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.jira.create_issue_link(
                type=link_type,
                inwardIssue=source_issue_key,
                outwardIssue=target_issue_key
            )
            logger.info(f"Linked {source_issue_key} to {target_issue_key} with link type '{link_type}'")
            return True
            
        except Exception as e:
            logger.error(f"Failed to link {source_issue_key} to {target_issue_key}: {e}")
            return False

    def Jira_import_Target_US(
        self, 
        user_id: str,
        user_paths: Dict[str, str], 
        project_folder_path: str,
        Checker : Optional[bool] = True
    ) -> Tuple[Optional[str], List[str], List[str], pd.DataFrame]:
        """
        Import target User Story tickets from a Jira project based on status filter and Story issue type.
        
        Args:
            user_paths: Dictionary containing Jira configuration paths and settings
            project_folder_path: Path to the project folder where files will be saved
            credentials: Optional JIRA credentials
            
        Returns:
            tuple: (imported_US_file_path, ids_list, titles_list, dataframe)
        """
        try:
            if not self.jira:
                self._connect_to_jira(user_paths)
            
            # Get configuration from user_paths
            input_ticket_name_field = user_paths.get('US_input_name_field')
            project_key = user_paths.get('US_project_key')
            sprint = user_paths.get('US_sprint')
            assignee = user_paths.get('US_assignee')
            etiquette = user_paths.get('US_etiquette')


            if not input_ticket_name_field:
                logger.error("Missing 'US_input_name_field' in user_paths configuration")
                return None, [], [], pd.DataFrame()
            elif input_ticket_name_field not in ['To Do', 'In Progress', 'Done', 'A faire', 'Terminé', 'En cours']:
                logger.error(f"Invalid 'US_input_name_field': {input_ticket_name_field}. Expected one of ['To Do', 'In Progress', 'Done']")
                return None, [], [], pd.DataFrame()
            
            if not project_key:
                logger.error("Missing 'US_project_key' in user_paths configuration")
                return None, [], [], pd.DataFrame()
            
            if input_ticket_name_field == 'A faire' :
                input_ticket_name_field = 'To Do'
            elif input_ticket_name_field == 'Terminé':
                input_ticket_name_field = 'Done'
            elif input_ticket_name_field == 'En cours':
                input_ticket_name_field = 'In Progress'

            # Validate project access
            try:
                project = self.jira.project(project_key)
                logger.info(f"Successfully accessed project: {project.name} ({project_key})")
            except Exception as e:
                logger.error(f"Error accessing project {project_key}: {e}")
                return None, [], [], pd.DataFrame()

            # Define path where the text file of US will be saved
            imported_US = os.path.join(project_folder_path, "Imported_Target_US.txt")
            
            # Initialize lists to store extracted data
            ids_list = []
            titles_list = []
            description_list = []
            RG_list = []
            CA_list = []

            # Retrieve JIRA FIELDS AND MAP THEM
            try:
                fields = self.jira.fields()
                field_name_to_id = {field['name']: field['id'] for field in fields}
                logger.info("Successfully retrieved Jira field mappings")
            except Exception as e:
                logger.error(f"Error retrieving Jira fields: {e}")
                return None, [], [], pd.DataFrame()

           

            # Define JQL query to get Story tickets from the project with specific status
            jql_query = f'project = {project_key} AND issuetype = "Story" AND statusCategory = "{input_ticket_name_field}"  '

            if sprint :
                jql_query += f' AND sprint = "{sprint}"'
            if assignee:
                jql_query += f' AND assignee = "{assignee}"'
            if etiquette:
                jql_query += f' AND labels = "{etiquette}"'

            logger.info(f"JQL Query: {jql_query}")
            print(f"Debug - JQL Query: '{jql_query}'")
        

            try:
                # Search for tickets in the project
                tickets = self.jira.search_issues(jql_query, maxResults=1000, expand='fields', fields='*all')
                
                logger.info(f"Found {len(tickets)} Story tickets with status '{input_ticket_name_field}' in project {project_key}")

                
                if len(tickets) == 0:
                    logger.warning(f"No Story tickets with status '{input_ticket_name_field}' found in project {project_key}")
                    return None, [], [], pd.DataFrame()
                    
            except Exception as e:
                logger.error(f"Error searching for Story tickets in project {project_key}: {e}")
                return None, [], [], pd.DataFrame()
            
            # Process tickets
            matching_tickets_count = len(tickets)
            
            try:
                with open(imported_US, "w", encoding='utf-8') as file:
                    file.write(f"Target User Stories extracted from Jira Project: {project_key}\n")
                    file.write(f"Filter: Issue Type = 'Story' AND Status = '{input_ticket_name_field}'\n")
                    file.write(f"Total matching tickets found: {len(tickets)}\n")
                    file.write("=" * 60 + "\n\n")
                    
                    # Process each ticket
                    for i, ticket in enumerate(tickets, 1):
                        logger.debug(f"Processing ticket {i}/{len(tickets)}: {ticket.key}")
                        
                        try:
                            # Extract basic ticket information
                            ticket_key = ticket.key
                            title = ticket.fields.summary if ticket.fields.summary else ""
                            description = ticket.fields.description if ticket.fields.description else ""
                            ticket_status = ticket.fields.status if ticket.fields.status else ""
                            
                            # Store basic information in lists
                            ids_list.append(ticket_key)
                            titles_list.append(title)

                            if Checker:
                                try:
                                    RG_CA_US_cleaned_content, RG_CA_US_final_path = files_service.Extract_RG_CA_US_from_Description(description, project_key, user_id)
                                    treated_user_story_description = RG_CA_US_cleaned_content.get("User Story Description", "Not provided")
                                    acceptance_criteria = RG_CA_US_cleaned_content.get("Acceptance Criteria", "Not provided")
                                    business_rules = RG_CA_US_cleaned_content.get("Business Rules", "Not provided")

                                    # Use treated description instead of original
                                    description_list.append(treated_user_story_description)
                                    RG_list.append(business_rules)
                                    CA_list.append(acceptance_criteria)

                                    file.write(f"Ticket ID: {ticket_key}\n")
                                    file.write(f"Title: {title}\n")
                                    file.write(f"Description: {treated_user_story_description}\n")
                                    file.write(f"Business Rules: {business_rules}\n")
                                    file.write(f"Acceptance Criteria: {acceptance_criteria}\n")
                                    file.write(f"Status: {ticket_status}\n")
                                    file.write(f"Issue Type: {ticket.fields.issuetype.name}\n")
                                    file.write("\n" + "=" * 40 + "\n\n")

                                except Exception as extraction_error:
                                    logger.error(f"Error extracting RG/CA for ticket {ticket_key}: {extraction_error}")
                                    # Fallback to original description
                                    description_list.append(description)
                                    RG_list.append("Error extracting business rules")
                                    CA_list.append("Error extracting acceptance criteria")

                                    file.write(f"Ticket ID: {ticket_key}\n")
                                    file.write(f"Title: {title}\n")
                                    file.write(f"Description: {description}\n")
                                    file.write(f"Business Rules: Error extracting business rules\n")
                                    file.write(f"Acceptance Criteria: Error extracting acceptance criteria\n")
                                    file.write(f"Status: {ticket_status}\n")
                                    file.write(f"Issue Type: {ticket.fields.issuetype.name}\n")
                                    file.write("\n" + "=" * 40 + "\n\n")

                            else: 
                                # Use original description when Checker is False
                                description_list.append(description)
                                RG_list.append("")
                                CA_list.append("")

                                # Write basic information to file
                                file.write(f"Ticket ID: {ticket_key}\n")
                                file.write(f"Title: {title}\n")
                                file.write(f"Description: {description}\n")
                                file.write(f"Status: {ticket_status}\n")
                                file.write(f"Issue Type: {ticket.fields.issuetype.name}\n")
                                file.write("\n" + "=" * 40 + "\n\n")

                            
                        except Exception as e:
                            logger.error(f"Error processing ticket {ticket.key}: {e}")
                            # Ensure list consistency even if ticket processing fails
                            if len(ids_list) > len(description_list):
                                description_list.append("Error processing ticket")
                            if len(ids_list) > len(RG_list):
                                RG_list.append("Error processing ticket")
                            if len(ids_list) > len(CA_list):
                                CA_list.append("Error processing ticket")
                           
                    
                    file.write(f"\nTotal Story tickets matching status '{input_ticket_name_field}': {matching_tickets_count}\n")
                    file.write(f"Total tickets processed successfully: {len(ids_list)}\n")
                    file.write(f"File generated on: {pd.Timestamp.now()}\n")
                    
            except Exception as e:
                logger.error(f"Error writing to file {imported_US}: {e}")
                return None, [], [], pd.DataFrame()

            # Create DataFrame with all extracted User Story data
            try:
                if Checker == True: 
                    df = pd.DataFrame({
                        'US_ID': ids_list,
                        'Titre': titles_list,
                        'Description': description_list,
                        'Règles de Gestion': RG_list,
                        'Critères Acceptance': CA_list
                    })
                else: 
                    df = pd.DataFrame({
                        'US_ID': ids_list,
                        'Titre': titles_list,
                        'Description': description_list,
                    })
                    
                logger.info(f"Target US Extraction Summary:")
                logger.info(f"Total Story tickets with status '{input_ticket_name_field}': {matching_tickets_count}")
                logger.info(f"Successfully processed User Stories: {len(ids_list)}")
                logger.info(f"DataFrame shape: {df.shape}")
                logger.info(f"User Story details saved to: {imported_US}")
                
            except Exception as e:
                logger.error(f"Error creating DataFrame: {e}")
                df = pd.DataFrame()

            return imported_US, ids_list, titles_list, df
            
        except Exception as e:
            logger.error(f"Error in Jira_import_Target_US: {e}")
            return None, [], [], pd.DataFrame()

    def Jira_import_Target_US_d(
        self, 
        user_id: str,
        user_paths: Dict[str, str], 
        project_folder_path: str,
        Checker : Optional[bool] = True
    ) -> Tuple[Optional[str], List[str], List[str], pd.DataFrame]:
        """
        Import target User Story tickets from a Jira project based on status filter and Story issue type.
        
        Args:
            user_paths: Dictionary containing Jira configuration paths and settings
            project_folder_path: Path to the project folder where files will be saved
            credentials: Optional JIRA credentials
            
        Returns:
            tuple: (imported_US_file_path, ids_list, titles_list, dataframe)
        """
        try:
            if not self.jira:
                self._connect_to_jira(user_paths)
            
            # Get configuration from user_paths
            input_ticket_name_field = user_paths.get('US_input_name_field')
            project_key = user_paths.get('US_project_key')
            sprint = user_paths.get('US_sprint')
            assignee = user_paths.get('US_assignee')
            etiquette = user_paths.get('US_etiquette')


            if not input_ticket_name_field:
                logger.error("Missing 'US_input_name_field' in user_paths configuration")
                return None, [], [], pd.DataFrame()
            elif input_ticket_name_field not in ['To Do', 'In Progress', 'Done', 'A faire', 'Terminé', 'En cours']:
                logger.error(f"Invalid 'US_input_name_field': {input_ticket_name_field}. Expected one of ['To Do', 'In Progress', 'Done']")
                return None, [], [], pd.DataFrame()
            
            if not project_key:
                logger.error("Missing 'US_project_key' in user_paths configuration")
                return None, [], [], pd.DataFrame()
            
            if input_ticket_name_field == 'A faire' :
                input_ticket_name_field = 'To Do'
            elif input_ticket_name_field == 'Terminé':
                input_ticket_name_field = 'Done'
            elif input_ticket_name_field == 'En cours':
                input_ticket_name_field = 'In Progress'

            # Validate project access
            try:
                project = self.jira.project(project_key)
                logger.info(f"Successfully accessed project: {project.name} ({project_key})")
            except Exception as e:
                logger.error(f"Error accessing project {project_key}: {e}")
                return None, [], [], pd.DataFrame()

            # Define path where the text file of US will be saved
            imported_US = os.path.join(project_folder_path, "Imported_Target_US.txt")
            
            # Initialize lists to store extracted data
            ids_list = []
            titles_list = []
            description_list = []
            RG_list = []
            CA_list = []

            # Retrieve JIRA FIELDS AND MAP THEM
            try:
                fields = self.jira.fields()
                field_name_to_id = {field['name']: field['id'] for field in fields}
                logger.info("Successfully retrieved Jira field mappings")
            except Exception as e:
                logger.error(f"Error retrieving Jira fields: {e}")
                return None, [], [], pd.DataFrame()

           

            # Define JQL query to get Story tickets from the project with specific status
            jql_query = f'project = {project_key} AND issuetype = "Story" AND statusCategory = "{input_ticket_name_field}"  '

            if sprint :
                jql_query += f' AND sprint = "{sprint}"'
            if assignee:
                jql_query += f' AND assignee = "{assignee}"'
            if etiquette:
                jql_query += f' AND labels = "{etiquette}"'

            logger.info(f"JQL Query: {jql_query}")
            print(f"Debug - JQL Query: '{jql_query}'")
        

            try:
                # Search for tickets in the project
                tickets = self.jira.search_issues(jql_query, maxResults=1000, expand='fields', fields='*all')
                
                logger.info(f"Found {len(tickets)} Story tickets with status '{input_ticket_name_field}' in project {project_key}")

                
                if len(tickets) == 0:
                    logger.warning(f"No Story tickets with status '{input_ticket_name_field}' found in project {project_key}")
                    return None, [], [], pd.DataFrame()
                    
            except Exception as e:
                logger.error(f"Error searching for Story tickets in project {project_key}: {e}")
                return None, [], [], pd.DataFrame()
            
            # Process tickets
            matching_tickets_count = len(tickets)
            
            try:
                with open(imported_US, "w", encoding='utf-8') as file:
                    file.write(f"Target User Stories extracted from Jira Project: {project_key}\n")
                    file.write(f"Filter: Issue Type = 'Story' AND Status = '{input_ticket_name_field}'\n")
                    file.write(f"Total matching tickets found: {len(tickets)}\n")
                    file.write("=" * 60 + "\n\n")
                    
                    # Process each ticket
                    for i, ticket in enumerate(tickets, 1):
                        logger.debug(f"Processing ticket {i}/{len(tickets)}: {ticket.key}")
                        
                        try:
                            # Extract basic ticket information
                            ticket_key = ticket.key
                            title = ticket.fields.summary if ticket.fields.summary else ""
                            description = ticket.fields.description if ticket.fields.description else ""
                            ticket_status = ticket.fields.status if ticket.fields.status else ""
                            
                            # Store basic information in lists
                            ids_list.append(ticket_key)
                            titles_list.append(title)

                            if Checker :
                                RG_CA_US_cleaned_content, RG_CA_US_final_path = files_service.Extract_RG_CA_US_from_Description(description, project_key, user_id)
                                treated_user_story_description = RG_CA_US_cleaned_content.get("User Story Description", "Not provided")
                                acceptance_criteria = RG_CA_US_cleaned_content.get("Acceptance Criteria", "Not provided")
                                business_rules = RG_CA_US_cleaned_content.get("Business Rules", "Not provided")

                                RG_list.append(business_rules)
                                CA_list.append(acceptance_criteria)
                                description_list.append(treated_user_story_description)

                                file.write(f"Ticket ID: {ticket_key}\n")
                                file.write(f"Title: {title}\n")
                                file.write(f"Description: {treated_user_story_description}\n")
                                file.write(f"Business Rules: {business_rules}\n")
                                file.write(f"Acceptance Criteria: {acceptance_criteria}\n")

                                file.write(f"Status: {ticket_status}\n")
                                file.write(f"Issue Type: {ticket.fields.issuetype.name}\n")
                                
                                file.write("\n" + "=" * 40 + "\n\n")

                            else : 
                                description_list.append(description)

                                # Write basic information to file
                                file.write(f"Ticket ID: {ticket_key}\n")
                                file.write(f"Title: {title}\n")
                                file.write(f"Description: {description}\n")
                                file.write(f"Status: {ticket_status}\n")
                                file.write(f"Issue Type: {ticket.fields.issuetype.name}\n")

                                file.write("\n" + "=" * 40 + "\n\n")

                            
                        except Exception as e:
                            logger.error(f"Error processing ticket {ticket.key}: {e}")
                           
                    
                    file.write(f"\nTotal Story tickets matching status '{input_ticket_name_field}': {matching_tickets_count}\n")
                    file.write(f"Total tickets processed successfully: {len(ids_list)}\n")
                    file.write(f"File generated on: {pd.Timestamp.now()}\n")
                    
            except Exception as e:
                logger.error(f"Error writing to file {imported_US}: {e}")
                return None, [], [], pd.DataFrame()

            # Create DataFrame with all extracted User Story data
            try:
                if Checker == True : 
                    df = pd.DataFrame({
                        'US_ID': ids_list,
                        'Titre': titles_list,
                        'Description': description_list,
                        'Règles de Gestion': RG_list,
                        'Critères Acceptance': CA_list
                    })
                else : 
                        df = pd.DataFrame({
                        'US_ID': ids_list,
                        'Titre': titles_list,
                        'Description': description_list,
                    })
                    
                logger.info(f"Target US Extraction Summary:")
                logger.info(f"Total Story tickets with status '{input_ticket_name_field}': {matching_tickets_count}")
                logger.info(f"Successfully processed User Stories: {len(ids_list)}")
                logger.info(f"DataFrame shape: {df.shape}")
                logger.info(f"User Story details saved to: {imported_US}")
                
            except Exception as e:
                logger.error(f"Error creating DataFrame: {e}")
                df = pd.DataFrame()

            return imported_US, ids_list, titles_list, df
            
        except Exception as e:
            logger.error(f"Error in Jira_import_Target_US: {e}")
            return None, [], [], pd.DataFrame()