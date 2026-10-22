import sqlite3
import os

os.makedirs(os.path.join(os.path.dirname(__file__), 'database'), exist_ok=True)
DATABASE_FILE_PATH = os.path.join(os.path.dirname(__file__), 'database.db')


def initialize_database():
    database_connection = sqlite3.connect(DATABASE_FILE_PATH)
    database_manager = database_connection.cursor()

    database_manager.execute("PRAGMA foreign_keys = ON;")

    database_manager.execute(
    '''
        CREATE TABLE IF NOT EXISTS degree_plans 
        (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            MAJOR_NAME TEXT NOT NULL,
            YEAR INTEGER NOT NULL,
            TERM INTEGER NOT NULL,
            SUBJ TEXT NOT NULL,
            NUMB TEXT NOT NULL,
            TITLE TEXT NOT NULL,
            UNIQUE(MAJOR_NAME, SUBJ, NUMB)
        );
    ''')

    database_manager.execute(
    '''
        CREATE TABLE IF NOT EXISTS reconciliation
        (
            change_from TEXT PRIMARY KEY,
            change_to TEXT
        );
    ''')

    database_manager.execute(
    '''
        CREATE TABLE IF NOT EXISTS grade_history
        (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            TERM TEXT,
            TERM_DESC TEXT,
            SUBJ TEXT NOT NULL,
            NUMB TEXT NOT NULL,
            TITLE TEXT,
            CRN TEXT,
            INSTRUCTOR TEXT,
            GRADE_A INTEGER DEFAULT 0,
            GRADE_B INTEGER DEFAULT 0,
            GRADE_C INTEGER DEFAULT 0,
            GRADE_D INTEGER DEFAULT 0,
            GRADE_F INTEGER DEFAULT 0,
            DNF_COUNT INTEGER DEFAULT 0,
            TOTAL_STUDENTS INTEGER DEFAULT 0
        );
    ''')

    database_connection.commit()
    database_connection.close()

    print("Database initialized successfully!"
          "\nSaved as a file: 'database.db'"
          "\nFile stored in directory named: 'database'")


if __name__ == '__main__':
    initialize_database()