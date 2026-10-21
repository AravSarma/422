import sqlite3
import csv
import os

DATABASE_FILE_PATH = os.path.join(os.path.dirname(__file__), 'database/database.db')


def _safe_integer_conversion(value, default=0):
    try: 
        return int(value)
    except (ValueError, TypeError): 
        return default


def read_grade_history(file_path):
    try:
        with open(file_path, mode='r', encoding='utf-8-sig') as opened_file:
            reader = csv.DictReader(opened_file)
            for row in reader:
                if any(val and val.strip() and val.strip() != '*' for val in row.values()):
                    return row
                
    except Exception as e:
        return {"ERROR!": str(e)}
    
    return None


def load_grade_history(file_path):
    database_connection = sqlite3.connect(DATABASE_FILE_PATH)
    database_manager = database_connection.cursor()

    database_manager.execute("SELECT change_from, change_to FROM reconciliation")
    reconcile_map = {row[0]: row[1] for row in database_manager.fetchall()}

    courses_inserted_count = 0
    with open(file_path, mode='r', encoding='utf-8-sig') as opened_file:
        reader = csv.DictReader(opened_file)
        for row in reader:
            course_subject = row.get('SUBJECT_CODE', '').strip()
            if course_subject in reconcile_map:
                course_subject = reconcile_map[course_subject]
            
            database_manager.execute(
            '''
                INSERT INTO grade_history
                (
                    term_code,
                    term_description,
                    academic_year,
                    subject_code,
                    course_code,
                    instructor_name,
                    grade_a,
                    grade_b,
                    grade_c,
                    grade_d,
                    grade_f,
                    dnf_count,
                    total_students
                )
                Values(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''',
                (
                row.get('TERM_CODE', '').strip(),
                row.get('TERM_DESCRIPTION', '').strip(),
                _safe_integer_conversion(row.get('ACADEMIC_YEAR'), 2020),
                course_subject,
                row.get('COURSE_CODE', '').strip(),
                row.get('INSTRUCTOR_NAME', '').strip(),
                _safe_integer_conversion(row.get('GRADE_A', 0)),
                _safe_integer_conversion(row.get('GRADE_B', 0)),
                _safe_integer_conversion(row.get('GRADE_C', 0)),
                _safe_integer_conversion(row.get('GRADE_D', 0)),
                _safe_integer_conversion(row.get('GRADE_F', 0)),
                _safe_integer_conversion(row.get('DNF_COUNT', 0)),
                _safe_integer_conversion(row.get('TOTAL_STUDENTS', 0)),
                ),
            )
            courses_inserted_count += 1

    database_connection.commit()
    database_connection.close()

    return courses_inserted_count


def preview_degree_plan(file_path):
    try:
        with open(file_path, mode='r', encoding='utf-8-sig') as opened_file:
            reader = csv.DictReader(opened_file)
            for row in reader:
                if any(val and val.strip() and val.strip() != '*' for val in row.values()):
                    return row
                
    except Exception as e:
        return {"ERROR!": str(e)}
    
    return None


def load_degree_plan(file_path, major_name):
    database_connection = sqlite3.connect(DATABASE_FILE_PATH)
    database_manager = database_connection.cursor()

    database_manager.execute("DELETE FROM degree_plans WHERE major = ?;", (major_name,))

    courses_loaded_count = 0
    with open(file_path, mode='r', encoding='utf-8-sig') as opened_file:
        reader = csv.DictReader(opened_file)
        for row in reader:
            database_manager.execute(
            '''
                INSERT INTO degree_plans
                (
                    major,
                    year,
                    term,
                    subject,
                    number,
                    title
                )
                VALUES(?, ?, ?, ?, ?, ?)
            ''',
                (
                    major_name,
                    _safe_integer_conversion(row.get('ACAEDMIC_YEAR', 1)),
                    _safe_integer_conversion(row.get('TERM', 1)),
                    row.get('SUBJECT_CODE', '').strip(),
                    row.get('COURSE_CODE', '').strip(),
                    row.get('TITLE', '').strip()
                )
            )
            courses_loaded_count +=1

    database_connection.commit()
    database_connection.close()

    return {"status": "success", "major": major_name, "majors_inserted": courses_loaded_count}


def load_reconciliation(file_path = 'data/Reconciliation.CSV'):
    database_connection = sqlite3.connect(DATABASE_FILE_PATH)
    database_manager = database_connection.cursor()

    database_manager.execute("DELETE FROM reconciliations;")

    reconciliation_loaded_count = 0
    with open(file_path, mode='r', encoding='utf-8-sig') as opened_file:
        reader = csv.DictReader(opened_file)
        for row in reader:
            change_from  = row.get('CHANGE_FROM', '').strip()
            change_to = row.get('TO','').strip()

            if change_from and change_to:
                database_manager.execute(
                    "INSERT or REPLACE INTO reconciliations (change_from, change_to) VALUES (?, ?);",
                    (change_from, change_to)
                )
                reconciliation_loaded_count += 1

    database_connection.commit()
    database_connection.close()
    
    return {"status": "success", "reconciliations_loaded": reconciliation_loaded_count}