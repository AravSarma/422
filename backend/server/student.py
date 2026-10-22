import sqlite3
import os

DATABASE_FILE_PATH = os.path.join(os.path.dirname(__file__), '../database/database.db')

def get_majors():
    """Returns all active course structural paths registered inside the local database system."""
    conn = sqlite3.connect(DATABASE_FILE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT major_name FROM degree_plans")
    majors = [row[0] for row in cursor.fetchall()]
    conn.close()
    return majors

def get_academic_years():
    """Scans metrics repository to map available operational time horizons."""
    conn = sqlite3.connect(DATABASE_FILE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT academic_year FROM grade_history WHERE academic_year != '' ORDER BY academic_year ASC")
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
        SELECT academic_year, term_code, subject_code, course_code, course_name 
        FROM degree_plans 
        WHERE major_name = ?
        ORDER BY academic_year ASC, term_code ASC
    ''', (major_name,))
    requirements = cursor.fetchall()
    
    report_course_list = []
    
    for req in requirements:
        subj = req['subject_code']
        numb = req['course_code']
        c_name = req['course_name']
        
        # 2. Extract matched historical data points matching constraints
        cursor.execute('''
            SELECT * FROM grade_history 
            WHERE subject_code = ? AND course_code = ? 
              AND academic_year >= ? AND academic_year <= ?
        ''', (subj, numb, start_year, end_year))
        histories = cursor.fetchall()
        
        course_payload = {
            # arav: added two fields to show year 1 and term 1
            "year": req['academic_year'],
            "term": req['term_code'],
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
        all_redacted = all(h['total_students'] == -1 for h in histories)
        if all_redacted:
            course_payload["has_data"] = False
            course_payload["alert_message"] = f"Class {subj} {numb} is required for the major but no grade data are available."
            report_course_list.append(course_payload)
            continue

        # 3. Calculate unweighted aggregate totals across matching rows
        tot_a, tot_b, tot_c, tot_d, tot_f, tot_dnf, tot_students = 0, 0, 0, 0, 0, 0, 0
        instructor_groups = {}
        
        for h in histories:
            if h['total_students'] == -1: # Skip redacted line items during calculations
                continue
                
            tot_a += h['grade_a']
            tot_b += h['grade_b']
            tot_c += h['grade_c']
            tot_d += h['grade_d']
            tot_f += h['grade_f']
            tot_dnf += h['dnf_count']
            tot_students += h['total_students']
            
            # Group data sets under specific professors to compare rankings
            prof = h['instructor_name'] if h['instructor_name'] else "Unknown Instructor"
            if prof not in instructor_groups:
                instructor_groups[prof] = {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0, "DNF": 0, "total": 0}
                
            instructor_groups[prof]["A"] += h['grade_a']
            instructor_groups[prof]["B"] += h['grade_b']
            instructor_groups[prof]["C"] += h['grade_c']
            instructor_groups[prof]["D"] += h['grade_d']
            instructor_groups[prof]["F"] += h['grade_f']
            instructor_groups[prof]["DNF"] += h['dnf_count']
            instructor_groups[prof]["total"] += h['total_students']

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
