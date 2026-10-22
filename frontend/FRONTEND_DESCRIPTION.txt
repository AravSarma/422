# MaxGPA Frontend - Technical Description


## Stack

| Layer | Choice | Version |
|---|---|---|
| UI library | React | 19.3.1 |
| Language | TypeScript | 6.0.3 |
| Build / dev server | Vite | 8.3.5 |
| Styling | Tailwind CSS | 4.3.3 |
| Charts | Hand-written inline SVG | - |
| Routing | None (component state) | - |

Four packages total, three of which are the toolchain itself.



**No charting library (Recharts, Chart.js, D3).** The specification asks for one
chart shape: four bars (A, B, C, DNF) on a fixed 0-100% axis with gridlines at
0, 50 and 100 (spec 3.6, and the figure on page 2). That is roughly sixty lines
of SVG, implemented in `src/components/BarChart.tsx`. Recharts would have added
a dependency whose transitive tree is substantially larger than the component it
replaces, and would have had to be defended on a report where "we needed four
rectangles" is not a strong argument. Writing the SVG by hand also meant the
charts could be given exact, consistent geometry across every column they appear
in, which matters because they are read comparatively.

**No router (react-router).** The application has two destinations, Student
Report and Administration. Spec 2.3.1 forbids logins, so there is no session to
restore and no route to guard. A `useState<'student' | 'admin'>` in `App.tsx`
covers it. The cost is real and worth stating: neither view is deep-linkable,
and a page refresh returns to the student view. For a two-destination tool with
no auth, that was judged a better trade than a fifth dependency.

**Tailwind was kept.** It is a build-time dependency that produces plain CSS -
the shipped stylesheet is 16 KB, 4 KB gzipped, with no runtime. It buys
consistent spacing and type scales across roughly a dozen components without a
hand-maintained stylesheet drifting out of sync. It is the one dependency here
that exists for developer throughput rather than necessity, and that is the
honest justification for the report.

---

## 2. Project structure

```
src/
  main.tsx                     React root
  App.tsx                      Shell, header, tab switching
  api.ts                       Every network call; the only module that knows about HTTP
  types.ts                     TypeScript mirror of the backend's JSON contract
  fixtures.ts                  Development-only sample report
  index.css                    Tailwind import, design tokens, grade colours
  lib/
    grades.ts                  Grade maths, DNF definition, Year/Term grouping, AY labels
  components/
    ui.tsx                     Button, Callout, Card, EmptyState, Spinner, SectionHeading
    BarChart.tsx               The SVG grade-distribution chart
    CourseCard.tsx             One required course: chart plus instructor table
    InstructorTable.tsx        Sortable instructor table with expandable charts
    StudentReport.tsx          Student view: criteria controls and report body
    AdminPanel.tsx             Administrative view: three independent loaders
```

The layering rule is that `api.ts` is the only module that performs network
calls or knows about status codes, and `lib/grades.ts` is the only module that
decides what a grade percentage means. Components receive data and render it.
This keeps the two places most likely to change - the backend contract and the
DNF definition - each in a single file.

---

## 3. How the frontend talks to the backend

### 3.1 Everything goes through the Vite proxy

`vite.config.ts` proxies `/api` to `http://127.0.0.1:8000`. The browser only
ever sees its own origin. This is not incidental convenience; it avoids a
specific failure in the backend.

`server.py` sets `Access-Control-Allow-Origin: *` on every response but defines
**no `do_OPTIONS` handler**. Any request that triggers a CORS preflight therefore
receives a `501 Unsupported method ('OPTIONS')` from `BaseHTTPRequestHandler`
and fails before the real request is ever sent. Behind a same-origin proxy no
preflight is ever issued, so the problem cannot occur.

The frontend is nevertheless written to survive without the proxy. Setting
`VITE_API_BASE` points it at another origin, and in that mode the backend's
wildcard CORS header does the work - provided every request stays within the
"simple request" rules that skip preflight. Which leads to the next decision.

### 3.2 POST requests deliberately send no headers and no body

```ts
function post<T>(path: string): Promise<T> {
  return request<T>(path, { method: 'POST' })
}
```

Adding `Content-Type: application/json` - the reflex when writing a POST - would
make the request non-simple and trigger the preflight described above. The three
admin write endpoints take no parameters (`server.py` reads every path and file
name from its own hardcoded constants), so there is nothing to send. The absence
of a body here is a requirement, not an oversight, and is commented as such in
`api.ts`.

### 3.3 The proxy target is 127.0.0.1, not localhost

`server.py` binds with `server_address = ('', port)`, which listens on IPv4 only
(verified: `0.0.0.0:8000`). Node resolves `localhost` to `::1` first on Windows.
A proxy target of `http://localhost:8000` therefore fails with `ECONNREFUSED`
while the server is visibly running. Using the literal IPv4 address removes the
ambiguity.

The same hazard exists in mirror image on the frontend: Vite binds `[::1]:5173`,
IPv6 only. Browsers handle this correctly, so it affects only command-line tools
pointed at `127.0.0.1:5173`.

### 3.4 Error handling has to distinguish three different failures

