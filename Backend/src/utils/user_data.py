import json
import os
from typing import Dict

from src.utils.config import settings

USER_DATA_FILE = settings.USER_PATHS_JSON_FILE

class UserDataManager:
    def __init__(self, folder_path: str = settings.USER_PATHS_JSON):
        self.folder_path = folder_path
        os.makedirs(self.folder_path, exist_ok=True)
        self.user_paths = {}  # will load per-user when needed

    def _get_file_path(self, us_user_id: str) -> str:
        if not us_user_id:
            raise ValueError("us_user_id is required to save/load user data")
        return os.path.join(self.folder_path, f"User_data_{us_user_id}.json")

    def _load_data(self, us_user_id: str) -> Dict[str, str]:
        file_path = self._get_file_path(us_user_id)
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                return json.load(f)
        return {}

    def _save_data(self, us_user_id: str) -> None:
        file_path = self._get_file_path(us_user_id)
        with open(file_path, "w") as f:
            json.dump(self.user_paths, f, indent=2)

    # --------------------------------------
    def save_jira_credentials(self, jira_url: str, jira_username: str, us_user_id: str) -> None:
        self.user_paths = self._load_data(us_user_id)
        self.user_paths["jira_url"] = jira_url
        self.user_paths["jira_username"] = jira_username
        self._save_data(us_user_id)

    def save_project_key(self, project_key: str, key_type: str, us_user_id: str) -> None:
        if key_type not in ["US", "TC"]:
            raise ValueError("Invalid key type. Must be 'US' or 'TC'.")
        self.user_paths = self._load_data(us_user_id)
        self.user_paths[f"{key_type}_project_key"] = project_key
        self._save_data(us_user_id)

    def save_test_automation_config(self, us_user_id: str, tests_to_automate_name_field: str = None, application_link_to_test: str = None) -> None:
        self.user_paths = self._load_data(us_user_id)
        if tests_to_automate_name_field is not None:
            self.user_paths["Tests_to_automate_name_field"] = tests_to_automate_name_field
        if application_link_to_test is not None:
            self.user_paths["Application_link_to_test"] = application_link_to_test
        self._save_data(us_user_id)

    def save_user_story_config(
        self,
        us_user_id: str,
        us_project_key: str = None,
        us_output_name_field: str = None,
        us_input_name_field: str = None,
        us_etiquette: str = None,
        us_assignee: str = None,
        us_sprint: str = None
    ) -> None:
        self.user_paths = self._load_data(us_user_id)
        if us_project_key is not None:
            self.user_paths['us_project_key'] = us_project_key
        if us_output_name_field is not None:
            self.user_paths["US_output_name_field"] = us_output_name_field
        if us_input_name_field is not None:
            self.user_paths["US_input_name_field"] = us_input_name_field
        if us_etiquette is not None:
            self.user_paths["US_etiquette"] = us_etiquette
        if us_assignee is not None:
            self.user_paths["US_assignee"] = us_assignee
        if us_sprint is not None:
            self.user_paths["US_sprint"] = us_sprint
        self._save_data(us_user_id)

    def save_test_case_config(self, tc_format: str = None, tc_etiquette_to_create: str = None, tc_etiquette_to_execute: str = None, user_id:str = None) -> None:
        self.user_paths = self._load_data(user_id)
        if tc_format is not None:
            self.user_paths["TC_format"] = tc_format
        if tc_etiquette_to_create is not None:
            self.user_paths["TC_etiquette_to_create"] = tc_etiquette_to_create
        if tc_etiquette_to_execute is not None:
            self.user_paths["TC_etiquette_to_execute"] = tc_etiquette_to_execute
       
        self._save_data(user_id)

    def get_field_value(self, field_name: str) -> str:
        """Get the value of a specific field"""
        return self.user_paths.get(field_name, "")

    def load_user_paths(self) -> Dict[str, str]:
        return self.user_paths