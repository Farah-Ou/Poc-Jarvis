"""
src/utils/ticket_history_manager_utils.py - Ticket History Management Service
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging
from pathlib import Path


logger = logging.getLogger(__name__)
from src.utils.config import settings

class TicketHistoryManager:
    """Service for managing ticket import history records"""
    
    def __init__(self):
        """
        Initialize TicketHistoryManager with optional custom file template.
        
        Args:
            history_file_template: Custom template for history file naming.
                                 Defaults to "TC_jira_{ticket_type}_history.json"
        """
        self.history_file_template =  os.path.join(settings.Ticket_History_Management,"{jira_project_key}","Jira_{ticket_type}_history.json")

        logger.info("TicketHistoryManager initialized")

    def _get_history_file_path(self, ticket_type: str, jira_project_key: str) -> str:
        """
        Generate the history file path for a given ticket type.
        
        Args:
            ticket_type: The type of ticket (e.g., 'bug', 'feature')
        
        Returns:
            str: The formatted file path for the ticket type's history
        """
        return self.history_file_template.format(jira_project_key=jira_project_key, ticket_type=ticket_type)

    def load_ticket_history(self, ticket_type: str, jira_project_key: str) -> List[Dict[str, Any]]:
        """
        Load ticket import history from the corresponding JSON file.
        
        Args:
            ticket_type: The type of ticket to load history for
        
        Returns:
            List[Dict]: List of historical import records, empty list if file doesn't exist
        """
        history_path = self._get_history_file_path(ticket_type, jira_project_key)
        
        if not os.path.exists(history_path):
            logger.debug(f"History file not found for {ticket_type}: {history_path}")
            return []
        
        try:
            with open(history_path, "r", encoding="utf-8") as f:
                history = json.load(f)
            logger.info(f"Loaded {len(history)} records from {ticket_type} history")
            return history
        except Exception as e:
            logger.error(f"Error loading {ticket_type} history: {e}")
            logger.error(f"Error loading {ticket_type} history: {e}")
            return []

    def save_ticket_history(self, most_recent_ticket_date: Any, num_tickets: int, ticket_type: str, jira_project_key: str) -> None:
        """
        Append a new import record to the corresponding ticket type history file.
        
        Args:
            most_recent_ticket_date: The date of the most recent ticket (datetime or string)
            num_tickets: Number of tickets imported in this batch
            ticket_type: The type of ticket being saved
        """
        history_path = self._get_history_file_path(ticket_type, jira_project_key)

        current_import = {
            "import_date": datetime.now().isoformat(),
            "most_recent_ticket_date": (
                most_recent_ticket_date.isoformat()
                if hasattr(most_recent_ticket_date, 'isoformat')
                else most_recent_ticket_date
            ),
            "num_tickets": num_tickets,
            "graph_updated": False 
        }

        history = self.load_ticket_history(ticket_type, jira_project_key)
        history.append(current_import)

        try:
            # Ensure directory exists
            Path(history_path).parent.mkdir(parents=True, exist_ok=True)
            
            with open(history_path, "w", encoding="utf-8") as f:
                json.dump(history, f, indent=4)
            
            logger.info(f"Saved {ticket_type} history with {num_tickets} tickets to {history_path}")
            logger.info(f"{ticket_type.capitalize()} ticket history updated in {history_path}")
        except Exception as e:
            logger.error(f"Error saving {ticket_type} history: {e}")
            logger.error(f"Error saving {ticket_type} history: {e}")

    def load_latest_ticket_history(self, ticket_type: str, jira_project_key: str) -> Optional[Dict[str, Any]]:
        """
        Return the latest (last appended) ticket import entry.
        
        Args:
            ticket_type: The type of ticket to get latest history for
        
        Returns:
            Dict or None: The most recent import record, None if no history exists
        """
        history = self.load_ticket_history(ticket_type, jira_project_key)
        latest = history[-1] if history else None
        
        if latest:
            logger.debug(f"Latest {ticket_type} history entry: {latest['import_date']}")
        else:
            logger.debug(f"No history found for {ticket_type}")
            
        return latest

    def mark_graph_as_updated(self, ticket_type: str, jira_project_key: str) -> None:
        """
        Set the 'graph_updated' field of the latest history record to True.
        
        Args:
            ticket_type: The type of ticket to mark as graph updated
        """
        history_path = self._get_history_file_path(ticket_type, jira_project_key)
        history = self.load_ticket_history(ticket_type, jira_project_key)

        if not history:
            logger.warning(f"No history found for {ticket_type}. Nothing to update.")
            logger.warning(f"No history found for {ticket_type}. Nothing to update.")
            return

        history[-1]['graph_updated'] = True

        try:
            with open(history_path, "w", encoding="utf-8") as f:
                json.dump(history, f, indent=4)
            
            logger.info(f"Marked graph as updated for latest {ticket_type} entry")
            logger.info(f"Marked 'graph_updated' as True for latest {ticket_type} ticket entry.")
        except Exception as e:
            logger.error(f"Error updating graph status for {ticket_type}: {e}")
            logger.info(f"Error updating graph status for {ticket_type}: {e}")

    def get_ticket_history_summary(self, ticket_type: str, jira_project_key: str) -> Dict[str, Any]:
        """
        Get a summary of ticket history statistics.
        
        Args:
            ticket_type: The type of ticket to summarize
        
        Returns:
            Dict: Summary containing total imports, total tickets, and date range
        """
        history = self.load_ticket_history(ticket_type, jira_project_key)
        
        if not history:
            logger.debug(f"No history available for {ticket_type} summary")
            return {
                "total_imports": 0,
                "total_tickets": 0,
                "date_range": None,
                "last_import": None
            }
        
        total_tickets = sum(record.get("num_tickets", 0) for record in history)
        import_dates = [record.get("import_date") for record in history if record.get("import_date")]
        
        summary = {
            "total_imports": len(history),
            "total_tickets": total_tickets,
            "date_range": {
                "first_import": min(import_dates) if import_dates else None,
                "last_import": max(import_dates) if import_dates else None
            },
            "last_import": history[-1]
        }
        
        logger.info(f"Generated summary for {ticket_type}: {summary['total_imports']} imports, {summary['total_tickets']} tickets")
        return summary

    def cleanup_old_history(self, ticket_type: str, jira_project_key: str,  keep_last_n: int = 10) -> None:
        """
        Remove old history records, keeping only the most recent N entries.
        
        Args:
            ticket_type: The type of ticket to clean up
            keep_last_n: Number of most recent records to keep (default: 10)
        """
        history = self.load_ticket_history(ticket_type, jira_project_key)

        if len(history) <= keep_last_n:
            logger.debug(f"History for {ticket_type} has {len(history)} records, no cleanup needed")
            logger.info(f"History for {ticket_type} has {len(history)} records, no cleanup needed.")
            return
        
        # Keep only the last N records
        trimmed_history = history[-keep_last_n:]
        history_path = self._get_history_file_path(ticket_type, jira_project_key)  # Use a default key for cleanup

        try:
            with open(history_path, "w", encoding="utf-8") as f:
                json.dump(trimmed_history, f, indent=4)
            
            removed_count = len(history) - keep_last_n
            logger.info(f"Cleaned up {ticket_type} history: removed {removed_count} records, kept {keep_last_n}")
            logger.info(f"Cleaned up {ticket_type} history: removed {removed_count} old records, kept {keep_last_n}.")
        except Exception as e:
            logger.error(f"Error cleaning up {ticket_type} history: {e}")
            logger.error(f"Error cleaning up {ticket_type} history: {e}")

    def get_all_ticket_types(self) -> List[str]:
        """
        Get all ticket types that have history files.
        
        Returns:
            List[str]: List of ticket types with existing history files
        """
        ticket_types = []
        
        # Look for files matching the pattern
        current_dir = Path(".")
        pattern = self.history_file_template.replace("{ticket_type}", "*")
        
        for file_path in current_dir.glob(pattern):
            # Extract ticket type from filename
            filename = file_path.name
            # Remove the prefix and suffix to get ticket type
            prefix = self.history_file_template.split("{ticket_type}")[0]
            suffix = self.history_file_template.split("{ticket_type}")[1]
            
            if filename.startswith(prefix) and filename.endswith(suffix):
                ticket_type = filename[len(prefix):-len(suffix) if suffix else None]
                ticket_types.append(ticket_type)
        
        logger.debug(f"Found ticket types: {ticket_types}")
        return sorted(ticket_types)

    def get_pending_graph_updates(self, jira_project_key: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get all ticket types with pending graph updates.
        
        Returns:
            Dict: Mapping of ticket types to their pending update records
        """
        pending_updates = {}
        
        for ticket_type in self.get_all_ticket_types():
            history = self.load_ticket_history(ticket_type, jira_project_key)
            pending = [record for record in history if not record.get("graph_updated", False)]
            
            if pending:
                pending_updates[ticket_type] = pending
        
        logger.info(f"Found pending updates for {len(pending_updates)} ticket types")
        return pending_updates