MaxGPA - Backend & Data Pipeline



📋 PRE-REQUISITES

    Before setting up the repository, ensure you have:

    * Historical Grade Distribution CSV Files: 
            Download the two required historical grade distribution CSV files provided in 
            the Project 1 specification into your project directory
            and place it in the folder named 'csv_files'.
            Do NOT rename or alter these file names after downloading, as the 
            automated ETL pipeline relies on the standard filename patterns to parse and 
            ingest grade data correctly.



💾 DATA INITIALIZATION & SETUP

The setup script named 'project_setup.py' builds the SQLite database schema, imports degree requirements, processes Reconciliation.CSV, and transforms the raw historical grade CSVs into Grade_History.CSV. Running this script automatically generates the Grade_History.CSV file and populates the local SQLite database.

Running project_setup.py on the Terminal

    You can run the setup script with an optional --file_path argument to specify the location of raw historical grade files:


        python project_setup.py --file_path pub_rec_master_f2015-u2025.csv


    --file_path Argument: Specifies the path or directory containing your input grade distribution CSV files.

    Default Value: If --file_path is omitted, it defaults to the current working directory (./).



🏃 RUNNING THE LOCAL SERVER

    Start the Flask API server:


        python server.py


    By default, the backend server launches at:
    http://127.0.0.1:5000 (or http://localhost:5000)




🔌 API ENPOINTS FOR FRONT END_INGESTION

    1. Student Reports

        GET /api/report

            Query Parameters:

                major (string, required) - Degree major code (e.g., CS, BA, PHIL)

                start_term (string, optional) - Start term filter (e.g., 201501)

                end_term (string, optional) - End term filter (e.g., 202501)

            Response: Returns degree course requirements, aggregated grade distributions (A, B, C, D, F, DNF), student totals, and instructor performance metrics sorted by student success rates.


    2. Admin & Data Pipeline

        GET /api/admin/preview-history

            Returns a structured JSON preview of the processed Grade_History.CSV file for UI verification.

        POST /api/admin/load-reconciliation

            Triggers a reload of Reconciliation.CSV mapping rules into the SQLite database.

        POST /api/admin/load-history

            Re-executes historical grade data ingestion using active reconciliation mappings.



📂 PROJECT DIRECTORY OVERVIEW

├── database/                  # Local SQLite database & schema files
│   ├── database.db            # Main SQLite database file
│   └── database_setup.py      # Schema creation scripts
├── csv_files/                 # Catalog degree plan CSV files
├── Reconciliation.CSV         # Course reconciliation map (CHANGE_FROM -> TO)
├── Grade_History.CSV          # Cleaned output grade dataset (generated)
├── filter_process_grades.py   # ETL pipeline logic for raw grade data
├── project_setup.py           # Master setup script (accepts --file_path)
├── server.py                  # Flask backend REST API server
└── requirements.txt           # Required Python dependencies