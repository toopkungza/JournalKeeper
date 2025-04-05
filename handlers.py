# handlers.py

"""Contains handler functions for the main application menu choices."""

from database import JournalDatabase # Import the actual class
from ui import select_subject, display_entries, clear_console # Import UI functions

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
        print(message)
        return
    detail = input("Enter entry details: ").strip()
    if not detail:
        print("Entry details cannot be empty.")
        return
    # insert_entry handles subject creation if needed based on name
    success, message = db.insert_entry(subject_name, detail)
    print(message)
    
def handle_view_entries(db: JournalDatabase):
    """Handles the 'View Entries' menu option and optional deletion."""
    success, subject_name, message = select_subject(db, "view entries from")
    if not success or not subject_name:
        print(message)
        return
    sort_choice = input("Sort by (1) Oldest first or (2) Newest first? [1]: ").strip()
    newest_first = sort_choice == '2'
    entries, message = db.get_entries_for_subject(subject_name, newest_first)
    clear_console()
    print(message)
    display_entries(entries, not newest_first)
    if entries:
        print("-" * 50)
        while True:
            id_to_delete_str = input("Enter the ID of the entry to delete (or press Enter to go back if you don't want to delete): ").strip()
            if not id_to_delete_str:
                break
            try:
                entry_id_to_delete = int(id_to_delete_str)
                if any(entry['EntryID'] == entry_id_to_delete for entry in entries):
                    confirm = input(f"Are you sure you want to delete entry ID {entry_id_to_delete}? (y/N): ").strip().lower()
                    if confirm == 'y':
                        delete_success, delete_message = db.delete_entry(entry_id_to_delete)
                        print(delete_message)
                        break
                    else:
                        print("Deletion cancelled.")
                        break
                else:
                    print(f"Error: ID {entry_id_to_delete} is not in the list shown above.")
            except ValueError:
                print("Invalid input. Please enter a number (ID) or press Enter.")
                
def handle_list_subjects(db: JournalDatabase):
    """Handles the 'List Subjects' menu option."""
    subjects = db.get_all_subjects()
    if not subjects:
        print("No subjects found.")
        return
    print("\nAll subjects:")
    for subject in subjects:
        print(f"ID: {subject['SubjectID']} - {subject['SubjectName']}")
        
def handle_credits():
    """Displays the credits screen."""
    clear_console() # Optional: clear screen before showing credits
    print("\n--- Credits ---")
    print("Application developed using Python and SQLite.")
    print("Intended for personal journaling and information recall.")
    # Add your name or other credits here if you like
    print("-------------\n")
    input("Press Enter to return to the main menu...") # Pause screen
    
# EOF #
