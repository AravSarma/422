import csv
import os
import re
import sqlite3

DATABASE_FILE_PATH = os.path.join(os.path.dirname(__file__), '../database/database.db')


# ---------------------------------------------------------------------------
# Grade-history column mapping (spec 2.2.1)
#
# The heading row of the file decides where each value comes from. UO has
# always used the same heading names, so each field lists the headings it may
# appear under; the first one present in the file wins. The grade columns are
# summed: "A" is AP + A + AM, and so on.
# ---------------------------------------------------------------------------
FIELD_HEADINGS = {
    'term_code': ['TERM', 'TERM_CODE'],
    'term_description': ['TERM_DESC', 'TERM_DESCRIPTION'],
    'subject': ['SUBJ', 'SUBJECT_CODE', 'SUBJECT'],
    'number': ['NUMB', 'COURSE_CODE', 'COURSE_NUMBER'],
    'title': ['TITLE', 'COURSE_TITLE'],
    'instructor': ['INSTRUCTOR', 'INSTRUCTOR_NAME'],
    'total': ['TOT_NON_W', 'TOTAL_STUDENTS'],
}

GRADE_HEADINGS = {
    'A': ['AP', 'A', 'AM', 'GRADE_A'],
    'B': ['BP', 'B', 'BM', 'GRADE_B'],
    'C': ['CP', 'C', 'CM', 'GRADE_C'],
    'D': ['DP', 'D', 'DM', 'GRADE_D'],
    'F': ['F', 'GRADE_F'],
    # N is "no pass". D and F are kept separately so spec 3.4 (DNF = D-, D, D+,
    # F, N) can be assembled by whoever reads the table.
    'N': ['N', 'DNF_COUNT'],
}

REDACTED = -1  # total_students value stored for an all-asterisk (redacted) row


def _safe_integer_conversion(value, default=0):
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def _headings_present(fieldnames, wanted):
    """The wanted headings that exist in the file, matched ignoring case."""
    lookup = {name.strip().upper(): name for name in (fieldnames or []) if name}
    return [lookup[w] for w in wanted if w in lookup]


def _build_column_map(fieldnames):
    """Works out, from the heading row alone, how to read every data row."""
    columns = {}
    for field, wanted in FIELD_HEADINGS.items():
        found = _headings_present(fieldnames, wanted)
        columns[field] = found[0] if found else None

    missing = [f for f in ('term_code', 'subject', 'number') if columns[f] is None]
    if missing:
        raise ValueError(
            "Grade-history file is missing required column(s): "
            + ", ".join(FIELD_HEADINGS[m][0] for m in missing)
            + ". Headings found: " + ", ".join(n for n in fieldnames if n)
        )

    grades = {g: _headings_present(fieldnames, wanted) for g, wanted in GRADE_HEADINGS.items()}
    if not any(grades.values()):
        raise ValueError("Grade-history file has no grade-count columns (A, B, C, ...).")
    return columns, grades


def _count(value):
    """An integer count; blanks and asterisks count as zero."""
    value = (value or '').strip()
    return int(value) if value.isdigit() else 0


def _academic_year(term_code):
    """UO term codes are YYYYTT with YYYY the academic year (201501 = Fall 2015,
    201502 = Winter 2016). AY16 runs Fall 2016 through Summer 2017 (spec 2.1.2)."""
    term_code = (term_code or '').strip()
    return term_code[:4] if term_code[:4].isdigit() else ''


# ---------------------------------------------------------------------------
# Previews
# ---------------------------------------------------------------------------
def read_grade_history(file_path):
    """First row of non-null, non-asterisk data, for the administrator to check
    that headings and values line up before anything is replaced (spec 2.2.1).

    Prefers a row with no asterisk in any field. If every row has some, falls
    back to the first row that has any real value. Returns None if there is none.
    """
    try:
        fallback = None
        with open(file_path, mode='r', encoding='utf-8-sig', newline='') as opened_file:
            reader = csv.DictReader(opened_file)
            for row in reader:
                values = [(v or '').strip() for v in row.values() if not isinstance(v, list)]
                if not any(v and v != '*' for v in values):
                    continue
                if '*' not in values:
                    return row
                if fallback is None:
                    fallback = row
        return fallback
    except Exception as e:
        return {"ERROR!": str(e)}


def preview_degree_plan(file_path):
    try:
        with open(file_path, mode='r', encoding='utf-8-sig', newline='') as opened_file:
            reader = csv.DictReader(opened_file)
            for row in reader:
                if any(val and val.strip() and val.strip() != '*' for val in row.values()):
                    return row
    except Exception as e:
        return {"ERROR!": str(e)}

    return None


# ---------------------------------------------------------------------------
# Reconciliation (spec 2.2.3) - applied to the grade history as it is loaded
# ---------------------------------------------------------------------------
_COURSE_CODE = re.compile(r'^\s*([A-Za-z]{1,6})\s*(\d{3}[A-Za-z]?)\s*$')
_SUBJECT_ONLY = re.compile(r'^[A-Z]{1,6}$')


def _course_code(text):
    """'BA101Z' or 'BA 101Z' -> ('BA', '101Z'); None if it is not a course code."""
    match = _COURSE_CODE.match(text or '')
    return (match.group(1).upper(), match.group(2).upper()) if match else None


