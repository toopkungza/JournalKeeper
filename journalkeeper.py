import sqlite3
import sys # For sys.exit
from datetime import datetime
from typing import List, Tuple, Optional, Any # For type hinting

# --- Constants for SQL Queries ---
CREATE_SUBJECT_TABLE = """
CREATE TABLE IF NOT EXISTS Subject (
    SubjectID INTEGER PRIMARY KEY AUTOINCREMENT,
    SubjectName TEXT UNIQUE NOT NULL
)
"""

CREATE_ENTRY_TABLE = """
CREATE TABLE IF NOT EXISTS Entry (
    EntryID INTEGER PRIMARY KEY AUTOINCREMENT,
    SubjectID INTEGER NOT NULL,
    EntryDate TEXT NOT NULL,
    Detail TEXT NOT NULL,
    FOREIGN KEY (SubjectID) REFERENCES Subject(SubjectID)
)
"""

INSERT_SUBJECT = "INSERT INTO Subject (SubjectName) VALUES (?)"
SELECT_SUBJECT_ID_BY_NAME = "SELECT SubjectID FROM Subject WHERE SubjectName = ?"
SELECT_SUBJECT_NAME_BY_ID = "SELECT SubjectName FROM Subject WHERE SubjectID = ?"
INSERT_ENTRY = "INSERT INTO Entry (SubjectID, EntryDate, Detail) VALUES (?, ?, ?)"
SELECT_ENTRIES_BY_SUBJECT_NAME = """
SELECT e.EntryDate, e.Detail
FROM Entry e
JOIN Subject s ON e.SubjectID = s.SubjectID
WHERE s.SubjectName = ?
ORDER BY e.EntryDate {} -- Placeholder for ASC/DESC
"""
SELECT_ALL_SUBJECTS = "SELECT SubjectID, SubjectName FROM Subject ORDER BY SubjectName"


class DatabaseError(Exception):
    """Custom exception for database related errors."""
    pass

