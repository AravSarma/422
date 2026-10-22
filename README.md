MaxGPA - CS 422 Project 1
=========================

Shows the grade distribution (A, B, C, DNF) for every required class of a
major, plus each instructor's distribution, for a chosen span of academic years.
Runs entirely on this computer. No logins, no external services.

REQUIREMENTS
  Python 3.9 or newer. Nothing else: no Node, no pip packages, no Docker.
  (The web interface is shipped pre-built in frontend/dist.)

INSTALL AND RUN  (5 actions)
  1. Open a terminal in this folder.
  2. python3 -m venv venv
  3. source venv/bin/activate          (Windows: venv\Scripts\activate)
  4. python backend/server/server.py
  5. Open http://127.0.0.1:8000 in a web browser.
  The database (backend/database/database.db) is created automatically.

LOAD THE DATA  (Administration tab)
  The system reads fixed file names from backend/csv_files/ :
    Computer_Science_BA.CSV, Business_Administration_BA.CSV,
    Philosophy_BA.CSV      degree plans (included)
    Reconciliation.CSV     name fixes applied to grade history (included)
    Grade_History.CSV      header only; put the real UO file here (spec 3.8)

  1. Copy the UO grade-history file (either Canvas file) into
     backend/csv_files/ and name it Grade_History.CSV.
  2. Administration > Reconciliation: Load reconciliation.
  3. Administration > Degree plans: choose a file, Preview, then load it.
     Repeat for each of the three plans.
  4. Administration > Grade history: Preview, check the fields, then load.
     Loading replaces all earlier grade history.
  Each of the three data sets can be reloaded on its own at any time.
  Reconciliation is applied while grade history loads, so after changing
  Reconciliation.CSV, load reconciliation and then grade history again.
  The grade file is read using its heading row (TERM, SUBJ, NUMB, INSTRUCTOR,
  AP/A/AM ... N, TOT_NON_W); extra columns are ignored.

USING IT
  Student Report tab: pick a major and a From/To academic year (AY16 = Fall
  2016 - Summer 2017; the 2015-2025 file covers AY15-AY24), then Generate report. Courses with no usable grade data
  (all asterisks) are reported as required but without data (spec 3.2).

REPORT RULES
  A/B/C include plus and minus grades. DNF = D-, D, D+, F and N.
  Percentages are of all students pooled, not averages of class averages.

DELIVERING NEW DEGREE PLANS
  Add a CSV with columns YEAR,TERM,SUBJ,NUMB,TITLE (TERM 1=Fall, 2=Winter,
  3=Spring) and add its file name and major name to DEGREE_PLAN_FILES in
  backend/server/server.py and DEGREE_PLAN_FILES in frontend/src/api.ts
  (then rebuild the frontend as below). Exclude electives and special studies.

RECONCILIATION.CSV
  Columns CHANGE_FROM,TO. Entries may be a course code ("MATH 111,MATH 111Z"),
  a subject code ("CIS,CS") or a course title. Add a line whenever a required
  class shows "no grade data" although the data holds it under another code.

REBUILDING THE INTERFACE (developers only; needs Node 20+)
  cd frontend ; npm install ; npm run build
  Live development: npm run dev (port 5173, proxies /api to port 8000).

FILES
  backend/server/   server.py (HTTP routes + static files), admin.py (loading),
                    student.py (report)
  backend/database/ db_setup.py (SQLite schema)
  frontend/         React/TypeScript source; frontend/dist is the built result
  LIBRARIES_REPORT.txt, frontend/FRONTEND_DESCRIPTION.txt
