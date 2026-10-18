import sqlite3
import csv
import os

DATABASE_FILE_PATH = os.path.join(os.path.dirname(__file__), 'database/database.db')


def read_grade_history(file_path):
    try:
        with open(file_path, mode='r', encoding='utf-8-sig') as opened_file:
            reader = csv.DictReader(f)
            for row in reader:
                if any(val and val.strip() and val.strip() != '*' for val in row.values()):
                    return row
                
    except Exception as e:
        return {"ERROR!": str(e)}
    
    return None


def load_grade_history(file_path):
    return None


def preview_degree_plan(file_path):
    return None


def load_degree_plan(file_path):
    return None


def load_reconciliation(reconciliation_file_path = ''):
    reconciliation_map = {}
    return reconciliation_map