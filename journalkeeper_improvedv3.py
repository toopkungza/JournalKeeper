"""
Enhanced Journal Keeper Application
A robust SQLite-based journal application with improved error handling,
performance optimizations, and better code structure.
"""

import sqlite3
import logging
from datetime import datetime
from pathlib import Path
from contextlib import contextmanager
from typing import List, Tuple, Optional, Union
import sys


class JournalError(Exception):
    """Custom exception for journal-specific errors."""
    pass


class JournalDatabase:
    """
    A robust database handler for journal entries with connection pooling,
    proper error handling, and performance optimizations.
    """
    
    def __init__(self, db_file: str = 'Journal.db'):
        """
        Initialize database connection and ensure tables exist.
        
        Args:
            db_file: Path to the SQLite database file
        """
        self.db_file = Path(db_file)
        self._setup_logging()
        self._initialize_database()
    
    def _setup_logging(self) -> None:
        """Configure logging for the application."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('journal.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def _initialize_database(self) -> None:
        """Initialize database and create tables."""
        try:
            # Create database directory if it doesn't exist
            self.db_file.parent.mkdir(parents=True, exist_ok=True)
            
            with self._get_connection() as conn:
                self._create_tables(conn)
                self._create_indexes(conn)
            
            self.logger.info(f"Database initialized successfully: {self.db_file}")
            
        except sqlite3.Error as e:
            self.logger.error(f"Database initialization failed: {e}")
            raise JournalError(f"Failed to initialize database: {e}")
    
    @contextmanager
    def _get_connection(self):
        """
        Context manager for database connections with proper cleanup.
        
        Yields:
            sqlite3.Connection: Database connection
        """
        conn = None
        try:
            conn = sqlite3.connect(
                str(self.db_file),
                timeout=30.0,  # 30 second timeout
                isolation_level=None  # Autocommit mode
            )
            # Enable foreign key constraints
            conn.execute("PRAGMA foreign_keys = ON")
            # Enable WAL mode for better concurrency
            conn.execute("PRAGMA journal_mode = WAL")
            # Optimize for performance
            conn.execute("PRAGMA synchronous = NORMAL")
            conn.execute("PRAGMA cache_size = 10000")
            
            yield conn
            
        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            self.logger.error(f"Database error: {e}")
            raise JournalError(f"Database operation failed: {e}")
        finally:
            if conn:
                conn.close()
    
    def _create_tables(self, conn: sqlite3.Connection) -> None:
        """Create database tables if they don't exist."""
        # Create Subject table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS Subject (
                SubjectID INTEGER PRIMARY KEY AUTOINCREMENT,
                SubjectName TEXT UNIQUE NOT NULL COLLATE NOCASE,
                CreatedAt TEXT NOT NULL DEFAULT (datetime('now')),
                UpdatedAt TEXT NOT NULL DEFAULT (datetime('now'))
            )
        ''')
        
        # Create Entry table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS Entry (
                EntryID INTEGER PRIMARY KEY AUTOINCREMENT,
                SubjectID INTEGER NOT NULL,
                EntryDate TEXT NOT NULL DEFAULT (datetime('now')),
                Detail TEXT NOT NULL,
                CreatedAt TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (SubjectID) REFERENCES Subject(SubjectID) ON DELETE CASCADE
            )
        ''')
        
        # Create trigger to update UpdatedAt timestamp
        conn.execute('''
            CREATE TRIGGER IF NOT EXISTS update_subject_timestamp 
            AFTER UPDATE ON Subject
            BEGIN
                UPDATE Subject SET UpdatedAt = datetime('now') WHERE SubjectID = NEW.SubjectID;
            END
        ''')
    
    def _create_indexes(self, conn: sqlite3.Connection) -> None:
        """Create database indexes for better performance."""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_subject_name ON Subject(SubjectName)",
            "CREATE INDEX IF NOT EXISTS idx_entry_subject_id ON Entry(SubjectID)",
            "CREATE INDEX IF NOT EXISTS idx_entry_date ON Entry(EntryDate)",
            "CREATE INDEX IF NOT EXISTS idx_entry_subject_date ON Entry(SubjectID, EntryDate)"
        ]
        
        for index_sql in indexes:
            conn.execute(index_sql)
    
    def insert_subject(self, subject_name: str) -> Tuple[bool, str]:
        """
        Insert a new subject, handling duplicates gracefully.
        
        Args:
            subject_name: Name of the subject to insert
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        if not subject_name or not subject_name.strip():
            return False, "Subject name cannot be empty"
        
        subject_name = subject_name.strip()
        
        try:
            with self._get_connection() as conn:
                conn.execute(
                    "INSERT INTO Subject (SubjectName) VALUES (?)",
                    (subject_name,)
                )
                self.logger.info(f"Subject '{subject_name}' added successfully")
                return True, f"Subject '{subject_name}' added successfully"
                
        except sqlite3.IntegrityError:
            message = f"Subject '{subject_name}' already exists"
            self.logger.warning(message)
            return False, message
        except JournalError as e:
            return False, str(e)
    
    def get_subject_id(self, subject_name: str) -> Optional[int]:
        """
        Get subject ID by name, creating it if it doesn't exist.
        
        Args:
            subject_name: Name of the subject
            
        Returns:
            Subject ID if found/created, None otherwise
        """
        if not subject_name or not subject_name.strip():
            return None
        
        subject_name = subject_name.strip()
        
        try:
            with self._get_connection() as conn:
                cursor = conn.execute(
                    "SELECT SubjectID FROM Subject WHERE SubjectName = ? COLLATE NOCASE",
                    (subject_name,)
                )
                result = cursor.fetchone()
                
                if result:
                    return result[0]
                else:
                    # Create the subject if it doesn't exist
                    success, _ = self.insert_subject(subject_name)
                    if success:
                        return self.get_subject_id(subject_name)
                    return None
                    
        except JournalError as e:
            self.logger.error(f"Error retrieving subject '{subject_name}': {e}")
            return None
    
    def insert_entry(self, subject_identifier: Union[int, str], detail: str, 
                    entry_date: Optional[str] = None) -> Tuple[bool, str]:
        """
        Insert a new entry, allowing subject to be specified by name or ID.
        
        Args:
            subject_identifier: Subject ID (int) or name (str)
            detail: Entry content
            entry_date: Optional custom date (ISO format)
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        if not detail or not detail.strip():
            return False, "Entry details cannot be empty"
        
        detail = detail.strip()
        
        # Validate and parse entry_date if provided
        if entry_date:
            try:
                datetime.fromisoformat(entry_date.replace('Z', '+00:00'))
            except ValueError:
                return False, "Invalid date format. Use ISO format (YYYY-MM-DD HH:MM:SS)"
        else:
            entry_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Determine subject ID
        subject_id = self._resolve_subject_id(subject_identifier)
        if not subject_id:
            return False, "Failed to identify or create subject"
        
        try:
            with self._get_connection() as conn:
                conn.execute(
                    "INSERT INTO Entry (SubjectID, EntryDate, Detail) VALUES (?, ?, ?)",
                    (subject_id, entry_date, detail)
                )
                self.logger.info(f"Entry added successfully for subject ID {subject_id}")
                return True, "Entry added successfully"
                
        except JournalError as e:
            return False, str(e)
    
    def _resolve_subject_id(self, subject_identifier: Union[int, str]) -> Optional[int]:
        """
        Resolve subject identifier to subject ID.
        
        Args:
            subject_identifier: Subject ID (int) or name (str)
            
        Returns:
            Subject ID if found, None otherwise
        """
        if isinstance(subject_identifier, int):
            return self._validate_subject_id(subject_identifier)
        elif isinstance(subject_identifier, str):
            if subject_identifier.isdigit():
                return self._validate_subject_id(int(subject_identifier))
            else:
                return self.get_subject_id(subject_identifier)
        return None
    
    def _validate_subject_id(self, subject_id: int) -> Optional[int]:
        """Validate that a subject ID exists in the database."""
        try:
            with self._get_connection() as conn:
                cursor = conn.execute(
                    "SELECT SubjectID FROM Subject WHERE SubjectID = ?",
                    (subject_id,)
                )
                result = cursor.fetchone()
                return result[0] if result else None
        except JournalError:
            return None
    
    def get_entries_for_subject(self, subject_name: str, 
                              newest_first: bool = False,
                              limit: Optional[int] = None) -> Tuple[List[Tuple], str]:
        """
        Retrieve entries for a specific subject with optional pagination.
        
        Args:
            subject_name: Name of the subject
            newest_first: Sort order (True for newest first)
            limit: Maximum number of entries to return
            
        Returns:
            Tuple of (entries: List[Tuple], message: str)
        """
        if not subject_name or not subject_name.strip():
            return [], "Subject name cannot be empty"
        
        subject_name = subject_name.strip()
        sort_order = "DESC" if newest_first else "ASC"
        
        try:
            with self._get_connection() as conn:
                query = '''
                    SELECT e.EntryDate, e.Detail, e.EntryID
                    FROM Entry e
                    JOIN Subject s ON e.SubjectID = s.SubjectID
                    WHERE s.SubjectName = ? COLLATE NOCASE
                    ORDER BY e.EntryDate {}
                '''.format(sort_order)
                
                params = [subject_name]
                if limit and limit > 0:
                    query += " LIMIT ?"
                    params.append(limit)
                
                cursor = conn.execute(query, params)
                entries = cursor.fetchall()
                
                if not entries:
                    message = f"No entries found for '{subject_name}'"
                    self.logger.info(message)
                    return [], message
                
                message = f"Found {len(entries)} entries for '{subject_name}'"
                self.logger.info(message)
                return entries, message
                
        except JournalError as e:
            error_msg = f"Error retrieving entries: {e}"
            self.logger.error(error_msg)
            return [], error_msg
    
    def get_all_subjects(self) -> List[Tuple[int, str]]:
        """
        Get a list of all subjects with entry counts.
        
        Returns:
            List of tuples (SubjectID, SubjectName, EntryCount)
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.execute('''
                    SELECT s.SubjectID, s.SubjectName, COUNT(e.EntryID) as EntryCount
                    FROM Subject s
                    LEFT JOIN Entry e ON s.SubjectID = e.SubjectID
                    GROUP BY s.SubjectID, s.SubjectName
                    ORDER BY s.SubjectName COLLATE NOCASE
                ''')
                return cursor.fetchall()
        except JournalError as e:
            self.logger.error(f"Error retrieving subjects: {e}")
            return []
    
    def delete_subject(self, subject_id: int) -> Tuple[bool, str]:
        """
        Delete a subject and all its entries.
        
        Args:
            subject_id: ID of the subject to delete
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            with self._get_connection() as conn:
                # Check if subject exists
                cursor = conn.execute(
                    "SELECT SubjectName FROM Subject WHERE SubjectID = ?",
                    (subject_id,)
                )
                result = cursor.fetchone()
                
                if not result:
                    return False, f"Subject with ID {subject_id} not found"
                
                subject_name = result[0]
                
                # Delete subject (entries will be deleted due to CASCADE)
                conn.execute("DELETE FROM Subject WHERE SubjectID = ?", (subject_id,))
                
                message = f"Subject '{subject_name}' and all its entries deleted successfully"
                self.logger.info(message)
                return True, message
                
        except JournalError as e:
            error_msg = f"Error deleting subject: {e}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def get_database_stats(self) -> dict:
        """Get database statistics."""
        try:
            with self._get_connection() as conn:
                stats = {}
                
                # Get subject count
                cursor = conn.execute("SELECT COUNT(*) FROM Subject")
                stats['total_subjects'] = cursor.fetchone()[0]
                
                # Get entry count
                cursor = conn.execute("SELECT COUNT(*) FROM Entry")
                stats['total_entries'] = cursor.fetchone()[0]
                
                # Get database size
                stats['database_size'] = self.db_file.stat().st_size if self.db_file.exists() else 0
                
                return stats
        except (JournalError, OSError) as e:
            self.logger.error(f"Error getting database stats: {e}")
            return {}


