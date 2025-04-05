# ui.py

"""Functions for user interface interactions and display"""

import os
import sys
import sqlite3 # For sqlite3.Row type hint
from typing import List, Tuple, Optional, TYPE_CHECKING
if TYPE_CHECKING:
    from database import JournalDatabase
    
#Clear Console
def clear_console():
    """Clears the terminal screen."""
    command = 'cls' if os.name == 'nt' else 'clear'
    os.system(command)

#UI Display Functions
def display_entries(entries: List[sqlite3.Row], oldest_first: bool = True):
    """Format and display entries, including their IDs."""
    if not entries:
        return

    sort_description = "oldest to newest" if oldest_first else "newest to oldest"
    print(f"\n===== Entries (sorted {sort_description}) =====")
    print("=" * 50)
    for entry in entries:
        print(f"ID: {entry['EntryID']}")
        print(f"[{entry['EntryDate']}]")
        print(f"{entry['Detail']}")
        print("-" * 50)

#UI Input Functions
def select_subject(db: 'JournalDatabase', action_description: str = "") -> Tuple[bool, Optional[str], str]:
    """
    Utility function to handle subject selection by either ID or name.
    Returns (success_status, subject_name, message)
    """
    subjects = db.get_all_subjects()
    if not subjects:
        print("No subjects found. Please add a subject first.")
        return False, None, "No subjects available."

    print("\nAvailable subjects:")
    subject_map_id_to_name = {}
    subject_map_name_to_id = {}
    for subject in subjects:
        subject_id = subject['SubjectID']
        subject_name = subject['SubjectName']
        print(f"ID: {subject_id} - {subject_name}")
        subject_map_id_to_name[subject_id] = subject_name
        subject_map_name_to_id[subject_name.lower()] = subject_id

    if action_description:
        print(f"\nSelect subject to {action_description}")

    while True:
        selection_method = input("\nSelect by (1) ID or (2) Name? [2]: ").strip() or '2'

        if selection_method == '1':
            id_input = input("Enter subject ID: ").strip()
            try:
                subject_id = int(id_input)
                if subject_id in subject_map_id_to_name:
                    subject_name = subject_map_id_to_name[subject_id]
                    print(f"Selected subject: '{subject_name}' (ID: {subject_id})")
                    return True, subject_name, "Subject found by ID."
                else:
                    print(f"Error: No subject found with ID {subject_id}.")
                    continue
            except ValueError:
                print("Invalid ID. Please enter a number.")
                continue

        elif selection_method == '2':
            subject_name = input("Enter subject name: ").strip()
            if not subject_name:
                print("Subject name cannot be empty.")
                continue

            if subject_name.lower() not in subject_map_name_to_id:
                 print(f"Note: Subject '{subject_name}' doesn't exist yet (it might be created if needed by the action).")
            return True, subject_name, "Subject selected by name."
        else:
            print("Invalid selection. Please choose 1 or 2.")

# EOF #
