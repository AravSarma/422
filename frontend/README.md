# MaxGPA Frontend

React + TypeScript interface for MaxGPA. Design rationale is in
`FRONTEND_DESCRIPTION.md`.

## Running it

Two terminals.

```bash
# 1 - backend
cd backend/database && python db_setup.py   # once
cd ../server && python server.py            # port 8000

# 2 - frontend
cd frontend && npm install
npm run dev                                 # port 5173
```

Open <http://localhost:5173>. No login (spec 2.3.1). `/api` is proxied to port
8000; set `VITE_API_BASE` to point elsewhere.

First run: go to **Administration > Degree plans**, preview, then load. The
major dropdown fills in.

Also: `npm run build`, `npm run lint`.

## Known issues

Two are already fixed, noted only because the symptoms are confusing if they
recur: three modules used different database paths (all now resolve to
`backend/database/database.db`, and SQLite creates a missing file silently, so
the symptom was `no such table` rather than a missing file); and
`admin.load_degree_plan` read column `NUM` where the CSVs use `NUMB`, loading
empty course codes and tripping the `UNIQUE` constraint.

Outstanding, all on the grade-history path:

| # | Issue | Effect |
|---|---|---|
| 1 | `Grade_History.CSV` and `Reconciliation.CSV` are header-only | No charts. Reports list every course as "no grade data available", which is correct per spec 3.2 |
| 2 | `admin.py` reads `SUBJECT_CODE`/`COURSE_CODE`/`INSTRUCTOR_NAME`/`TERM_DESCRIPTION`; `filter_process_grades.py` writes `SUBJ`/`NUMB`/`INSTRUCTOR`/`TERM_DESC` | Same bug class as the `NUMB` fix above. Every course returns `has_data: false` |
| 3 | No CSV has `ACADEMIC_YEAR`; `admin.py:67` defaults it to `2020` | `/api/years` returns only `["2020"]`, so spec 2.1.2 year spans can't be used. Derive it from `TERM_CODE` (`201501` = Fall 2015) |
| 4 | `filter_process_grades.py` has no entry point, and `os.makedirs(..., exists_ok=True)` is a typo for `exist_ok` | Cannot run. Also needs the raw UO file from Canvas, which isn't in the repo |
| 5 | Reconciliation maps `SUBJECT_CODE` only, which is the department | Spec 2.2.3's examples - a title rename and `BA101Z` to `BA101` - are unreachable |
| 6 | No index on `grade_history(subject_code, course_code)` | One full table scan per required course. On 300k rows: 824 ms per major, 3.2 s for three. With an index, 7 ms and 24 ms |
| 7 | `server.py` catches nothing | A handler exception closes the socket with no response; it reaches the browser as a bare 502, and the real error is only in the server terminal |

Frontend limits: per-instructor DNF counts N only (spec 3.4 wants D + F + N,
which the course chart does compute - `student.py` just doesn't expose
per-instructor D and F, and each course says so beneath its table); tabs are
component state, so no deep links; no printed-document view.

To see the charts before grade data exists, use **Load sample report** in the
student view - development builds only, fixture data from `src/fixtures.ts`.

## Two features worth adding

Neither is required by the spec. Listed in dependency order.

### A. Average grade awarded

Reduce a course's distribution to a grade-point number, and a major's courses
to an average. The ConOps calls the report "a predictor of GPA upon completion
of a major" and nothing currently produces one.

Pure frontend maths over existing data. In `src/lib/grades.ts`:

```ts
export function courseGradePoints(m: GlobalMetrics): number | null {
  const graded = m.A + m.B + m.C + m.D + m.F
  if (graded <= 0) return null
  return (4 * m.A + 3 * m.B + 2 * m.C + 1 * m.D) / graded
}
```

Average over `courses.filter(c => c.has_data)`. DNF stays out of the
denominator - an N is not a graded attempt.

Two things not to get wrong:

- **Always show the denominator.** If 12 of 23 courses have data, the figure is
  the average of 12 and will move as data loads. Render it as
  `3.21 - based on 12 of 23 required courses`, never bare.
- **Don't call it a predicted GPA.** It ignores credit hours (`degree_plans`
  has no credits column), ignores who self-selects into a major, and excludes
  electives per spec 3.1. "Average grade awarded across required courses" holds
  up under questioning; "predicted GPA" doesn't.

Effort: low.

### B. Major comparison

Pick two or three majors and one shared year range; show them side by side.
This is the spec's own Figure 1 - two degree plans with no grades - with the
grades filled in, and it answers ConOps goal (a), choosing between majors.

Per major, derived from the existing `/api/report` response: average grade,
A rate, DNF rate, required-course count, data coverage, the three lowest-A-rate
courses by name, and a distribution chart.

Course count must sit next to the average. Philosophy requires 11 courses and
CS 23; comparing those on a flat average without the denominator misleads.

The useful output is the toughest-courses row: *Philosophy averages 3.5 across
11 courses with nothing below 3.2; CS averages 3.1 across 23, but CS 313 and
MATH 252Z are where the GPA goes.*

**Fetch sequentially, not with `Promise.all`.** `server.py` uses `HTTPServer`,
which is single-threaded, so parallel requests queue anyway - and with issue 6
above, three majors is ~3.2 s as one frozen block. Render each column as it
lands:

```ts
for (const major of selected) {
  const report = await getReport(major, start, end)
  setColumns((prev) => [...prev, summarise(report)])
}
```

First column then appears at ~800 ms instead of everything at 3.2 s. Fixing
issue 6 makes this fast regardless, but sequential is correct either way.

Effort: medium. Depends on A for its headline column.