`server.py` answers almost everything with HTTP 200 and a JSON body, including
failures, so the status code alone is not a success signal. `api.ts` separates:

| Failure | How it appears | What the UI says |
|---|---|---|
| Documented error | `{"error": "..."}`, with 200, 400 or 404 | The backend's own message |
| Preview exception | `{"ERROR!": "..."}` with 200 - `admin.py` catches and returns it under that literal key | The caught Python message |
| Handler crash | No JSON at all | See below |

The third case is the interesting one and the most likely during setup. An
unhandled exception in a handler means `_json_helper` never runs, so Python
aborts the socket without writing a status line. What reaches the browser
depends on the path: through the Vite proxy it arrives as **`502 Bad Gateway`
with a `text/plain` body**; called directly it arrives as a transport-level
rejection. `api.ts` handles both and phrases the 502 case explicitly, because a
crashed handler is indistinguishable from a stopped server unless the message
says so:

> The dev server could not get a response from the Python backend (HTTP 502).
> Either server.py is not running on port 8000, or the request handler raised an
> exception. Check the terminal running server.py.

This matters in practice: with the repository in its shipped state, `/api/majors`
and `/api/years` both crash this way (see `README.md`).

### 3.5 The type contract

`src/types.ts` mirrors the backend's JSON field by field, with names copied from
the Python that emits them. The point is that a rename on either side becomes a
compile error rather than an `undefined` discovered at runtime. Two details are
worth noting.

`ReportCourse.year` and `ReportCourse.term` are optional. They were added to
`student.py` after the rest of the contract existed, and marking them optional
lets the UI degrade to an ungrouped course list against a server that predates
them, rather than rendering a page of empty headings.

`InstructorMetrics` has no `D` or `F`, while `GlobalMetrics` does. That is not a
modelling choice - it reflects that `student.py` computes per-instructor D and F
and then does not serialise them. The consequence is discussed in section 5.

---

## 4. Interface decisions

### 4.1 A dashboard rather than a reproduction of the sample report

The specification illustrates a printed document: a title block, then
`Year 1 - Term 1`, then each course followed by a row of small charts. The
structure of that document is preserved - courses are grouped by year and term,
every course carries an All Instructors chart, instructors are ranked - but it
is presented as an interactive dashboard with sortable tables and expandable
detail rather than a static page.

The trade is explicit: the dashboard is better to use and further from the
figure a grader may be holding. The structural elements the figure demonstrates
are all present, so the comparison should still be legible.

### 4.2 Instructors in a sortable table, charts on demand

The specification's figure shows three instructors side by side as small charts.
Real data does not look like that: a long-running required course such as
`WR 121Z` can have dozens of instructors across a ten-year window, and a wall of
thumbnails is neither readable nor sortable.

`InstructorTable.tsx` renders every instructor as a row with A, B, C, DNF and
A+B percentages, sortable on any column, with each row expanding into the same
chart the figure shows. Nothing the specification illustrates is lost and
ranking is gained. The default sort is `success_percentage` descending, which
matches the order `student.py` already returns, so the first paint agrees with
the API rather than silently reordering it.

Columns use `font-variant-numeric: tabular-nums` so figures stay aligned as
sorting changes the rows.

### 4.3 Year and Term grouping

`student.py` orders required courses by `academic_year, term_code` but did not
originally return either field, so the ordering was invisible to any client. Two
fields were added to the course payload to make the specification's grouping
possible at all. This is the only backend change made for the frontend.

`lib/grades.ts:groupByYearTerm` partitions on those fields and falls back to a
single unlabelled group when they are absent. Headings render as
`Year 1 - Term 1 (Fall)`, carrying both the specification's own notation and the
term name from spec 2.2.2 (1 = Fall, 2 = Winter, 3 = Spring).

### 4.4 Academic-year labelling

Spec 2.1.2 expresses every range in `AY16-AY23` notation, and the backend's own
`time_frame` string uses it. The year selectors therefore display `AY15`, `AY16`
and so on while submitting the raw four-digit value the API expects. Any span is
selectable including a single year; the only constraint enforced is that the end
cannot precede the start, implemented by filtering the end options rather than
by validating after the fact, so an invalid range cannot be selected at all.

### 4.5 Administration: three independent panels

Spec 2.2.4 requires grade history and degree requirements to be updatable
independently, so nothing in `AdminPanel.tsx` is sequenced, numbered or locked
behind another panel.

There is one genuine ordering dependency: `load_grade_history` reads the
`reconciliation` table to build its rename map, so reconciliation must be loaded
first for the mappings to apply. A guided wizard would enforce that and violate
2.2.4. The resolution is a non-blocking note on the Grade History panel stating
that unreconciled data will be stored if reconciliation has not been run. The
administrator is informed and still free to run the panels in any order.

### 4.6 Preview before load, rendered generically

Spec 2.2.1 and 2.2.2 require the administrator to confirm the column mapping
before data is replaced. Both panels implement this as a gate: the load action
does not exist in the DOM until a preview has been fetched, and the confirmation
step offers "Fields look correct, load the file" against "Leave unchanged",
matching the specification's wording that the administrator may proceed or leave
the data unchanged.

