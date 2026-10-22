import { Fragment, useMemo, useState } from 'react'
import type { Instructor } from '../types'
import { instructorDistribution } from '../lib/grades'
import { BarChart } from './BarChart'

type SortKey = 'instructor_name' | 'A' | 'B' | 'C' | 'DNF' | 'success_percentage'
type Direction = 'asc' | 'desc'

interface Column {
  key: SortKey
  label: string
  numeric: boolean
  title?: string
}

const COLUMNS: Column[] = [
  { key: 'instructor_name', label: 'Instructor', numeric: false },
  { key: 'A', label: 'A', numeric: true },
  { key: 'B', label: 'B', numeric: true },
  { key: 'C', label: 'C', numeric: true },
  { key: 'DNF', label: 'DNF', numeric: true, title: 'Non-passing: D, F and N.' },
  { key: 'success_percentage', label: 'A + B', numeric: true, title: 'Share of students awarded an A or a B.' },
]

function valueOf(instructor: Instructor, key: SortKey): string | number {
  switch (key) {
    case 'instructor_name':
      return instructor.instructor_name.toLowerCase()
    case 'success_percentage':
      return instructor.success_percentage
    default:
      return instructor.metrics[key]
  }
}

/**
 * Every instructor who has taught the course in the selected window.
 *
 * A table rather than the row of small charts in the spec's figure: that figure
 * shows three instructors, while a long-running required course can have
 * dozens, and a wall of thumbnails is unreadable and unsortable. The charts are
 * still reachable - a row expands into one - so nothing the spec illustrates is
 * lost, and ranking by any column is gained.
 */
export function InstructorTable({ instructors }: { instructors: Instructor[] }) {
  // Defaults mirror the backend's own ordering (student.py sorts by
  // success_percentage descending) so the first paint matches the API.
  const [sortKey, setSortKey] = useState<SortKey>('success_percentage')
  const [direction, setDirection] = useState<Direction>('desc')
  const [expanded, setExpanded] = useState<string | null>(null)

  const sorted = useMemo(() => {
    const copy = [...instructors]
    copy.sort((a, b) => {
      const av = valueOf(a, sortKey)
      const bv = valueOf(b, sortKey)
      if (av === bv) return a.instructor_name.localeCompare(b.instructor_name)
      const result = av < bv ? -1 : 1
      return direction === 'asc' ? result : -result
    })
    return copy
  }, [instructors, sortKey, direction])

  function toggleSort(key: SortKey) {
    if (key === sortKey) {
      setDirection((d) => (d === 'asc' ? 'desc' : 'asc'))
    } else {
      setSortKey(key)
      // Names read naturally A-Z; percentages are most useful highest-first.
      setDirection(key === 'instructor_name' ? 'asc' : 'desc')
    }
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[32rem] border-collapse text-sm">
        <thead>
          <tr className="border-b border-ink-200 text-left">
            {COLUMNS.map((column) => {
              const active = column.key === sortKey
              return (
                <th
                  key={column.key}
                  scope="col"
                  title={column.title}
                  aria-sort={active ? (direction === 'asc' ? 'ascending' : 'descending') : 'none'}
                  className={`py-1.5 font-medium ${column.numeric ? 'text-right' : 'text-left'}`}
                >
                  <button
                    type="button"
                    onClick={() => toggleSort(column.key)}
                    className={`inline-flex items-center gap-1 rounded px-1 py-0.5 text-xs uppercase tracking-wide hover:bg-ink-100 ${
                      active ? 'text-ink-900' : 'text-ink-500'
                    }`}
                  >
                    {column.label}
                    <span aria-hidden className="text-[9px]">
                      {active ? (direction === 'asc' ? '▲' : '▼') : ''}
                    </span>
                  </button>
                </th>
              )
            })}
          </tr>
        </thead>
        <tbody>
          {sorted.map((instructor) => {
            const name = instructor.instructor_name
            const isOpen = expanded === name
            const cell = 'tnum py-1.5 text-right text-ink-600'
            return (
              <Fragment key={name}>
                <tr className={`border-b border-ink-100 ${isOpen ? 'bg-ink-50' : ''}`}>
                  <td className="py-1.5 pr-2">
                    <button
                      type="button"
                      onClick={() => setExpanded(isOpen ? null : name)}
                      aria-expanded={isOpen}
                      className="flex w-full items-center gap-1.5 rounded px-1 py-0.5 text-left hover:bg-ink-100"
                      title={isOpen ? 'Hide chart' : 'Show chart'}
                    >
                      <span aria-hidden className="text-[9px] text-ink-400">
                        {isOpen ? '▼' : '▶'}
                      </span>
                      <span className="truncate text-ink-800">{name}</span>
                    </button>
                  </td>
                  <td className={cell}>{instructor.metrics.A}</td>
                  <td className={cell}>{instructor.metrics.B}</td>
                  <td className={cell}>{instructor.metrics.C}</td>
                  <td className={cell}>{instructor.metrics.DNF}</td>
                  <td className="tnum py-1.5 text-right font-semibold text-ink-900">
                    {instructor.success_percentage}
                  </td>
                </tr>
                {isOpen ? (
                  <tr className="border-b border-ink-100 bg-ink-50">
                    <td colSpan={COLUMNS.length} className="px-1 pb-3">
                      <div className="max-w-[14rem]">
                        <BarChart bars={instructorDistribution(instructor.metrics)} caption={name} />
                      </div>
                    </td>
                  </tr>
                ) : null}
              </Fragment>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