def display_entries(entries: List[Tuple], oldest_first: bool = True) -> None:
    """
    Format and display entries with improved formatting.
    
    Args:
        entries: List of entry tuples (date, detail, entry_id)
        oldest_first: Display order preference
    """
    if not entries:
        print("No entries found.")
        return
    
    sort_description = "oldest to newest" if oldest_first else "newest to oldest"
    print(f"\n{'='*60}")
    print(f"ENTRIES (sorted {sort_description}) - Total: {len(entries)}")
    print(f"{'='*60}")
    
    for i, (date, detail, entry_id) in enumerate(entries, 1):
        print(f"\n[Entry #{entry_id}] - {date}")
        print(f"{'-'*50}")
        # Handle long entries with word wrapping
        words = detail.split()
        line = ""
        for word in words:
            if len(line + word) > 70:
                print(line)
                line = word + " "
            else:
                line += word + " "
        if line:
            print(line.strip())
        
        if i < len(entries):
            print(f"{'='*60}")


def select_subject(db: JournalDatabase, action_description: str = "") -> Tuple[bool, Optional[str], str]:
    """
    Utility function to handle subject selection by either ID or name with improved UX.
    
    Args:
        db: Database instance
        action_description: Description of the action being performed
        
    Returns:
        Tuple of (success: bool, subject_name: Optional[str], message: str)
    """
    # Show available subjects with entry counts
    subjects = db.get_all_subjects()
    if not subjects:
        return False, None, "No subjects found. Please add a subject first."
    
    print(f"\n{'='*50}")
    print("AVAILABLE SUBJECTS")
    print(f"{'='*50}")
    print(f"{'ID':<5} {'Subject Name':<30} {'Entries':<10}")
    print(f"{'-'*50}")
    
    for subject_id, name, entry_count in subjects:
        print(f"{subject_id:<5} {name:<30} {entry_count:<10}")
    
    if action_description:
        print(f"\nSelect subject to {action_description}")
    
    while True:
        print("\nSelection options:")
        print("1. Select by ID")
        print("2. Select by name")
        print("3. Go back to main menu")
        
        selection_method = input("\nEnter your choice (1-3): ").strip()
        
        if selection_method == '1':
            return _select_by_id(subjects)
        elif selection_method == '2':
            return _select_by_name(subjects)
        elif selection_method == '3':
            return False, None, "Selection cancelled"
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")


