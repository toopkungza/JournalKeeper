# Simple Python Journal CLI Application

A command-line interface (CLI) application for creating and managing simple journal entries categorized by subject, built using Python and SQLite.

## Overview

JournalKeeper is a simple yet powerful command-line journal application that allows you to:
- Create and manage subject categories
- Add dated entries to specific subjects
- Retrieve and view your historical entries by subject
- Store information in structured, relational database

The application uses SQLite for data storage, providing a reliable and portable database solution without requiring complex setup.

## Features
- Add new subjects for journal entries.
- Add new journal entries under specific subjects (identified by name or ID).
- View all entries for a chosen subject, sorted oldest or newest first.
- List all existing subjects with their IDs.
- Delete specific journal entries after viewing them.
- Persistent storage using an SQLite database file (`Journal.db`).
- Basic error handling and user feedback.
- Console clearing for better readability when viewing entries.

## Installation

### Requirements
- Python 3.6 or higher (due to f-strings and type hinting usage, though adaptable for older versions)
- SQLite3 (included with Python)
- No external libraries needed (uses built-in `sqlite3`, `os`, `sys`, `datetime`)

## How to Run
1.  Ensure you have Python 3 installed.
2.  Clone this repository or download the `.py` files into a single directory.
3.  Navigate to that directory in your terminal.
4.  Run the application using the command:
    ```bash
    python main.py
    ```
5.  Follow the on-screen menu prompts. The application will create a `Journal.db` file in the same directory to store your data.

## Project Structure
The application is organized into several Python files to promote maintainability and separation of concerns:
*   **`main.py`**:
    *   The main entry point of the application (`if __name__ == "__main__":`).
    *   Contains the primary application loop (`main()` function) that displays the menu and routes user choices to the appropriate handler functions.
    *   Handles overall application setup (database initialization) and teardown (database closing).
    *   Manages top-level error handling (e.g., `DatabaseError`, `KeyboardInterrupt`).
*   **`database.py`**:
    *   Defines the `JournalDatabase` class, encapsulating all interactions with the SQLite database.
    *   Includes methods for connecting, creating tables (`_create_tables`), inserting subjects (`insert_subject`), inserting entries (`insert_entry`), retrieving subjects (`get_all_subjects`), retrieving entries (`get_entries_for_subject`), deleting entries (`delete_entry`), and closing the connection (`close`).
    *   Defines a custom `DatabaseError` exception for database-specific issues.
    *   Uses the `constants.py` module for SQL query strings.
*   **`handlers.py`**:
    *   Contains functions that directly handle the logic for each menu option presented in `main.py`.
    *   Examples: `handle_add_subject`, `handle_add_entry`, `handle_view_entries`, `handle_list_subjects`, `handle_credits`.
    *   These functions orchestrate calls to `ui.py` functions (for input/output) and `database.py` methods (for data manipulation).
*   **`ui.py`**:
    *   Includes functions responsible for user interaction and displaying information to the console.
    *   Examples: `clear_console` (clears the terminal screen), `display_entries` (formats and prints journal entries), `select_subject` (handles the logic for prompting the user to choose a subject by ID or name).
*   **`constants.py`**:
    *   Stores constant values used throughout the application, primarily the SQL query strings.
    *   Centralizing constants makes queries easier to find and modify without searching through other code files.
*   **`Journal.db`** (Generated):
    *   The SQLite database file created automatically when the application runs for the first time. It stores all the subject and entry data.

## Usage

Run the application with:
```
python main.py
```

### Main Menu Options

1. **Add a new subject**
   - Create a new category to organize your entries
   - Subject names must be unique

2. **Add a new entry**
   - Record a new entry under an existing subject
   - If the subject doesn't exist, it will be created automatically
   - Entries are automatically timestamped

3. **View entries for a subject**
   - Display all entries for a specific subject
   - Entries are shown in reverse chronological order (newest first)

4. **List all subjects**
   - View all available subject categories
   
5. **Credits**
   - List the credits

6. **Exit**
   - Close the application

## Data Structure

JournalKeeper uses a simple relational database structure:

### Tables
- **Subject**: Stores subject categories
  - SubjectID (Primary Key)
  - SubjectName (Unique)
  - CreationDate (Log Date for Housekeeping)

- **Entry**: Stores individual journal entries
  - EntryID (Primary Key)
  - SubjectID (Foreign Key)
  - EntryDate (Timestamp)
  - Detail (Entry content)
  - CreationDate (Log Date for Housekeeping)

## Example Use Cases

### Personal Journal
Use JournalKeeper to maintain a personal journal with entries categorized by themes like "Work," "Health," "Goals," etc.

### Project Notes
Track progress and ideas for different projects by creating a subject for each project.

### Research Log
Maintain research notes organized by topic, making it easy to retrieve related entries.

### Habit Tracking
Record daily progress on different habits or activities.

## Technical Details

JournalKeeper DB is built with an object-oriented approach:

- **JournalDatabase class**: Encapsulates all database operations
- **Automatic table creation**: Tables are created if they don't exist
- **Exception handling**: Robust error management throughout
- **Resource management**: Proper connection closing

## Customization

### Database Location
By default, the database file (`Journal.db`) is created in the same directory as the script. You can customize the location by modifying DB_FILE_NAME in constants.py.

### Date Format
The default date format is ISO-style (`YYYY-MM-DD HH:MM:SS`). You can customize this by modifying the `strftime` format in the `insert_entry` method within database.py.

## Best Practices

1. **Regular Backups**: While SQLite is reliable, making occasional backups of your `Journal.db` file is recommended.

2. **Consistent Naming**: Using consistent subject naming conventions will make retrieval easier.

3. **Concise Entries**: While the database can handle lengthy entries, keeping them focused helps with future review.

4. **Single User**: The application is designed for single-user usage and doesn't include authentication.

## Troubleshooting

### Database Lock Errors
If you encounter database lock errors, ensure you don't have the database open in another application.

### Missing Entries
If entries seem to be missing, check if you're using the exact subject name. Subject names are case-sensitive.

## Future Enhancements

Potential future features:
- Search functionality across all entries
- Entry editing
- Entry tagging system
- Export/import capabilities
- Simple statistics (entries per subject, activity over time)
- GUI interface

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License
This project is licensed under the MIT License - see the LICENSE file for details.

---

JournalKeeper - Simple, organized, and persistent journaling.