class JournalDatabase:
    def __init__(self, db_file: str = 'Journal.db'):
        """Initialize database connection."""
        self.db_file = db_file
        try:
            # Connect using a context manager in methods where needed,
            # or maintain a persistent connection if preferred for CLI app performance.
            # For simplicity here, we'll connect once and manage commits/closing.
            self._conn = sqlite3.connect(self.db_file)
            self._conn.row_factory = sqlite3.Row # Access columns by name
            self._create_tables()
        except sqlite3.Error as e:
            # Raise a more specific error if connection/creation fails critically
            raise DatabaseError(f"Fatal database initialization error: {e}") from e

    def _execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        """Executes SQL query with error handling."""
        try:
            cursor = self._conn.cursor()
            cursor.execute(sql, params)
            return cursor
        except sqlite3.Error as e:
            # Log or handle specific errors as needed
            print(f"Database execution error: {e} (SQL: {sql[:100]}...)")
            # Depending on severity, you might rollback or raise
            raise DatabaseError(f"Failed to execute query: {e}") from e

    def _create_tables(self):
        """Create database tables if they don't exist."""
        try:
            with self._conn: # Use connection as context manager for transaction
                self._execute(CREATE_SUBJECT_TABLE)
                self._execute(CREATE_ENTRY_TABLE)
        except sqlite3.Error as e:
            # Error during table creation is serious
            raise DatabaseError(f"Table creation error: {e}") from e

    def insert_subject(self, subject_name: str) -> Tuple[bool, str]:
        """Insert a new subject, handling duplicates gracefully."""
        try:
            with self._conn:
                self._execute(INSERT_SUBJECT, (subject_name,))
            return True, f"Subject '{subject_name}' added successfully."
        except sqlite3.IntegrityError:
            # Expected error if subject already exists (UNIQUE constraint)
            return False, f"Subject '{subject_name}' already exists."
        except DatabaseError as e:
            # Catch errors from _execute
            return False, f"Error adding subject: {e}"
        except sqlite3.Error as e:
            # Catch other potential sqlite errors
             return False, f"Unexpected error adding subject: {e}"

    def get_subject_id(self, subject_name: str, create_if_not_exists: bool = True) -> Optional[int]:
        """Get subject ID by name, optionally creating it if it doesn't exist."""
        try:
            cursor = self._execute(SELECT_SUBJECT_ID_BY_NAME, (subject_name,))
            result = cursor.fetchone()

            if result:
                return result['SubjectID'] # Access by column name
            elif create_if_not_exists:
                print(f"Subject '{subject_name}' not found, creating...")
                success, message = self.insert_subject(subject_name)
                if success:
                    # Fetch the newly created ID
                    cursor = self._execute(SELECT_SUBJECT_ID_BY_NAME, (subject_name,))
                    new_result = cursor.fetchone()
                    return new_result['SubjectID'] if new_result else None
                else:
                    print(f"Failed to create subject: {message}")
                    return None
            else:
                return None # Subject not found and not created
        except DatabaseError as e:
            print(f"Error retrieving/creating subject '{subject_name}': {e}")
            return None

    def _validate_subject_id(self, subject_id: int) -> bool:
        """Check if a subject ID exists in the database."""
        try:
            cursor = self._execute(SELECT_SUBJECT_NAME_BY_ID, (subject_id,))
            return cursor.fetchone() is not None
        except DatabaseError:
            return False # Assume invalid if query fails

    def insert_entry(self, subject_identifier: Any, detail: str, entry_date: Optional[str] = None) -> Tuple[bool, str]:
        """Insert a new entry, allowing subject by name (str) or ID (int)."""
        if entry_date is None:
            entry_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        subject_id: Optional[int] = None

        if isinstance(subject_identifier, int):
            if self._validate_subject_id(subject_identifier):
                subject_id = subject_identifier
            else:
                return False, f"Subject with ID {subject_identifier} not found."
        elif isinstance(subject_identifier, str):
            if subject_identifier.isdigit():
                 # Treat numeric string as ID, but validate it
                 potential_id = int(subject_identifier)
                 if self._validate_subject_id(potential_id):
                     subject_id = potential_id
                 else:
                     # Maybe they meant a subject named "123"? Try finding by name.
                     print(f"Warning: Subject ID '{subject_identifier}' not found. Trying as subject name.")
                     subject_id = self.get_subject_id(subject_identifier, create_if_not_exists=True)
            else:
                # Treat as subject name, get or create ID
                subject_id = self.get_subject_id(subject_identifier, create_if_not_exists=True)

            if subject_id is None:
                 return False, f"Could not find or create subject '{subject_identifier}'."
        else:
            return False, "Invalid subject identifier type. Use name (str) or ID (int)."


        if subject_id is None: # Should have been caught above, but double-check
             return False, "Failed to determine subject ID."

        try:
            with self._conn:
                self._execute(INSERT_ENTRY, (subject_id, entry_date, detail))
            return True, "Entry added successfully."
        except DatabaseError as e:
            return False, f"Error adding entry: {e}"
        except sqlite3.Error as e:
             return False, f"Unexpected error adding entry: {e}"

    def get_entries_for_subject(self, subject_name: str, newest_first: bool = False) -> Tuple[List[sqlite3.Row], str]:
        """Retrieve all entries for a specific subject."""
        sort_order = "DESC" if newest_first else "ASC"
        # Safely format the query string - ONLY because sort_order is strictly controlled
        query = SELECT_ENTRIES_BY_SUBJECT_NAME.format(sort_order)

        try:
            cursor = self._execute(query, (subject_name,))
            entries = cursor.fetchall() # Returns list of Row objects
            if not entries:
                return [], f"No entries found for '{subject_name}'."
            return entries, f"Found {len(entries)} entries for '{subject_name}'."
        except DatabaseError as e:
            return [], f"Error retrieving entries: {e}"

    def get_all_subjects(self) -> List[sqlite3.Row]:
        """Get a list of all subjects."""
        try:
            cursor = self._execute(SELECT_ALL_SUBJECTS)
            return cursor.fetchall() # Returns list of Row objects
        except DatabaseError as e:
            print(f"Error retrieving subjects: {e}")
            return []

    def close(self):
        """Close the database connection."""
        if self._conn:
            self._conn.close()
            print("Database connection closed.") # Optional feedback

# --- UI Functions ---

def display_entries(entries: List[sqlite3.Row], oldest_first: bool = True):
    """Format and display entries."""
    if not entries:
        # Message already printed by get_entries_for_subject in this design
        # print("No entries found.")
        return

    sort_description = "oldest to newest" if oldest_first else "newest to oldest"
    print(f"\n===== Entries for Subject (sorted {sort_description}) =====")
    print("=" * 50)
    for entry in entries:
        # Access columns by name thanks to row_factory
        print(f"[{entry['EntryDate']}]")
        print(f"{entry['Detail']}")
        print("-" * 50)