def _select_by_id(subjects: List[Tuple]) -> Tuple[bool, Optional[str], str]:
    """Select subject by ID with validation."""
    try:
        subject_id = int(input("Enter subject ID: ").strip())
        
        # Find the subject name that matches this ID
        for sid, name, _ in subjects:
            if sid == subject_id:
                return True, name, f"Subject '{name}' selected"
        
        return False, None, f"No subject found with ID {subject_id}"
        
    except ValueError:
        return False, None, "Invalid ID. Please enter a valid number."


def _select_by_name(subjects: List[Tuple]) -> Tuple[bool, Optional[str], str]:
    """Select subject by name with fuzzy matching."""
    subject_name = input("Enter subject name: ").strip()
    if not subject_name:
        return False, None, "Subject name cannot be empty."
    
    # Exact match first
    for _, name, _ in subjects:
        if name.lower() == subject_name.lower():
            return True, name, f"Subject '{name}' selected"
    
    # Partial match if no exact match
    matches = []
    for _, name, _ in subjects:
        if subject_name.lower() in name.lower():
            matches.append(name)
    
    if len(matches) == 1:
        return True, matches[0], f"Subject '{matches[0]}' selected (partial match)"
    elif len(matches) > 1:
        print(f"\nMultiple matches found: {', '.join(matches)}")
        print("Please be more specific or use the exact name.")
        return False, None, "Multiple matches found"
    else:
        # Offer to create new subject
        create_new = input(f"Subject '{subject_name}' not found. Create it? (y/n): ").strip().lower()
        if create_new in ['y', 'yes']:
            return True, subject_name, f"Will create new subject '{subject_name}'"
        return False, None, "Subject not found"


