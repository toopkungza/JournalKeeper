# main.py

"""Main entry point for the Journal Application."""

import sys
from typing import Optional

# Import necessary components from other modules
from database import JournalDatabase, DatabaseError
from handlers import (
    handle_add_subject,
    handle_add_entry,
    handle_view_entries,
    handle_list_subjects,
    handle_credits
)
from ui import clear_console # Import if needed directly in main (e.g., before menu)

def main():
    """Main application loop."""
    db: Optional[JournalDatabase] = None
    try:
        # Initialize database - use constant if defined, e.g., from constants import DB_FILE_NAME
        db = JournalDatabase('Journal.db')

        while True:
            # clear_console() # Optional: Clear console each time menu is shown
            print("\n===== JOURNAL APPLICATION =====")
            print("1. Add a new subject")
            print("2. Add a new entry")
            print("3. View entries for a subject")
            print("4. List all subjects")
            print("5. Credits") # Moved Exit down
            print("6. Exit")
            print("-----------------------------")

            choice = input("Enter your choice (1-6): ").strip()

            # Clear console before showing action output? (Optional)
            # clear_console()

            if choice == '1':
                handle_add_subject(db)
            elif choice == '2':
                handle_add_entry(db)
            elif choice == '3':
                handle_view_entries(db)
            elif choice == '4':
                handle_list_subjects(db)
            elif choice == '5':
                handle_credits()
            elif choice == '6':
                print("Exiting program. Goodbye!")
                break
            else:
                print("Invalid choice. Please enter a number between 1 and 6.")

            # Optional pause before showing the menu again
            if choice not in ('5', '6'): # Don't pause after credits or exit
                 input("\nPress Enter to continue...")

    except DatabaseError as e:
        print(f"\nA critical database error occurred: {e}")
        print("Application cannot continue.")
        sys.exit(1)
    except KeyboardInterrupt:
         print("\nOperation cancelled by user. Exiting.")
         sys.exit(0)
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
        # Consider logging the full traceback here for debugging
        # import traceback
        # traceback.print_exc()
        sys.exit(1)
    finally:
        if db:
            db.close()

if __name__ == "__main__":
    main()

# EOF #
