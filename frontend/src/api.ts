import type {
  LoadDegreeResponse,
  LoadHistoryResponse,
  LoadReconciliationResponse,
  PreviewRow,
  ReportResponse,
} from './types'

/**
 * Empty by default: requests go to the Vite dev proxy on the page's own origin,
 * which forwards /api to the Python server. Set VITE_API_BASE to call a server
 * elsewhere (that path relies on the backend's Access-Control-Allow-Origin: *).
 */
const BASE = import.meta.env.VITE_API_BASE ?? ''

export class ApiError extends Error {
  readonly status: number
  /** Operator-facing detail: a Python traceback, an HTML error page, etc. */
  readonly detail?: string

  constructor(message: string, status: number, detail?: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.detail = detail
  }
}

/**
 * server.py answers nearly everything with HTTP 200 and a JSON body, including
 * failures, so the status code alone is not a reliable success signal. An
 * unhandled exception in a handler is different again: http.server aborts the
 * response, and what reaches us is a transport error or a non-JSON body. All
 * three cases have to be distinguished before anything is returned to the UI.
 */
async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response
  try {
    response = await fetch(`${BASE}${path}`, init)
  } catch {
    // Reached when nothing answered at all. Behind the dev proxy that means
    // Vite itself is gone; with VITE_API_BASE set it also covers a Python
    // handler that raised and closed the socket without writing a status line.
    throw new ApiError(
      'No response from the MaxGPA server. Check that server.py is running on port 8000, and that the dev server is still up.',
      0,
    )
  }

  const text = await response.text()

  let parsed: unknown
  try {
    parsed = JSON.parse(text)
  } catch {
    // An unhandled exception in a handler never produces a JSON body. Python
    // aborts the socket, and the Vite proxy turns that dead connection into a
    // 502 with a text/plain body, so this is the branch a backend crash
    // actually lands in during development.
    const message =
      response.status === 502
        ? 'The dev server could not get a response from the Python backend (HTTP 502). Either server.py is not running on port 8000, or the request handler raised an exception. Check the terminal running server.py.'
        : `The server returned a non-JSON response (HTTP ${response.status}). This usually means a handler raised an exception.`
    throw new ApiError(message, response.status, text.slice(0, 500))
  }

  // The documented error shape: {"error": "..."} , sent with 400, 404 or 200.
  if (parsed && typeof parsed === 'object' && 'error' in parsed) {
    throw new ApiError(String((parsed as { error: unknown }).error), response.status)
  }

  // admin.py's preview helpers swallow exceptions and return them under this
  // literal key, so a malformed or missing CSV arrives as a 200 "success".
  if (parsed && typeof parsed === 'object' && 'ERROR!' in parsed) {
    throw new ApiError(
      String((parsed as Record<string, unknown>)['ERROR!']),
      response.status,
    )
  }

  if (!response.ok) {
    throw new ApiError(`Request failed with HTTP ${response.status}.`, response.status)
  }

  return parsed as T
}

/**
 * Writes carry no body and no headers on purpose. Adding Content-Type:
 * application/json would make the request non-simple, and the browser would
 * send an OPTIONS preflight that BaseHTTPRequestHandler answers with 501
 * because server.py defines no do_OPTIONS. Harmless behind the dev proxy,
 * fatal when VITE_API_BASE points at a different origin.
 */
function post<T>(path: string): Promise<T> {
  return request<T>(path, { method: 'POST' })
}

/* ---------------------------------- student --------------------------------- */

/** Distinct major_name values present in degree_plans. Empty until plans are loaded. */
export function getMajors(): Promise<string[]> {
  return request<string[]>('/api/majors')
}

/** Distinct academic_year values present in grade_history, ascending. */
export function getYears(): Promise<string[]> {
  return request<string[]>('/api/years')
}

export function getReport(
  major: string,
  start: string,
  end: string,
): Promise<ReportResponse> {
  const query = new URLSearchParams({ major, start, end })
  return request<ReportResponse>(`/api/report?${query}`)
}

/* ----------------------------------- admin ---------------------------------- */

export function previewGradeHistory(): Promise<PreviewRow> {
  return request<PreviewRow>('/api/admin/preview-history')
}

export function previewDegreePlan(file: string): Promise<PreviewRow> {
  const query = new URLSearchParams({ file })
  return request<PreviewRow>(`/api/admin/preview-degree?${query}`)
}

export function loadGradeHistory(): Promise<LoadHistoryResponse> {
  return post<LoadHistoryResponse>('/api/admin/load-history')
}

export function loadDegreePlans(): Promise<LoadDegreeResponse> {
  return post<LoadDegreeResponse>('/api/admin/load-degree')
}

export function loadReconciliation(): Promise<LoadReconciliationResponse> {
  return post<LoadReconciliationResponse>('/api/admin/load-reconciliation')
}

/**
 * server.py hardcodes exactly these three files in its load-degree handler, so
 * the picker must mirror that list. Adding a fourth major means editing both.
 */
export const DEGREE_PLAN_FILES = [
  { file: 'Computer_Science_BA.CSV', major: 'Computer Science' },
  { file: 'Business_Administration_BA.CSV', major: 'Business Administration' },
  { file: 'Philosophy_BA.CSV', major: 'Philosophy' },
] as const