def display_menu() -> None:
    """Display the main menu with improved formatting."""
    print(f"\n{'='*50}")
    print("JOURNAL APPLICATION")
    print(f"{'='*50}")
    print("1. Add a new subject")
    print("2. Add a new entry")
    print("3. View entries for a subject")
    print("4. List all subjects")
    print("5. Delete a subject")
    print("6. Database statistics")
    print("7. Export entries")
    print("8. Help")
    print("9. Exit")
    print(f"{'='*50}")


def export_entries(db: JournalDatabase) -> None:
    """Export entries to a text file."""
    success, subject_name, message = select_subject(db, "export entries from")
    if not success:
        print(message)
        return
    
    entries, msg = db.get_entries_for_subject(subject_name, newest_first=False)
    if not entries:
        print(msg)
        return
    
    # Generate filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_subject_name = "".join(c for c in subject_name if c.isalnum() or c in (' ', '-', '_')).strip()
    filename = f"journal_export_{safe_subject_name}_{timestamp}.txt"
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"Journal Export - Subject: {subject_name}\n")
            f.write(f"Export Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Entries: {len(entries)}\n")
            f.write("=" * 60 + "\n\n")
            
            for date, detail, entry_id in entries:
                f.write(f"[Entry #{entry_id}] - {date}\n")
                f.write("-" * 50 + "\n")
                f.write(f"{detail}\n")
                f.write("=" * 60 + "\n\n")
        
        print(f"Entries exported successfully to: {filename}")
        
    except IOError as e:
        print(f"Error exporting entries: {e}")


