import sqlite3
from datetime import datetime

class JournalDatabase:
    def __init__(self, db_file='Journal.db'):
        """Initialize database connection and ensure tables exist."""
        self.db_file = db_file
        self.conn = None
        self.cursor = None
        self.connect()
        self.create_tables()
    
    def connect(self):
        """Establish database connection."""
        try:
            self.conn = sqlite3.connect(self.db_file)
            self.cursor = self.conn.cursor()
        except sqlite3.Error as e:
            print(f"Database connection error: {e}")
            exit(1)
    
    def create_tables(self):
        """Create database tables if they don't exist."""
        try:
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS Subject (
                SubjectID INTEGER PRIMARY KEY AUTOINCREMENT,
                SubjectName TEXT UNIQUE NOT NULL
            )
            ''')
            
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS Entry (
                EntryID INTEGER PRIMARY KEY AUTOINCREMENT,
                SubjectID INTEGER NOT NULL,
                EntryDate TEXT NOT NULL,
                Detail TEXT NOT NULL,
                FOREIGN KEY (SubjectID) REFERENCES Subject(SubjectID)
            )
            ''')
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Table creation error: {e}")
            self.close()
            exit(1)
    
    def insert_subject(self, subject_name):
        """Insert a new subject, handling duplicates gracefully."""
        try:
            self.cursor.execute('''
            INSERT INTO Subject (SubjectName)
            VALUES (?)
            ''', (subject_name,))
            self.conn.commit()
            return True, f"Subject '{subject_name}' added successfully"
        except sqlite3.IntegrityError:
            return False, f"Subject '{subject_name}' already exists"
        except sqlite3.Error as e:
            return False, f"Error adding subject: {e}"
    
    def get_subject_id(self, subject_name):
        """Get subject ID by name, creating it if it doesn't exist."""
        try:
            self.cursor.execute('''
            SELECT SubjectID FROM Subject WHERE SubjectName = ?
            ''', (subject_name,))
            result = self.cursor.fetchone()
            
            if result:
                return result[0]
            else:
                # Create the subject if it doesn't exist
                success, _ = self.insert_subject(subject_name)
                if success:
                    return self.get_subject_id(subject_name)
                return None
        except sqlite3.Error as e:
            print(f"Error retrieving subject: {e}")
            return None
    
    def insert_entry(self, subject_name, detail, entry_date=None):
        """Insert a new entry, allowing subject to be specified by name."""
        if entry_date is None:
            entry_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
        subject_id = self.get_subject_id(subject_name)
        if not subject_id:
            return False, "Failed to identify or create subject"
        
        try:
            self.cursor.execute('''
            INSERT INTO Entry (SubjectID, EntryDate, Detail)
            VALUES (?, ?, ?)
            ''', (subject_id, entry_date, detail))
            self.conn.commit()
            return True, f"Entry added to '{subject_name}'"
        except sqlite3.Error as e:
            return False, f"Error adding entry: {e}"
    
    def get_entries_for_subject(self, subject_name):
        """Retrieve all entries for a specific subject."""
        try:
            self.cursor.execute('''
            SELECT e.EntryDate, e.Detail
            FROM Entry e
            JOIN Subject s ON e.SubjectID = s.SubjectID
            WHERE s.SubjectName = ?
            ORDER BY e.EntryDate DESC
            ''', (subject_name,))
            
            entries = self.cursor.fetchall()
            if not entries:
                return [], f"No entries found for '{subject_name}'"
            return entries, f"Found {len(entries)} entries for '{subject_name}'"
        except sqlite3.Error as e:
            return [], f"Error retrieving entries: {e}"
    
    def get_all_subjects(self):
        """Get a list of all subjects."""
        try:
            self.cursor.execute("SELECT SubjectID, SubjectName FROM Subject ORDER BY SubjectName")
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error retrieving subjects: {e}")
            return []
    
    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()

def display_entries(entries):
    """Format and display entries."""
    if not entries:
        print("No entries found.")
        return
        
    print("\n" + "="*50)
    for date, detail in entries:
        print(f"[{date}]")
        print(f"{detail}")
        print("-"*50)

def main():
    """Main application loop."""
    db = JournalDatabase()
    
    try:
        while True:
            print("\n===== JOURNAL APPLICATION =====")
            print("1. Add a new subject")
            print("2. Add a new entry")
            print("3. View entries for a subject")
            print("4. List all subjects")
            print("5. Exit")
            print("6. Creators and Credits")
            
            try:
                choice = input("\nEnter your choice (1-5): ")
                
                if choice == '1':
                    subject_name = input("Enter subject name: ").strip()
                    if not subject_name:
                        print("Subject name cannot be empty.")
                        continue
                    success, message = db.insert_subject(subject_name)
                    print(message)
                    
                elif choice == '2':
                    # Show available subjects
                    subjects = db.get_all_subjects()
                    if not subjects:
                        print("No subjects found. Please add a subject first.")
                        continue
                        
                    print("\nAvailable subjects:")
                    for id, name in subjects:
                        print(f"- {name}")
                        
                    subject_name = input("\nEnter subject name (or create new): ").strip()
                    if not subject_name:
                        print("Subject name cannot be empty.")
                        continue
                        
                    detail = input("Enter entry details: ").strip()
                    if not detail:
                        print("Entry details cannot be empty.")
                        continue
                        
                    success, message = db.insert_entry(subject_name, detail)
                    print(message)
                    
                elif choice == '3':
                    # Show available subjects
                    subjects = db.get_all_subjects()
                    if not subjects:
                        print("No subjects found.")
                        continue
                        
                    print("\nAvailable subjects:")
                    for id, name in subjects:
                        print(f"- {name}")
                        
                    subject_name = input("\nEnter subject name to view: ").strip()
                    entries, message = db.get_entries_for_subject(subject_name)
                    print(message)
                    display_entries(entries)
                    
                elif choice == '4':
                    subjects = db.get_all_subjects()
                    if not subjects:
                        print("No subjects found.")
                        continue
                        
                    print("\nAll subjects:")
                    for id, name in subjects:
                        print(f"ID: {id} - {name}")
                    
                elif choice == '5':
                    print("Exiting program. Goodbye!")
                    break

                elif choice == '6':
                    print("Thanks for visiting this page. \n")
                    print("This journal application is created by Sukrit Riyaphan with the help of DeepSeek (functions) and Claude (DB class). \n")
                    print("This is intended for history recalls and information access only. \n")
                    break
                    
                else:
                    print("Invalid choice. Please enter a number between 1 and 5.")
                    
            except ValueError as e:
                print(f"Invalid input: {e}")
                
    finally:
        db.close()

if __name__ == "__main__":
    main()