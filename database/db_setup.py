import sqlite3
import os

database_file_path = os.path.join(os.path.dirname(__file__), 'database.db')


def initialize_database():
    connect_to_database = sqlite3.connect(database_file_path)
    database_manager = connect_to_database.cursor()

    database_manager.execute("PRAGMA foreign_keys = ON;")

    database_manager.execute
    ('''
        CREATE TABLE IF NOT EXISTS degree_plans 
        (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            major_name TEXT NOT NULL,
            academic_year INTEGER NOT NULL,
            term_number INTEGER NOT NULL,
            subject_code TEXT NOT NULL,
            course_number TEXT NOT NULL,
            course_name TEXT NOT NULL,
            UNIQUE(major, subject, number)                 
        );
    ''')

    
    return None


if __name__ == '__main__':
    initialize_database()