import { useEffect, useMemo, useState } from 'react'
import { ApiError, getMajors, getReport, getYears } from '../api'
import { SAMPLE_REPORT } from '../fixtures'
import { academicYearLabel, groupByYearTerm, termName } from '../lib/grades'
import type { ReportResponse } from '../types'
import { CourseCard } from './CourseCard'
import { Button, Callout, Card, EmptyState, SectionHeading, Spinner } from './ui'

type Load<T> =
  | { state: 'loading' }
  | { state: 'ready'; data: T }
  | { state: 'error'; error: string }

export function StudentReport() {
  const [majors, setMajors] = useState<Load<string[]>>({ state: 'loading' })
  const [years, setYears] = useState<Load<string[]>>({ state: 'loading' })

  const [major, setMajor] = useState('')
  const [start, setStart] = useState('')
  const [end, setEnd] = useState('')

  const [report, setReport] = useState<ReportResponse | null>(null)
  const [reportError, setReportError] = useState<string | null>(null)
  const [running, setRunning] = useState(false)
  const [usingSample, setUsingSample] = useState(false)

  // Spec 2.1.1 and 2.1.2: the system must make clear what is actually in the
  // system before asking the student to choose. Both lists are therefore read
  // from the database rather than hardcoded in the UI.
  useEffect(() => {
    let cancelled = false

    getMajors()
      .then((data) => {
        if (cancelled) return
        setMajors({ state: 'ready', data })
        if (data.length > 0) setMajor((current) => current || data[0])
      })
      .catch((error: unknown) => {
        if (!cancelled) setMajors({ state: 'error', error: describe(error) })
      })

    getYears()
      .then((data) => {
        if (cancelled) return
        setYears({ state: 'ready', data })
        if (data.length > 0) {
          setStart((current) => current || data[0])
          setEnd((current) => current || data[data.length - 1])
        }
      })
      .catch((error: unknown) => {
        if (!cancelled) setYears({ state: 'error', error: describe(error) })
      })

    return () => {
      cancelled = true
    }
  }, [])

  // Derived from `years` rather than recreated inline so the memo below has a
  // stable dependency instead of a fresh array identity every render.
  const yearList = useMemo(
    () => (years.state === 'ready' ? years.data : []),
    [years],
  )

  // Spec 2.1.2 allows any span, including a single year, so the only rule
  // enforced here is that the end cannot precede the start.
  const endOptions = useMemo(
    () => yearList.filter((year) => !start || year >= start),
    [yearList, start],
  )

  function onStartChange(value: string) {
    setStart(value)
    if (end && value > end) setEnd(value)
  }

  async function runReport() {
    if (!major || !start || !end) return
    setRunning(true)
    setReportError(null)
    setUsingSample(false)
    try {
      setReport(await getReport(major, start, end))
    } catch (error: unknown) {
      setReport(null)
      setReportError(describe(error))
    } finally {
      setRunning(false)
    }
  }

  const noMajors = majors.state === 'ready' && majors.data.length === 0
  const noYears = years.state === 'ready' && years.data.length === 0
  const selectClass =
    'w-full rounded-md border border-ink-300 bg-white px-2 py-1.5 text-sm disabled:bg-ink-100'

  return (
    <div className="space-y-5">
      <Card className="p-4">
        <SectionHeading hint="Spec 2.1.1 and 2.1.2">Report criteria</SectionHeading>

        <div className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-[2fr_1fr_1fr_auto] lg:items-end">
          <label className="block text-sm">
            <span className="mb-1 block font-medium text-ink-700">Major</span>
            <select
              value={major}
              onChange={(event) => setMajor(event.target.value)}
              disabled={majors.state !== 'ready' || noMajors}
              className={selectClass}
            >
              {majors.state === 'loading' ? <option>Loading</option> : null}
              {noMajors ? <option>No majors loaded</option> : null}
              {majors.state === 'ready' &&
                majors.data.map((name) => (
                  <option key={name} value={name}>
                    {name}
                  </option>
                ))}
            </select>
          </label>

          <label className="block text-sm">
            <span className="mb-1 block font-medium text-ink-700">From</span>
            <select
              value={start}
              onChange={(event) => onStartChange(event.target.value)}
              disabled={years.state !== 'ready' || noYears}
              className={selectClass}
            >
              {noYears ? <option>No data</option> : null}
              {yearList.map((year) => (
                <option key={year} value={year}>
                  {academicYearLabel(year)}
                </option>
              ))}
            </select>
          </label>

          <label className="block text-sm">
            <span className="mb-1 block font-medium text-ink-700">To</span>
            <select
              value={end}
              onChange={(event) => setEnd(event.target.value)}
              disabled={years.state !== 'ready' || noYears}
              className={selectClass}
            >
              {noYears ? <option>No data</option> : null}
              {endOptions.map((year) => (
                <option key={year} value={year}>
                  {academicYearLabel(year)}
                </option>
              ))}
            </select>
          </label>

          <Button
            variant="primary"
            onClick={runReport}
            disabled={running || !major || !start || !end}
          >
            {running ? 'Generating' : 'Generate report'}
          </Button>
        </div>

        {majors.state === 'error' ? (
          <div className="mt-3">
            <Callout tone="danger" title="Could not load majors">
              {majors.error}
            </Callout>
          </div>
        ) : null}

        {years.state === 'error' ? (
          <div className="mt-3">
            <Callout tone="danger" title="Could not load academic years">
              {years.error}
            </Callout>
          </div>
        ) : null}

        {import.meta.env.DEV ? (
          <div className="mt-3 flex flex-wrap items-center gap-3 border-t border-dashed border-ink-200 pt-3">
            <Button
              onClick={() => {
                setReport(SAMPLE_REPORT)
                setReportError(null)
                setUsingSample(true)
              }}
            >
              Load sample report
            </Button>
            <p className="text-xs text-ink-500">
              Development only. Renders fixture data so the report layout can be checked before
              grade history is loaded.
            </p>
          </div>
        ) : null}
      </Card>

      {noMajors ? (
        <EmptyState title="No degree plans are loaded">
          The majors list is read from the <code>degree_plans</code> table, which is empty. Open
          Administration and run the Degree Plans loader.
        </EmptyState>
      ) : null}

      {noYears && !noMajors ? (
        <EmptyState title="No grade history is loaded">
          The year list is read from <code>grade_history</code>, which is empty. Open
          Administration and run the Grade History loader. A report generated now will list the
          required courses with no grade data against any of them.
        </EmptyState>
      ) : null}

      {running ? <Spinner label="Querying grade history" /> : null}

      {reportError ? (
        <Callout tone="danger" title="Report failed">
          {reportError}
        </Callout>
      ) : null}

      {report ? <ReportBody report={report} isSample={usingSample} /> : null}
    </div>
  )
}

