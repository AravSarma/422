import { useState } from 'react'
import {
  ApiError,
  DEGREE_PLAN_FILES,
  loadDegreePlans,
  loadGradeHistory,
  loadReconciliation,
  previewDegreePlan,
  previewGradeHistory,
} from '../api'
import type { PreviewRow } from '../types'
import { Button, Callout, Card, SectionHeading, Spinner } from './ui'

/**
 * Administrative view.
 *
 * Three self-contained panels, one per data file. They are deliberately
 * independent: spec 2.2.4 requires grade history and degree requirements to be
 * updatable without touching each other, so nothing here is sequenced or
 * locked behind another panel. The one real ordering dependency - grade
 * history applies the reconciliation map at load time - is surfaced as a note
 * rather than a gate.
 */
export function AdminPanel() {
  return (
    <div className="space-y-5">
      <Callout tone="neutral">
        Each data set loads independently (spec 2.2.4). Grade history and degree plans show the
        first populated row of their file before anything is written, so the column mapping can be
        confirmed first (spec 2.2.1, 2.2.2).
      </Callout>

      <ReconciliationCard />
      <GradeHistoryCard />
      <DegreePlanCard />
    </div>
  )
}

/* --------------------------------- preview --------------------------------- */

/**
 * Renders a preview row generically as field/value pairs.
 *
 * The endpoints return whatever the CSV's header row happened to be, so the
 * shape is unknown at compile time. Rendering it generically is also the point
 * of the requirement: the administrator is checking that the headings line up
 * with the values, which a fixed set of columns would hide.
 */
function PreviewTable({ row }: { row: Record<string, string> }) {
  const entries = Object.entries(row)

  if (entries.length === 0) {
    return <p className="text-sm text-ink-500">The row contained no fields.</p>
  }

  return (
    <dl className="divide-y divide-ink-100 rounded-md border border-ink-200 bg-ink-50">
      {entries.map(([field, value]) => (
        <div key={field} className="grid grid-cols-[minmax(8rem,14rem)_1fr] gap-3 px-3 py-1.5">
          <dt className="truncate font-mono text-xs text-ink-500" title={field}>
            {field}
          </dt>
          <dd className="break-words text-sm text-ink-800">
            {value === '' ? <span className="text-ink-400">(empty)</span> : value}
          </dd>
        </div>
      ))}
    </dl>
  )
}

function PreviewResult({ row }: { row: PreviewRow }) {
  // admin.py returns None when it reaches the end of the file without finding a
  // row that has any non-asterisk content. A header-only file lands here, which
  // is the state the repository ships in.
  if (row === null) {
    return (
      <Callout tone="warning" title="No data rows found">
        The file was read successfully but contains no populated rows, only a header. Nothing will
        be loaded.
      </Callout>
    )
  }
  return <PreviewTable row={row} />
}

/* ------------------------------ reconciliation ------------------------------ */

function ReconciliationCard() {
  const [busy, setBusy] = useState(false)
  const [result, setResult] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  async function run() {
    setBusy(true)
    setError(null)
    setResult(null)
    try {
      const response = await loadReconciliation()
      setResult(`${response.status}. ${response.mappings_count} mappings loaded.`)
    } catch (caught: unknown) {
      setError(describe(caught))
    } finally {
      setBusy(false)
    }
  }

  return (
    <Card className="p-4">
      <SectionHeading hint="Spec 2.2.3">Reconciliation</SectionHeading>
      <p className="mt-1 max-w-prose text-sm text-ink-600">
        Loads <code>Reconciliation.CSV</code> (columns <code>CHANGE_FROM</code>, <code>TO</code>)
        into the reconciliation table, replacing its current contents. Load this before grade
        history if the mappings should be applied to it.
      </p>

      {/*
        No preview here: the backend exposes preview endpoints for grade history
        and degree plans only, and spec 2.2.1/2.2.2 require the confirmation
        step for those two. Adding one for this file needs a new route.
      */}
      <div className="mt-3 flex flex-wrap items-center gap-3">
        <Button variant="primary" onClick={run} disabled={busy}>
          {busy ? 'Loading' : 'Load reconciliation'}
        </Button>
        {busy ? <Spinner label="Writing to database" /> : null}
      </div>

      {result ? (
        <div className="mt-3">
          <Callout tone="info">{result}</Callout>
        </div>
      ) : null}
      {error ? (
        <div className="mt-3">
          <Callout tone="danger" title="Load failed">
            {error}
          </Callout>
        </div>
      ) : null}
    </Card>
  )
}

