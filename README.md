# JournalKeeper

A lightweight SQLite-based journaling application that helps you organize and track entries by subject categories.

## Overview

JournalKeeper is a simple yet powerful command-line journal application that allows you to:
- Create and manage subject categories
- Add dated entries to specific subjects
- Retrieve and view your historical entries by subject
- Store information in structured, relational database

The application uses SQLite for data storage, providing a reliable and portable database solution without requiring complex setup.

## Features

- **Subject Organization**: Categorize your entries by custom subjects
- **Chronological Tracking**: Automatically timestamps all entries
- **Easy Retrieval**: View all entries for a specific subject
- **Simple Interface**: User-friendly command-line menu system
- **Data Persistence**: All entries stored in a local SQLite database
- **Error Handling**: Robust error management for reliable operation

## Installation

### Requirements
- Python 3.6 or higher
- SQLite3 (included with Python)

### Setup
1. Clone this repository:
   ```
   git clone https://github.com/toopkungza/journalkeeper.git
   cd journalkeeper
   ```

2. No additional dependencies required - JournalKeeper uses only Python standard libraries.

## Usage

Run the application with:
```
python journalkeeper.py
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

5. **Exit**
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
By default, the database file (`journal.db`) is created in the same directory as the script. You can customize the location by modifying the `db_file` parameter when initializing `JournalDatabase`.

### Date Format
The default date format is ISO-style (`YYYY-MM-DD HH:MM:SS`). You can customize this by modifying the `strftime` format in the `insert_entry` method.

## Advanced Usage

### Programmatic API
The `JournalDatabase` class can be imported and used in other Python scripts:

```python
from journalkeeper import JournalDatabase

# Initialize database
db = JournalDatabase('custom_location.db')

# Add a subject
db.insert_subject('Work')

# Add an entry
db.insert_entry('Work', 'Completed the quarterly report')

# Retrieve entries
entries, message = db.get_entries_for_subject('Work')
for date, detail in entries:
    print(f"{date}: {detail}")

# Clean up
db.close()
```

## Best Practices

1. **Regular Backups**: While SQLite is reliable, making occasional backups of your `journal.db` file is recommended.

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
- Entry editing and deletion
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
