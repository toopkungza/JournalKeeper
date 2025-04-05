# database.py

"""Handles all database interactions for the Journal application."""

import sqlite3
from datetime import datetime
from typing import List, Tuple, Optional, Any

# Import constants from the constants file
import constants

class DatabaseError(Exception):
    """Custom exception for database related errors."""
    pass

class JournalDatabase:
    def __init__(self, db_file: str = constants.DB_FILE_NAME):
        """Initialize database connection."""
        self.db_file = db_file
        self._conn: Optional[sqlite3.Connection] = None
        try:
            self._conn = sqlite3.connect(self.db_file)
            self._conn.row_factory = sqlite3.Row # Access columns by name
            self._create_tables()
        except sqlite3.Error as e:
            raise DatabaseError(f"Fatal database initialization error: {e}") from e

    def _execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        """Executes SQL query with error handling."""
        if not self._conn:
             raise DatabaseError("Database connection is not established.")
        try:
            cursor = self._conn.cursor()
            cursor.execute(sql, params)
            return cursor
        except sqlite3.Error as e:
            print(f"Database execution error: {e} (SQL: {sql[:100]}...)")
            raise DatabaseError(f"Failed to execute query: {e}") from e

    def _create_tables(self):
        """Create database tables if they don't exist."""
        if not self._conn:
             raise DatabaseError("Database connection is not established.")
        try:
            with self._conn: # Use connection as context manager for transaction
                self._execute(constants.CREATE_SUBJECT_TABLE)
                self._execute(constants.CREATE_ENTRY_TABLE)
        except sqlite3.Error as e:
            raise DatabaseError(f"Table creation error: {e}") from e

    def insert_subject(self, subject_name: str) -> Tuple[bool, str]:
        """Insert a new subject, handling duplicates gracefully."""
        if not self._conn:
             return False, "Database connection is not established."
        try:
            with self._conn:
                self._execute(constants.INSERT_SUBJECT, (subject_name,))
            return True, f"Subject '{subject_name}' added successfully."
        except sqlite3.IntegrityError:
            return False, f"Subject '{subject_name}' already exists."
        except DatabaseError as e:
            return False, f"Error adding subject: {e}"
        except sqlite3.Error as e:
             return False, f"Unexpected error adding subject: {e}"

    def get_subject_id(self, subject_name: str, create_if_not_exists: bool = True) -> Optional[int]:
        """Get subject ID by name, optionally creating it if it doesn't exist."""
        try:
            cursor = self._execute(constants.SELECT_SUBJECT_ID_BY_NAME, (subject_name,))
            result = cursor.fetchone()

            if result:
                return result['SubjectID']
            elif create_if_not_exists:
                print(f"Subject '{subject_name}' not found, creating...")
                success, message = self.insert_subject(subject_name)
                if success:
                    cursor = self._execute(constants.SELECT_SUBJECT_ID_BY_NAME, (subject_name,))
                    new_result = cursor.fetchone()
                    return new_result['SubjectID'] if new_result else None
                else:
                    print(f"Failed to create subject: {message}")
                    return None
            else:
                return None
        except DatabaseError as e:
            print(f"Error retrieving/creating subject '{subject_name}': {e}")
            return None

    def _validate_subject_id(self, subject_id: int) -> bool:
        """Check if a subject ID exists in the database."""
        try:
            cursor = self._execute(constants.SELECT_SUBJECT_NAME_BY_ID, (subject_id,))
            return cursor.fetchone() is not None
        except DatabaseError:
            return False

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
                 potential_id = int(subject_identifier)
                 if self._validate_subject_id(potential_id):
                     subject_id = potential_id
                 else:
                     print(f"Warning: Subject ID '{subject_identifier}' not found. Trying as subject name.")
                     subject_id = self.get_subject_id(subject_identifier, create_if_not_exists=True)
            else:
                subject_id = self.get_subject_id(subject_identifier, create_if_not_exists=True)

            if subject_id is None:
                 return False, f"Could not find or create subject '{subject_identifier}'."
        else:
            return False, "Invalid subject identifier type. Use name (str) or ID (int)."

        if subject_id is None:
             return False, "Failed to determine subject ID."

        if not self._conn:
             return False, "Database connection is not established."

        try:
            with self._conn:
                self._execute(constants.INSERT_ENTRY, (subject_id, entry_date, detail))
            return True, "Entry added successfully."
        except DatabaseError as e:
            return False, f"Error adding entry: {e}"
        except sqlite3.Error as e:
             return False, f"Unexpected error adding entry: {e}"

    def get_entries_for_subject(self, subject_name: str, newest_first: bool = False) -> Tuple[List[sqlite3.Row], str]:
        """Retrieve all entries (including EntryID) for a specific subject."""
        sort_order = "DESC" if newest_first else "ASC"
        query = constants.SELECT_ENTRIES_BY_SUBJECT_NAME.format(sort_order)

        try:
            cursor = self._execute(query, (subject_name,))
            entries = cursor.fetchall()
            if not entries:
                return [], f"No entries found for '{subject_name}'."
            return entries, f"Found {len(entries)} entries for '{subject_name}'."
        except DatabaseError as e:
            return [], f"Error retrieving entries: {e}"

    def get_all_subjects(self) -> List[sqlite3.Row]:
        """Get a list of all subjects."""
        try:
            cursor = self._execute(constants.SELECT_ALL_SUBJECTS)
            return cursor.fetchall()
        except DatabaseError as e:
            print(f"Error retrieving subjects: {e}")
            return []

    def delete_entry(self, entry_id: int) -> Tuple[bool, str]:
        """Deletes a specific entry by its ID."""
        if not self._conn:
             return False, "Database connection is not established."
        try:
            with self._conn:
                cursor = self._execute(constants.DELETE_ENTRY_BY_ID, (entry_id,))
                if cursor.rowcount == 0:
                    return False, f"Error: Entry with ID {entry_id} not found."
                else:
                    return True, f"Entry with ID {entry_id} deleted successfully."
        except DatabaseError as e:
            return False, f"Error deleting entry ID {entry_id}: {e}"
        except sqlite3.Error as e:
             return False, f"Unexpected error deleting entry ID {entry_id}: {e}"

    def close(self):
        """Close the database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None # Mark as closed
            print("Database connection closed.")
# EOF #
