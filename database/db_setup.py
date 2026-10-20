import sqlite3
import os

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
            major_name TEXT NOT NULL,
            academic_year INTEGER NOT NULL,
            term_code INTEGER NOT NULL,
            subject_code TEXT NOT NULL,
            course_number TEXT NOT NULL,
            course_name TEXT NOT NULL,
            UNIQUE(major_name, subject_code, course_number)
        );
    ''')

    database_manager.execute(
    '''
        CREATE TABLE IF NOT EXISTS reconciliations
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
            term_code TEXT,
            term_description TEXT,
            academic_year TEXT,
            subject_code TEXT NOT NULL,
            course_number TEXT NOT NULL,
            instructor_name TEXT,
            grade_a INTEGER DEFAULT 0,
            grade_b INTEGER DEFAULT 0,
            grade_c INTEGER DEFAULT 0,
            grade_d INTEGER DEFAULT 0,
            grade_f INTEGER DEFAULT 0,
            dnf_count INTEGER DEFAULT 0,
            total_students INTEGER DEFAULT 0,
        );
    ''')

    database_connection.commit()
    database_connection.close()

    print("Database initialized successfully!"
          "\nSaved as a file named 'database.db'")


if __name__ == '__main__':
    initialize_database()