/* ------------------------------- grade history ------------------------------ */

function GradeHistoryCard() {
  const [preview, setPreview] = useState<PreviewRow | undefined>(undefined)
  const [busy, setBusy] = useState<'preview' | 'load' | null>(null)
  const [result, setResult] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  async function runPreview() {
    setBusy('preview')
    setError(null)
    setResult(null)
    try {
      setPreview(await previewGradeHistory())
    } catch (caught: unknown) {
      setPreview(undefined)
      setError(describe(caught))
    } finally {
      setBusy(null)
    }
  }

  async function runLoad() {
    setBusy('load')
    setError(null)
    try {
      const inserted = await loadGradeHistory()
      setResult(`${inserted} grade-history rows inserted.`)
      setPreview(undefined)
    } catch (caught: unknown) {
      setError(describe(caught))
    } finally {
      setBusy(null)
    }
  }

  return (
    <Card className="p-4">
      <SectionHeading hint="Spec 2.2.1">Grade history</SectionHeading>
      <p className="mt-1 max-w-prose text-sm text-ink-600">
        Reads <code>Grade_History.CSV</code>. The file's header row defines how the remaining lines
        are interpreted. Preview the first populated row to confirm the columns map correctly
        before writing anything.
      </p>

      <Callout tone="neutral">
        Subject codes are rewritten using the reconciliation table as rows are inserted. If
        reconciliation has not been loaded, the data will be stored unreconciled.
      </Callout>

      <div className="mt-3 flex flex-wrap items-center gap-3">
        <Button onClick={runPreview} disabled={busy !== null}>
          {busy === 'preview' ? 'Reading' : 'Preview file'}
        </Button>
        {busy ? <Spinner label={busy === 'preview' ? 'Reading file' : 'Writing to database'} /> : null}
      </div>

      {preview !== undefined ? (
        <div className="mt-3 space-y-3">
          <PreviewResult row={preview} />
          {/*
            Spec 2.2.1: having seen the fields, the administrator either proceeds
            or leaves the data unchanged. Load is reachable only from here, so
            the confirmation step cannot be skipped.
          */}
          <div className="flex flex-wrap items-center gap-2">
            <Button variant="primary" onClick={runLoad} disabled={busy !== null}>
              Fields look correct, load the file
            </Button>
            <Button variant="ghost" onClick={() => setPreview(undefined)} disabled={busy !== null}>
              Leave unchanged
            </Button>
          </div>
        </div>
      ) : null}

      {result ? (
        <div className="mt-3">
          <Callout tone="info">{result}</Callout>
        </div>
      ) : null}
      {error ? (
        <div className="mt-3">
          <Callout tone="danger" title="Operation failed">
            {error}
          </Callout>
        </div>
      ) : null}
    </Card>
  )
}

/* ------------------------------- degree plans ------------------------------- */