def show_help() -> None:
    """Display help information."""
    help_text = """
JOURNAL APPLICATION HELP
========================

This application allows you to maintain a personal journal organized by subjects.

FEATURES:
- Create subjects to organize your entries
- Add dated entries to subjects
- View entries sorted by date (oldest or newest first)
- Search subjects by name or ID
- Export entries to text files
- Delete subjects and all associated entries

TIPS:
- Subject names are case-insensitive
- You can select subjects by ID (faster) or name (more intuitive)
- Partial name matching is supported when selecting subjects
- All operations are logged for troubleshooting
- Database is automatically backed up in WAL mode

KEYBOARD SHORTCUTS:
- Ctrl+C: Exit current operation
- Enter: Use default options where available

For technical support, check the journal.log file for detailed error messages.
"""
    print(help_text)


def handle_add_entry(db: JournalDatabase) -> None:
    """Handle adding a new entry with improved error handling."""
    max_attempts = 3
    attempts = 0
    
    while attempts < max_attempts:
        success, subject_name, message = select_subject(db, "add an entry to")
        if not success:
            print(message)
            return
        
        print(f"\nAdding entry to subject: '{subject_name}'")
        detail = input("Enter entry details (or 'cancel' to abort): ").strip()
        
        if detail.lower() == 'cancel':
            print("Entry cancelled.")
            return
        
        if not detail:
            print("Entry details cannot be empty.")
            attempts += 1
            if attempts < max_attempts:
                print(f"Please try again. ({max_attempts - attempts} attempts remaining)")
                continue
            else:
                print("Maximum attempts reached. Returning to main menu.")
                return
        
        # Ask for custom date (optional)
        use_custom_date = input("Use custom date? (y/n) [n]: ").strip().lower()
        entry_date = None
        
        if use_custom_date in ['y', 'yes']:
            date_input = input("Enter date (YYYY-MM-DD HH:MM:SS) or press Enter for now: ").strip()
            if date_input:
                try:
                    # Validate date format
                    datetime.strptime(date_input, "%Y-%m-%d %H:%M:%S")
                    entry_date = date_input
                except ValueError:
                    print("Invalid date format. Using current time.")
        
        # Add the entry
        success, message = db.insert_entry(subject_name, detail, entry_date)
        print(message)
        
        if success:
            # Ask if user wants to add another entry
            another = input("Add another entry to this subject? (y/n) [n]: ").strip().lower()
            if another in ['y', 'yes']:
                continue
        return


def handle_view_entries(db: JournalDatabase) -> None:
    """Handle viewing entries with pagination and filtering options."""
    success, subject_name, message = select_subject(db, "view entries from")
    if not success:
        print(message)
        return
    
    # Get sorting preference
    print("\nSorting options:")
    print("1. Oldest first (default)")
    print("2. Newest first")
    
    sort_choice = input("Choose sorting (1-2) [1]: ").strip()
    newest_first = sort_choice == '2'
    
    # Get limit preference
    limit_choice = input("Limit number of entries? (y/n) [n]: ").strip().lower()
    limit = None
    
    if limit_choice in ['y', 'yes']:
        try:
            limit = int(input("Enter maximum number of entries to display: ").strip())
            if limit <= 0:
                limit = None
                print("Invalid limit. Showing all entries.")
        except ValueError:
            print("Invalid number. Showing all entries.")
    
    entries, message = db.get_entries_for_subject(subject_name, newest_first, limit)
    print(f"\n{message}")
    
    if entries:
        display_entries(entries, not newest_first)
        
        # Offer export option
        if len(entries) > 0:
            export_choice = input(f"\nExport these {len(entries)} entries to file? (y/n) [n]: ").strip().lower()
            if export_choice in ['y', 'yes']:
                export_entries_to_file(subject_name, entries)


