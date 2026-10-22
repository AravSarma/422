import sqlite3
import os

DATABASE_FILE_PATH = os.path.join(os.path.dirname(__file__), '../database/database.db')

def get_majors():
    """Returns all active course structural paths registered inside the local database system."""
    conn = sqlite3.connect(DATABASE_FILE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT MAJOR_NAME FROM degree_plans")
    majors = [row[0] for row in cursor.fetchall()]
    conn.close()
    return majors

def get_academic_years():
    """Scans metrics repository to map available operational time horizons."""
    conn = sqlite3.connect(DATABASE_FILE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT SUBSTR(TERM, 1, 4) FROM grade_history WHERE TERM IS NOT NULL AND TERM != '' ORDER BY TERM ASC")
    years = [row[0] for row in cursor.fetchall() if row[0].isdigit()]
    conn.close()
    # Returns formatted string ranges (e.g., ["2015", "2016"])
    return years

def generate_student_report(major_name, start_year, end_year):
    """Calculates macro grade weights and ranks high-performing instructors across windows."""
    conn = sqlite3.connect(DATABASE_FILE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 1. Fetch requirements matching chosen major
    cursor.execute('''
        SELECT YEAR, TERM, SUBJ, NUMB, TITLE 
        FROM degree_plans 
        WHERE MAJOR_NAME = ?
        ORDER BY YEAR ASC, TERM ASC
    ''', (major_name,))
    requirements = cursor.fetchall()
    
    report_course_list = []
    
    for req in requirements:
        subj = req['SUBJ']
        numb = req['NUMB']
        c_name = req['TITLE']
        
        # 2. Extract matched historical data points matching constraints
        cursor.execute('''
            SELECT * FROM grade_history 
            WHERE SUBJ = ? AND NUMB = ? 
                AND SUBSTR(TERM, 1, 4) >= ? AND SUBSTR(TERM, 1, 4) <= ?
        ''', (subj, numb, str(start_year), str(end_year)))
        histories = cursor.fetchall()
        
        course_payload = {
            "subject": subj,
            "number": numb,
            "title": c_name,
            "has_data": True,
            "alert_message": "",
            "global_metrics": {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0, "DNF": 0},
            "instructors": []
        }
        
        if not histories:
            # Missing completely fallback check rule configuration
            course_payload["has_data"] = False
            course_payload["alert_message"] = f"Class {subj} {numb} is required for the major but no grade data are available."
            report_course_list.append(course_payload)
            continue
            
        # Check if all returned lines were flagged as fully redacted (-1 total_students)
        all_redacted = all(h['TOTAL_STUDENTS'] == -1 for h in histories)
        if all_redacted:
            course_payload["has_data"] = False
            course_payload["alert_message"] = f"Class {subj} {numb} is required for the major but no grade data are available."
            report_course_list.append(course_payload)
            continue

        # 3. Calculate unweighted aggregate totals across matching rows
        tot_a, tot_b, tot_c, tot_d, tot_f, tot_dnf, tot_students = 0, 0, 0, 0, 0, 0, 0
        instructor_groups = {}
        
        for h in histories:
            if h['TOTAL_STUDENTS'] == -1: # Skip redacted line items during calculations
                continue
                
            tot_a += h['GRADE_A']
            tot_b += h['GRADE_B']
            tot_c += h['GRADE_C']
            tot_d += h['GRADE_D']
            tot_f += h['GRADE_F']
            tot_dnf += h['DNF_COUNT']
            tot_students += h['TOTAL_STUDENTS']
            
            # Group data sets under specific professors to compare rankings
            prof = h['INSTRUCTOR'] if h['INSTRUCTOR'] else "Unknown Instructor"
            if prof not in instructor_groups:
                instructor_groups[prof] = {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0, "DNF": 0, "total": 0}
                
            instructor_groups[prof]["A"] += h['GRADE_A']
            instructor_groups[prof]["B"] += h['GRADE_B']
            instructor_groups[prof]["C"] += h['GRADE_C']
            instructor_groups[prof]["D"] += h['GRADE_D']
            instructor_groups[prof]["F"] += h['GRADE_F']
            instructor_groups[prof]["DNF"] += h['DNF_COUNT']
            instructor_groups[prof]["total"] += h['TOTAL_STUDENTS']

        # Populate calculations into core structural payload distributions
        if tot_students > 0:
            course_payload["global_metrics"] = {
                "A": round((tot_a / tot_students) * 100, 1),
                "B": round((tot_b / tot_students) * 100, 1),
                "C": round((tot_c / tot_students) * 100, 1),
                "D": round((tot_d / tot_students) * 100, 1),
                "F": round((tot_f / tot_students) * 100, 1),
                "DNF": round((tot_dnf / tot_students) * 100, 1)
            }
            
        # 4. Process individual instructor segments and sort by highest A/B metrics
        compiled_profs = []
        for prof_name, metrics in instructor_groups.items():
            if metrics["total"] == 0:
                continue
            
            # Sort factor calculation configuration: Rank by top marks achieved under instruction
            success_rate = ((metrics["A"] + metrics["B"]) / metrics["total"]) * 100
            
            compiled_profs.append({
                "instructor_name": prof_name,
                "success_percentage": round(success_rate, 1),
                "metrics": {
                    "A": round((metrics["A"] / metrics["total"]) * 100, 1),
                    "B": round((metrics["B"] / metrics["total"]) * 100, 1),
                    "C": round((metrics["C"] / metrics["total"]) * 100, 1),
                    "DNF": round((metrics["DNF"] / metrics["total"]) * 100, 1)
                }
            })
            
        # Enforce sequence: display highest performers first so students can plan ahead
        compiled_profs.sort(key=lambda x: x['success_percentage'], reverse=True)
        course_payload["instructors"] = compiled_profs
        
        report_course_list.append(course_payload)
        
    conn.close()
    
    return {
        "report_title": f"Grades Assigned Across UO Classes for {major_name}",
        "time_frame": f"AY{start_year[-2:]}-AY{end_year[-2:]}",
        "courses": report_course_list
    }