class _Reconciler:
    """Rewrites grade-history values using Reconciliation.CSV.

    CHANGE_FROM, TO may be a course code ("BA101" -> "BA101Z"), a bare subject
    code ("CIS" -> "CS"), or anything else, which is treated as a course title
    ("Intro to Business" -> "Introduction to Business").
    """

    def __init__(self, pairs):
        self.courses, self.subjects, self.titles = {}, {}, {}
        for change_from, change_to in pairs:
            change_from, change_to = (change_from or '').strip(), (change_to or '').strip()
            from_code, to_code = _course_code(change_from), _course_code(change_to)
            if from_code and to_code:
                self.courses[from_code] = to_code
            elif _SUBJECT_ONLY.match(change_from) and _SUBJECT_ONLY.match(change_to):
                self.subjects[change_from] = change_to
            elif change_from:
                self.titles[change_from] = change_to

    def apply(self, subject, number, title):
        subject, number = subject.strip().upper(), number.strip().upper()
        subject = self.subjects.get(subject, subject)
        subject, number = self.courses.get((subject, number), (subject, number))
        title = self.titles.get(title.strip(), title.strip())
        return subject, number, title


def _format_instructor(name):
    """UO lists 'Last, First'; the report shows 'First Last'."""
    name = (name or '').strip()
    if ',' in name:
        last, first = name.split(',', 1)
        return f"{first.strip()} {last.strip()}".strip()
    return name


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------
def load_grade_history(file_path):
    """Replaces the grade history with the contents of the file. Returns the
    number of rows stored. Nothing is changed if the file cannot be read."""
    with open(file_path, mode='r', encoding='utf-8-sig', newline='') as opened_file:
        reader = csv.DictReader(opened_file)
        columns, grades = _build_column_map(reader.fieldnames)

        database_connection = sqlite3.connect(DATABASE_FILE_PATH)
        try:
            cursor = database_connection.cursor()
            cursor.execute("SELECT change_from, change_to FROM reconciliation")
            reconciler = _Reconciler(cursor.fetchall())

            def field(row, name):
                heading = columns[name]
                return (row.get(heading) or '').strip() if heading else ''

            batch = []
            for row in reader:
                subject, number, title = reconciler.apply(
                    field(row, 'subject'), field(row, 'number'), field(row, 'title'))
                if not subject or not number or subject == '*' or number == '*':
                    continue

                counts = {g: sum(_count(row.get(h)) for h in headings)
                          for g, headings in grades.items()}

                # An asterisk (or missing) total means the registrar redacted the
                # whole line; keep it so student.py can tell "redacted" from
                # "no such class" (spec 3.2).
                # UO redacts a section by replacing every grade count with '*'
                # while TOT_NON_W stays numeric, so check the counts themselves.
                grade_cells = [(row.get(h) or '').strip() for hs in grades.values() for h in hs]
                raw_total = field(row, 'total')
                if grade_cells and all(c == '*' for c in grade_cells):
                    total = REDACTED
                elif columns['total'] is None:
                    total = sum(counts.values())
                elif raw_total.isdigit():
                    total = int(raw_total)
                else:
                    total = REDACTED

                term_code = field(row, 'term_code')
                batch.append((
                    term_code,
                    field(row, 'term_description'),
                    _academic_year(term_code),
                    subject,
                    number,
                    title,
                    _format_instructor(field(row, 'instructor')),
                    counts['A'], counts['B'], counts['C'], counts['D'], counts['F'],
                    counts['N'],
                    total,
                ))

            cursor.execute("DELETE FROM grade_history;")
            cursor.executemany(
                '''
                INSERT INTO grade_history
                (term_code, term_description, academic_year, subject_code, course_code,
                 course_title, instructor_name, grade_a, grade_b, grade_c, grade_d,
                 grade_f, dnf_count, total_students)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                batch,
            )
            database_connection.commit()
            return len(batch)
        except Exception:
            database_connection.rollback()
            raise
        finally:
            database_connection.close()


def load_degree_plan(file_path, major_name):
    database_connection = sqlite3.connect(DATABASE_FILE_PATH)
    try:
        database_manager = database_connection.cursor()
        database_manager.execute("DELETE FROM degree_plans WHERE major_name = ?;", (major_name,))

        courses_loaded_count = 0
        with open(file_path, mode='r', encoding='utf-8-sig', newline='') as opened_file:
            reader = csv.DictReader(opened_file)
            for row in reader:
                subject = (row.get('SUBJ') or '').strip()
                number = (row.get('NUMB') or '').strip()
                if not subject or not number:
                    continue
                database_manager.execute(
                    '''
                    INSERT OR REPLACE INTO degree_plans
                    (major_name, academic_year, term_code, subject_code, course_code, course_name)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ''',
                    (
                        major_name,
                        _safe_integer_conversion(row.get('YEAR'), 1),
                        _safe_integer_conversion(row.get('TERM'), 1),
                        subject,
                        number,
                        (row.get('TITLE') or '').strip(),
                    ),
                )
                courses_loaded_count += 1

        database_connection.commit()
    except Exception:
        database_connection.rollback()
        raise
    finally:
        database_connection.close()

    return {"status": "success", "major": major_name, "majors_inserted": courses_loaded_count}


def load_reconciliation(file_path):
    database_connection = sqlite3.connect(DATABASE_FILE_PATH)
    try:
        database_manager = database_connection.cursor()
        database_manager.execute("DELETE FROM reconciliation;")

        reconciliation_loaded_count = 0
        with open(file_path, mode='r', encoding='utf-8-sig', newline='') as opened_file:
            reader = csv.DictReader(opened_file, skipinitialspace=True)
            for row in reader:
                change_from = (row.get('CHANGE_FROM') or '').strip()
                change_to = (row.get('TO') or '').strip()

                if change_from and change_to:
                    database_manager.execute(
                        "INSERT OR REPLACE INTO reconciliation (change_from, change_to) VALUES (?, ?);",
                        (change_from, change_to),
                    )
                    reconciliation_loaded_count += 1

        database_connection.commit()
    except Exception:
        database_connection.rollback()
        raise
    finally:
        database_connection.close()

    return {"status": "success", "reconciliations_loaded": reconciliation_loaded_count}