function ReportBody({ report, isSample }: { report: ReportResponse; isSample: boolean }) {
  const groups = useMemo(() => groupByYearTerm(report.courses), [report.courses])
  const withoutData = report.courses.filter((course) => !course.has_data).length

  if (report.courses.length === 0) {
    return (
      <EmptyState title="This major has no required courses recorded">
        The degree plan loaded for this major contains no rows.
      </EmptyState>
    )
  }

  return (
    <div className="space-y-4">
      {isSample ? (
        <Callout tone="info" title="Sample data">
          This report is development fixture data, not the contents of the database.
        </Callout>
      ) : null}

      <Card className="p-4">
        <h3 className="text-lg font-semibold text-ink-900">{report.report_title}</h3>
        {report.prepared ? (
          <p className="mt-1 text-sm text-ink-600">Report prepared {report.prepared}.</p>
        ) : null}
        <p className="mt-1 text-sm text-ink-600">
          Data are from {report.time_frame}. {report.courses.length} required courses
          {withoutData > 0 ? `, ${withoutData} without available grade data` : ''}.
        </p>
      </Card>

      {groups.map((group) => (
        <Card key={group.key}>
          {group.year != null && group.term != null ? (
            <header className="border-b border-ink-200 bg-ink-50 px-4 py-2">
              <h3 className="text-sm font-semibold uppercase tracking-wide text-ink-700">
                Year {group.year} &ndash; Term {group.term}
                <span className="ml-2 font-normal normal-case text-ink-500">
                  ({termName(group.term)})
                </span>
              </h3>
            </header>
          ) : null}
          {group.courses.map((course) => (
            <CourseCard key={`${course.subject}-${course.number}`} course={course} />
          ))}
        </Card>
      ))}
    </div>
  )
}

function describe(error: unknown): string {
  if (error instanceof ApiError) {
    const firstLine = error.detail ? error.detail.split('\n')[0] : ''
    return firstLine ? `${error.message} (${firstLine})` : error.message
  }
  return error instanceof Error ? error.message : String(error)
}