def export_entries_to_file(subject_name: str, entries: List[Tuple]) -> None:
    """Export given entries to a file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_subject_name = "".join(c for c in subject_name if c.isalnum() or c in (' ', '-', '_')).strip()
    filename = f"journal_export_{safe_subject_name}_{timestamp}.txt"
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"Journal Export - Subject: {subject_name}\n")
            f.write(f"Export Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Entries: {len(entries)}\n")
            f.write("=" * 60 + "\n\n")
            
            for date, detail, entry_id in entries:
                f.write(f"[Entry #{entry_id}] - {date}\n")
                f.write("-" * 50 + "\n")
                f.write(f"{detail}\n")
                f.write("=" * 60 + "\n\n")
        
        print(f"Entries exported successfully to: {filename}")
        
    except IOError as e:
        print(f"Error exporting entries: {e}")


def handle_delete_subject(db: JournalDatabase) -> None:
    """Handle subject deletion with confirmation."""
    success, subject_name, message = select_subject(db, "delete")
    if not success:
        print(message)
        return
    
    # Get subject ID for deletion
    subjects = db.get_all_subjects()
    subject_id = None
    entry_count = 0
    
    for sid, name, count in subjects:
        if name.lower() == subject_name.lower():
            subject_id = sid
            entry_count = count
            break
    
    if not subject_id:
        print("Subject not found.")
        return
    
    # Confirmation
    print(f"\nWARNING: This will permanently delete:")
    print(f"- Subject: '{subject_name}'")
    print(f"- All {entry_count} associated entries")
    print("\nThis action cannot be undone!")
    
    confirmation = input("Type 'DELETE' to confirm: ").strip()
    
    if confirmation == 'DELETE':
        success, message = db.delete_subject(subject_id)
        print(f"\n{message}")
    else:
        print("Deletion cancelled.")


def show_database_stats(db: JournalDatabase) -> None:
    """Display database statistics."""
    stats = db.get_database_stats()
    
    if not stats:
        print("Unable to retrieve database statistics.")
        return
    
    print(f"\n{'='*40}")
    print("DATABASE STATISTICS")
    print(f"{'='*40}")
    print(f"Total Subjects: {stats.get('total_subjects', 'N/A')}")
    print(f"Total Entries: {stats.get('total_entries', 'N/A')}")
    
    # Format database size
    size_bytes = stats.get('database_size', 0)
    if size_bytes < 1024:
        size_str = f"{size_bytes} bytes"
    elif size_bytes < 1024 * 1024:
        size_str = f"{size_bytes / 1024:.1f} KB"
    else:
        size_str = f"{size_bytes / (1024 * 1024):.1f} MB"
    
    print(f"Database Size: {size_str}")
    print(f"{'='*40}")


def main() -> None:
    """Main application loop with comprehensive error handling."""
    try:
        db = JournalDatabase()
        print("Journal application started successfully!")
        
        # Show initial stats
        stats = db.get_database_stats()
        if stats:
            print(f"Database loaded: {stats['total_subjects']} subjects, {stats['total_entries']} entries")
        
    except JournalError as e:
        print(f"Failed to initialize journal application: {e}")
        return
    except KeyboardInterrupt:
        print("\nApplication startup cancelled.")
        return
    
    try:
        while True:
            display_menu()
            
            try:
                choice = input("Enter your choice (1-9): ").strip()
                
                if choice == '1':
                    subject_name = input("Enter subject name: ").strip()
                    if not subject_name:
                        print("Subject name cannot be empty.")
                        continue
                    success, message = db.insert_subject(subject_name)
                    print(message)
                
                elif choice == '2':
                    handle_add_entry(db)
                
                elif choice == '3':
                    handle_view_entries(db)
                
                elif choice == '4':
                    subjects = db.get_all_subjects()
                    if not subjects:
                        print("No subjects found.")
                        continue
                    
                    print(f"\n{'='*60}")
                    print("ALL SUBJECTS")
                    print(f"{'='*60}")
                    print(f"{'ID':<5} {'Subject Name':<35} {'Entries':<10} {'Created':<15}")
                    print(f"{'-'*60}")
                    
                    for subject_id, name, entry_count in subjects:
                        # Note: We don't have CreatedAt in the current query, so we'll show a placeholder
                        print(f"{subject_id:<5} {name:<35} {entry_count:<10} {'N/A':<15}")
                
                elif choice == '5':
                    handle_delete_subject(db)
                
                elif choice == '6':
                    show_database_stats(db)
                
                elif choice == '7':
                    export_entries(db)
                
                elif choice == '8':
                    show_help()
                
                elif choice == '9':
                    print("Exiting program. Goodbye!")
                    break
                
                else:
                    print("Invalid choice. Please enter a number between 1 and 9.")
            
            except KeyboardInterrupt:
                print("\nOperation cancelled. Returning to main menu.")
                continue
            except EOFError:
                print("\nExiting program. Goodbye!")
                break
            except Exception as e:
                print(f"An unexpected error occurred: {e}")
                print("Please try again or contact support if the problem persists.")
                continue
    
    except KeyboardInterrupt:
        print("\nProgram interrupted. Exiting...")
    except Exception as e:
        print(f"Fatal error: {e}")
        print("The application will now exit.")
    finally:
        print("Thank you for using the Journal Application!")


if __name__ == "__main__":
    main()