The preview is rendered as a generic field/value list rather than a fixed set of
columns. This is the point of the requirement: the administrator is checking
that headings line up with values, and a fixed column set would hide exactly the
mismatch they are looking for. It also means the preview keeps working when UO
supplies files with extra columns, which spec 2.2.1 explicitly anticipates.

A `null` response - which `admin.py` returns when it reaches end of file without
finding a row containing non-asterisk data - is rendered as "No data rows found",
not as an error. A header-only file is a legitimate state, and it is the state
the repository currently ships in.

Two asymmetries in the backend are surfaced in the interface rather than hidden:

- There is no preview endpoint for `Reconciliation.CSV`, so that panel loads
  directly. A comment in the source records why.
- `POST /api/admin/load-degree` takes no file parameter and reloads all three
  degree plans regardless of which one was previewed. The panel states this
  before the confirm button, so an administrator who previewed one file is not
  surprised that confirming rewrote the other two.

### 4.7 Empty states name the action that fixes them

The system ships with an empty database, so "no majors" is the expected first
run, not an error. Rather than an empty dropdown, the student view explains
where the list comes from and what to do:

> The majors list is read from the `degree_plans` table, which is empty. Open
> Administration and run the Degree Plans loader.

### 4.8 Visual design

A restrained neutral palette with University of Oregon green (`#154733`) as the
single accent, used only for the active tab and primary actions. No emoji
anywhere in the interface. Dense but not cramped: the student view is a reading
surface and the admin view is a control surface, and they are styled to feel
different.

Grade bars are semantically coloured (A green, B teal, C amber, DNF red) but
colour is never the only signal - every bar is labelled with its grade and its
value underneath, so the charts survive greyscale printing and colour-vision
deficiency. Each chart carries an `aria-label` summarising its values for screen
readers. Sortable headers use real `<button>` elements and `aria-sort`, and
expandable rows use `aria-expanded`.

---

## 5. Known divergences from the specification

### 5.1 DNF is defined two different ways, and only one is fixable here

Spec 3.4 defines DNF as every non-passing grade: D-, D, D+, F and N.

The backend does not implement that definition. `filter_process_grades.py:96`
sets `DNF_COUNT` from the `N` column alone, while D and F are tallied into
separate fields. At course level those separate fields are serialised, so
`lib/grades.ts:courseDistribution` reconstructs the specification's definition:

```ts
{ label: 'DNF', value: round1(m.D + m.F + m.DNF) }
```

At instructor level the same correction is impossible. `student.py` emits only
A, B, C and DNF per instructor; D and F never leave the backend. The
per-instructor DNF bar is therefore N-only and under-reports relative to the
course bar directly above it.

Rather than hide this, every course states it beneath the instructor table:

> All Instructors DNF counts D, F and N per spec 3.4. Per-instructor DNF counts
> N only, because the API does not expose D and F for an instructor.

The fix is two fields in `student.py`'s instructor payload. Until then this is
the most accurate reading the frontend can offer.

### 5.2 No printed-document view

Choosing a dashboard means there is no view that reproduces the sample report's
printed layout. A print stylesheet collapsing the dashboard into that shape was
scoped and not built.

---

## 6. Requirement traceability

| Requirement | Where |
|---|---|
| 2.1.1 Select major and degree | `StudentReport.tsx` - options read from `/api/majors` |
| 2.1.2 Select years, any span | `StudentReport.tsx` - AY-labelled selects, end filtered to >= start |
| 2.2.1 Read in grade history, with confirmation | `AdminPanel.tsx:GradeHistoryCard` - preview gates load |
| 2.2.2 Read in degree plans, with confirmation | `AdminPanel.tsx:DegreePlanCard` - per-file preview gates load |
| 2.2.3 Read in reconciliation | `AdminPanel.tsx:ReconciliationCard` |
| 2.2.4 Independent updating | Three independent panels, no sequencing |
| 2.3.1 No logins | No auth anywhere in the application |
| 3.2 Asterisk data | `CourseCard.tsx` renders the backend's spec 3.2 sentence instead of an empty chart |
| 3.4 DNF defined | `lib/grades.ts:courseDistribution`; see 5.1 for the instructor-level limit |
| 3.6 Graphs generated by the system | `BarChart.tsx`; pooled-student averaging is done in `student.py` |

---

## 7. Development notes

`src/fixtures.ts` holds a hand-built sample report reachable from a
development-only button in the student view, guarded by `import.meta.env.DEV`
so it is absent from production builds. It exists because the system ships with
an empty `grade_history`, leaving nothing to render against while building. It
is shaped to exercise the awkward paths rather than the happy one: a course with
one instructor, a course with several, a fully redacted course, and a course
whose instructor name is missing upstream.

`.npmrc` sets `legacy-peer-deps=true`. npm 11.3 crashes with
`Cannot read properties of null (reading 'edgesOut')` while resolving an
optional peer chain introduced by Vite 8 (`@vitest/browser` through to
`canvas`). The flag is the documented workaround; committing it to `.npmrc`
means a plain `npm install` works for everyone on the team rather than failing
with an error that looks like a broken repository.