def select_subject(db: JournalDatabase, action_description: str = "") -> Tuple[bool, Optional[str], str]:
    """
    Utility function to handle subject selection by either ID or name.
    Returns (success_status, subject_name, message)
    """
    subjects = db.get_all_subjects()
    if not subjects:
        print("No subjects found. Please add a subject first.")
        return False, None, "No subjects available."
    print("\nAvailable subjects:")
    subject_map_id_to_name = {} # Dictionary to easily find name from ID
    subject_map_name_to_id = {} # Dictionary to check if name exists
    for subject in subjects:
        # Access columns by name
        subject_id = subject['SubjectID']
        subject_name = subject['SubjectName']
        print(f"ID: {subject_id} - {subject_name}")
        subject_map_id_to_name[subject_id] = subject_name
        subject_map_name_to_id[subject_name.lower()] = subject_id # Store lowercase for case-insensitive check if needed
    if action_description:
        print(f"\nSelect subject to {action_description}")
    # --- START: Added ID/Name Selection Logic ---
    while True: # Loop until valid selection method is chosen
        selection_method = input("\nSelect by (1) ID or (2) Name? [2]: ").strip() or '2' # Default to Name
        if selection_method == '1':
            # --- Select by ID ---
            id_input = input("Enter subject ID: ").strip()
            try:
                subject_id = int(id_input)
                # Find the subject name that matches this ID
                if subject_id in subject_map_id_to_name:
                    subject_name = subject_map_id_to_name[subject_id]
                    print(f"Selected subject: '{subject_name}' (ID: {subject_id})")
                    return True, subject_name, "Subject found by ID."
                else:
                    print(f"Error: No subject found with ID {subject_id}.")
                    # Optionally loop back or return failure
                    # return False, None, f"No subject found with ID {subject_id}."
                    # Let's loop back to ask again:
                    continue # Go back to asking ID or Name
            except ValueError:
                print("Invalid ID. Please enter a number.")
                continue # Go back to asking ID or Name
        elif selection_method == '2':
            # --- Select by Name ---
            subject_name = input("Enter subject name: ").strip()
            if not subject_name:
                print("Subject name cannot be empty.")
                continue # Go back to asking ID or Name
            # Optional: Check if the entered name exists (case-insensitive check)
            if subject_name.lower() not in subject_map_name_to_id:
                 print(f"Note: Subject '{subject_name}' doesn't exist yet (it might be created if needed by the action).")
                 # Proceed anyway, let the calling function handle creation if necessary
            # Return the entered name. The calling function (e.g., handle_add_entry)
            # will use db.insert_entry or db.get_entries_for_subject, which
            # can handle finding/creating the subject based on the name.
            return True, subject_name, "Subject selected by name."
        else:
            print("Invalid selection. Please choose 1 or 2.")
            # Loop continues
    # --- END: Added ID/Name Selection Logic ---

# --- Main Application Logic ---
def handle_add_subject(db: JournalDatabase):
    """Handles the 'Add Subject' menu option."""
    subject_name = input("Enter new subject name: ").strip()
    if not subject_name:
        print("Subject name cannot be empty.")
        return
    success, message = db.insert_subject(subject_name)
    print(message)

def handle_add_entry(db: JournalDatabase):
    """Handles the 'Add Entry' menu option."""
    success, subject_name, message = select_subject(db, "add an entry to")
    if not success:
        print(message) # Print message from select_subject
        return # Go back to main menu

    # Now prompt for entry details
    detail = input("Enter entry details: ").strip()
    if not detail:
        print("Entry details cannot be empty.")
        # Loop or return? Returning for simplicity.
        return

    # Add the entry - insert_entry will handle subject creation if needed
    success, message = db.insert_entry(subject_name, detail)
    print(message)


def handle_view_entries(db: JournalDatabase):
    """Handles the 'View Entries' menu option."""
    success, subject_name, message = select_subject(db, "view entries from")
    if not success or not subject_name: # Ensure subject_name is not None
        print(message)
        return

    # Ask for sorting preference
    sort_choice = input("Sort by (1) Oldest first or (2) Newest first? [1]: ").strip()
    newest_first = sort_choice == '2'

    entries, message = db.get_entries_for_subject(subject_name, newest_first)
    print(message) # Print "Found X entries..." or "No entries..."
    display_entries(entries, not newest_first) # Pass oldest_first flag

def handle_list_subjects(db: JournalDatabase):
    """Handles the 'List Subjects' menu option."""
    subjects = db.get_all_subjects()
    if not subjects:
        print("No subjects found.")
        return

    print("\nAll subjects:")
    for subject in subjects:
        print(f"ID: {subject['SubjectID']} - {subject['SubjectName']}") # Access by name

def main():
    """Main application loop."""
    db: Optional[JournalDatabase] = None # Initialize db to None
    try:
        db = JournalDatabase() # Initialize database

        while True:
            print("\n===== JOURNAL APPLICATION =====")
            print("1. Add a new subject")
            print("2. Add a new entry")
            print("3. View entries for a subject")
            print("4. List all subjects")
            print("5. Exit")
            print("6. Credits") # Renamed from "Creators and Credits"

            choice = input("\nEnter your choice (1-6): ").strip()

            if choice == '1':
                handle_add_subject(db)
            elif choice == '2':
                handle_add_entry(db)
            elif choice == '3':
                handle_view_entries(db)
            elif choice == '4':
                handle_list_subjects(db)
            elif choice == '5':
                print("Exiting program. Goodbye!")
                break
            elif choice == '6':
                print("\n--- Credits ---")
                print("Application developed using Python and SQLite.")
                print("Intended for personal journaling and information recall.")
                # Add your name or other credits here if you like
                print("-------------\n")
                # No continue needed, loop will naturally restart
            else:
                print("Invalid choice. Please enter a number between 1 and 6.")

    except DatabaseError as e:
        print(f"\nA critical database error occurred: {e}")
        print("Application cannot continue.")
        sys.exit(1) # Exit with an error code
    except KeyboardInterrupt:
         print("\nOperation cancelled by user. Exiting.")
         sys.exit(0)
    except Exception as e:
        # Catch unexpected errors
        print(f"\nAn unexpected error occurred: {e}")
        sys.exit(1)
    finally:
        if db: # Ensure db was successfully initialized before closing
            db.close()

if __name__ == "__main__":
    main()
