import os
import sqlite3
import csv
import argparse


def filter_grades_by_majors(grade_distribution_file, database_file, majors_selected_list):
    if not os.path.exists(grade_distribution_file):
        print("UO Grade Distribution file not found.")
        return []

    if not os.path.exists(database_file):
        print("Database not found.")
        return []
    
    if not majors_selected_list:
        print("No majors were selected to filter them out "
              "from UO Grade Distribution file.")
        return []
    
    database_connection = sqlite3.connect(database_file)
    database_manager = database_connection.cursor()

    major_names_placeholder = ','.join(['?'] * len(majors_selected_list))
    query = f"""
        SELECT DISTINCT subject_code, course_code
        FROM degree_plans
        WHERE major_name IN ({major_names_placeholder})
    """
    database_manager.execute(query, majors_selected_list)
    rows = database_manager.fetchall()
    database_connection.close()

    valid_courses = set((row[0].strip(), row[1].strip()) for row in rows)
    print(f"Filtering for {len(valid_courses)} unique required courses "
          f"for majors: {majors_selected_list}...")
    filtered_rows = []
    total_rows = 0

    with open(grade_distribution_file, mode='r', encoding='utf-8') as opened_file:
        reader = csv.DictReader(opened_file)
        for row in reader:
            total_rows += 1
            course_subject = row.get('SUBJ', '').strip()
            course_number = row.get('NUMB', '').strip()

            if (course_subject, course_number) in valid_courses:
                filtered_rows.append(row)

    print(f"Filtered {len(filtered_rows)} relevant rows out of {total_rows} rows.")
    return filtered_rows


def process_grade_data(filtered_rows):

    def string_to_int(value):
        if not value or str(value).strip() == '*':
            return 0
        try:
            return int(value)
        except ValueError:
            return 0
        
    processed_grades = []
    for row in filtered_rows:
        term_code = row.get('TERM', '').strip()
        term_description = row.get('TERM_DESC', '').strip()
        subject_code = row.get('SUBJ', '').strip()
        course_code = row.get('NUMB', '').strip()
        course_name = row.get('TITLE', '').strip()
        course_crn = row.get('CRN', '').strip()

        unformatted_instructor_name = row.get('INSTRUCTOR', '').strip()
        instructor_name = unformatted_instructor_name
        if ',' in unformatted_instructor_name:
            tokenized_name = unformatted_instructor_name.split(',', 1)
            first_name = tokenized_name[1].strip()
            last_name = tokenized_name[0].strip()
            instructor_name = f"{first_name} {last_name}"

        total_non_withdrawals = row.get('TOT_NON_W', '0').strip()
        total_students = int(total_non_withdrawals) if total_non_withdrawals.isdigit() else -1

        processed_grades.append({
            'TERM_CODE': term_code,
            'TERM_DESC': term_description,
            'SUBJ': subject_code,
            'NUMB': course_code,
            'TITLE': course_name,
            'CRN': course_crn,
            'INSTRUCTOR': instructor_name,
            'GRADE_A': string_to_int(row.get('AP')) + string_to_int(row.get('A')) + string_to_int(row.get('AM')),
            'GRADE_B': string_to_int(row.get('BP')) + string_to_int(row.get('B')) + string_to_int(row.get('BM')),
            'GRADE_C': string_to_int(row.get('CP')) + string_to_int(row.get('C')) + string_to_int(row.get('CM')),
            'GRADE_D': string_to_int(row.get('DP')) + string_to_int(row.get('D')) + string_to_int(row.get('DM')),
            'GRADE_F': string_to_int(row.get('F')),
            'DNF_COUNT': string_to_int(row.get('N')),
            'TOTAL_STUDENTS': total_students
        })

    return processed_grades


def write_processed_grades_to_csv(processed_grades, output_csv_file):
    if not processed_grades:
        print("No processed grades dictionary provided.")
        return False
    
    output_directory = os.path.dirname(output_csv_file)
    if output_directory:
        os.makedirs(output_directory, exist_ok = True)

    csv_file_column_names = [
        'TERM_CODE', 'TERM_DESC', 'SUBJ', 'NUMB', 'TITLE',
        'CRN', 'INSTRUCTOR', 'GRADE_A', 'GRADE_B', 'GRADE_C',
        'GRADE_D', 'GRADE_F', 'DNF_COUNT', 'TOTAL_STUDENTS'
    ]

    try:
        with open(output_csv_file, mode='w', encoding='utf-8') as opened_file:
            writer = csv.DictWriter(opened_file, fieldnames=csv_file_column_names)
            writer.writeheader()
            writer.writerows(processed_grades)
            print("Grade History Distribution file successfully "
                  f"written at: ({output_csv_file})")
            return True
    except IOError as e:
        print(f"Error writing to file {output_csv_file}: {e}")
        return False
    

def run_extract_transform_load_pipeline(raw_file_path, output_file_path, database_path, target_majors):
    filtered_rows = filter_grades_by_majors(raw_file_path, database_path, target_majors)

    if filtered_rows:
        processed_rows = process_grade_data(filtered_rows)
        write_processed_grades_to_csv(processed_rows, output_file_path)


# Can be ran for debugging extract, transform, load pipeline. 
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Process UO Grade Distribution CSV files.")
    parser.add_argument(
        '--input',
        type = str,
        default = 'pub_rec_master_f2015-u2025.csv',
        help = 'File path to the raw UO Grade Distribution CSV file.'
    )
    parser.add_argument(
        '--output',
        type = str,
        default = 'csv_files/Grade_History.CSV',
        help = 'File path to save the processed output CSV file.'
    )

    args = parser.parse_args()

    database_file_path = os.path.join(os.path.dirname(__file__), 'database/database.db')
    target_majors = ['Business Administration', 'Computer Science', 'Philosophy']

    run_extract_transform_load_pipeline(args.input, args.output, database_file_path, target_majors)