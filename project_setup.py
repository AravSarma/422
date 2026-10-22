import os
import sys
import argparse
import filter_process_grades
from database import database_setup
from server import admin


def run_setup(raw_input_file):
    print("==================================================")
    print("              Setting up MaxGPA System              ")
    print("==================================================")

    print(f"Target File: {raw_input_file}")

    print("\n[1/5] Initializing local database schema...")
    database_setup.initialize_database()

    # Load reconciliation mappings
    print("\n[2/5] Loading reconciliation mappings...")
    recon_path = os.path.join(os.path.dirname(__file__), 'csv_files/Reconciliation.CSV')
    if os.path.exists(recon_path):
        recon_result = admin.load_reconciliation(recon_path)
        print(f"\tLoaded {recon_result.get('reconciliations_loaded', 0)} reconciliation mappings.")
    else:
        print(f"[{recon_path} not found. Skipping reconciliation loading.]")

    # Load degree plans for target majors
    print("\n[3/5] Loading degree plans for target majors...")
    degree_targets = {
        "Business_Administration_BA.CSV": "Business Administration",
        "Computer_Science_BA.CSV": "Computer Science",
        "Philosophy_BA.CSV": "Philosophy"
    }

    base_dir = os.path.join(os.path.dirname(__file__), 'csv_files/')

    for file_name, major_name in degree_targets.items():
        path = os.path.join(base_dir, file_name)

        if os.path.exists(path):
            res = admin.load_degree_plan(path, major_name)
            print(f"\tLoaded degree plan for {major_name} ({res.get('majors_inserted', 0)} courses).")
    
    print("\n[4/5] Extracting Grade History Distribution for target majors...")
    output_grade_csv = 'csv_files/Grade_History.CSV'
    db_path = os.path.join(os.path.dirname(__file__), 'database/database.db')
    target_majors = ['Business Administration', 'Computer Science', 'Philosophy']
    
    # Run ETL filtering
    if os.path.exists(raw_input_file):
        filter_process_grades.run_extract_transform_load_pipeline(
            raw_input_file, output_grade_csv, db_path, target_majors
        )
    else:
        print(f"[{raw_input_file} not found in root. Skipping ETL — ensure {output_grade_csv} is present.]")

    # Load grade history records
    print("\n[5/5] Loading grade history distribution into database...")
    if os.path.exists(output_grade_csv):
        inserted_grades = admin.load_grade_history(output_grade_csv)
        print(f"\tLoaded {inserted_grades} grade history records.")
    
    print("\n==================================================")
    print("              MaxGPA Setup Complete!              ")
    print("==================================================")


def main():
    parser = argparse.ArgumentParser(description="Initialize database and run ETL for MaxGPA.")
    parser.add_argument(
        '--file', 
        type=str, 
        default='csv_files/pub_rec_master_f2015-u2025.csv',
        help='Name of the original UO grade distribution CSV file.'
    )

    args = parser.parse_args()
    run_setup(args.file)


if __name__ == '__main__':
    main()