/**
 * Mirrors the JSON emitted by backend/server/. Every field name here is copied
 * from the Python that produces it, so a rename on either side is a type error
 * rather than an `undefined` at runtime.
 */

/** Per-course totals. Percentages of all students, already rounded to 1dp by the backend. */
export interface GlobalMetrics {
  A: number
  B: number
  C: number
  D: number
  F: number
  DNF: number
}

/**
 * Per-instructor totals. Note the asymmetry with GlobalMetrics: D and F are
 * absent. student.py computes them but never serialises them, so an instructor's
 * non-passing rate cannot be reconstructed here. See lib/grades.ts.
 */
export interface InstructorMetrics {
  A: number
  B: number
  C: number
  DNF: number
}

export interface Instructor {
  instructor_name: string
  /** (A + B) as a percentage of that instructor's students. Backend sorts on this. */
  success_percentage: number
  metrics: InstructorMetrics
}

export interface ReportCourse {
  /**
   * Year and term within the degree plan (year 1-4, term 1=Fall 2=Winter 3=Spring).
   * Optional because they were added to the payload after the rest of the contract
   * existed; the UI falls back to an ungrouped list if a server predates them.
   */
  year?: number
  term?: number
  subject: string
  number: string
  title: string
  /** False when the course has no grade rows at all, or every row was redacted. */
  has_data: boolean
  /** Spec 3.2 wording, supplied by the backend. Empty string when has_data is true. */
  alert_message: string
  global_metrics: GlobalMetrics
  instructors: Instructor[]
}

export interface ReportResponse {
  report_title: string
  /** Preformatted by the backend, e.g. "AY15-AY25". */
  time_frame: string
  courses: ReportCourse[]
}

/**
 * Admin preview payloads are whatever the CSV's header row was, so the shape is
 * not known ahead of time and is rendered generically.
 *
 * `null`  - the file parsed but held no non-asterisk data row (e.g. header only).
 * `ERROR!` - admin.py caught an exception and returned it under that literal key.
 */
export type PreviewRow = Record<string, string> | null

export interface LoadDegreeDetail {
  status: string
  major: string
  majors_inserted: number
}

export interface LoadDegreeResponse {
  status: string
  details: Record<string, LoadDegreeDetail>
}

export interface LoadReconciliationResponse {
  status: string
  mappings_count: number
}

/** POST /api/admin/load-history returns a bare integer, not an object. */
export type LoadHistoryResponse = number