function DegreePlanCard() {
  const [file, setFile] = useState<string>(DEGREE_PLAN_FILES[0].file)
  const [preview, setPreview] = useState<PreviewRow | undefined>(undefined)
  const [previewedFile, setPreviewedFile] = useState<string | null>(null)
  const [busy, setBusy] = useState<'preview' | 'load' | null>(null)
  const [result, setResult] = useState<string[] | null>(null)
  const [error, setError] = useState<string | null>(null)

  async function runPreview() {
    setBusy('preview')
    setError(null)
    setResult(null)
    try {
      setPreview(await previewDegreePlan(file))
      setPreviewedFile(file)
    } catch (caught: unknown) {
      setPreview(undefined)
      setPreviewedFile(null)
      setError(describe(caught))
    } finally {
      setBusy(null)
    }
  }

  async function runLoad() {
    setBusy('load')
    setError(null)
    try {
      const response = await loadDegreePlans()
      setResult(
        Object.entries(response.details).map(
          ([name, detail]) => `${name}: ${detail.majors_inserted} courses into ${detail.major}`,
        ),
      )
      setPreview(undefined)
      setPreviewedFile(null)
    } catch (caught: unknown) {
      setError(describe(caught))
    } finally {
      setBusy(null)
    }
  }

  return (
    <Card className="p-4">
      <SectionHeading hint="Spec 2.2.2">Degree plans</SectionHeading>
      <p className="mt-1 max-w-prose text-sm text-ink-600">
        Reads one <code>.CSV</code> per degree plan (columns <code>YEAR</code>, <code>TERM</code>,{' '}
        <code>SUBJ</code>, <code>NUMB</code>, <code>TITLE</code>). Each major's existing rows are
        replaced.
      </p>

      <div className="mt-3 flex flex-wrap items-end gap-3">
        <label className="block text-sm">
          <span className="mb-1 block font-medium text-ink-700">File to preview</span>
          <select
            value={file}
            onChange={(event) => setFile(event.target.value)}
            disabled={busy !== null}
            className="rounded-md border border-ink-300 bg-white px-2 py-1.5 text-sm disabled:bg-ink-100"
          >
            {DEGREE_PLAN_FILES.map((entry) => (
              <option key={entry.file} value={entry.file}>
                {entry.file}
              </option>
            ))}
          </select>
        </label>
        <Button onClick={runPreview} disabled={busy !== null}>
          {busy === 'preview' ? 'Reading' : 'Preview file'}
        </Button>
        {busy ? <Spinner label={busy === 'preview' ? 'Reading file' : 'Writing to database'} /> : null}
      </div>

      {preview !== undefined ? (
        <div className="mt-3 space-y-3">
          <p className="text-xs text-ink-500">
            First populated row of <code>{previewedFile}</code>
          </p>
          <PreviewResult row={preview} />
          {/*
            The load route takes no file parameter: server.py hardcodes all
            three degree files and reloads every one of them. Said plainly here
            so the administrator is not surprised that previewing one file and
            confirming rewrites the other two as well.
          */}
          <Callout tone="warning" title="This loads all three degree plans">
            The load endpoint reloads every file in{' '}
            {DEGREE_PLAN_FILES.map((entry) => entry.file).join(', ')}, not only the previewed one.
          </Callout>
          <div className="flex flex-wrap items-center gap-2">
            <Button variant="primary" onClick={runLoad} disabled={busy !== null}>
              Fields look correct, load degree plans
            </Button>
            <Button
              variant="ghost"
              onClick={() => {
                setPreview(undefined)
                setPreviewedFile(null)
              }}
              disabled={busy !== null}
            >
              Leave unchanged
            </Button>
          </div>
        </div>
      ) : null}

      {result ? (
        <div className="mt-3">
          <Callout tone="info" title="Degree plans loaded">
            <ul className="list-inside list-disc">
              {result.map((line) => (
                <li key={line}>{line}</li>
              ))}
            </ul>
          </Callout>
        </div>
      ) : null}
      {error ? (
        <div className="mt-3">
          <Callout tone="danger" title="Operation failed">
            {error}
          </Callout>
        </div>
      ) : null}
    </Card>
  )
}

function describe(error: unknown): string {
  if (error instanceof ApiError) {
    const firstLine = error.detail ? error.detail.split('\n')[0] : ''
    return firstLine ? `${error.message} (${firstLine})` : error.message
  }
  return error instanceof Error ? error.message : String(error)
}
