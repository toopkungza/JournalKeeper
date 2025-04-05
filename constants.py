# constants.py

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
SELECT e.EntryID, e.EntryDate, e.Detail
FROM Entry e
JOIN Subject s ON e.SubjectID = s.SubjectID
WHERE s.SubjectName = ?
ORDER BY e.EntryDate {} -- Placeholder for ASC/DESC
"""

SELECT_ALL_SUBJECTS = "SELECT SubjectID, SubjectName FROM Subject ORDER BY SubjectName"

DELETE_ENTRY_BY_ID = "DELETE FROM Entry WHERE EntryID = ?"
DB_FILE_NAME = 'Journal.db'

# EOF #
