import type { GlobalMetrics, InstructorMetrics, ReportCourse } from '../types'

/** One bar of a grade-distribution chart. */
export interface GradeBar {
  label: string
  /** Percentage of students, 0-100. */
  value: number
  /** A CSS colour; the grade colours are declared in index.css. */
  color: string
}

const COLOR = {
  A: 'var(--color-grade-a)',
  B: 'var(--color-grade-b)',
  C: 'var(--color-grade-c)',
  DNF: 'var(--color-grade-dnf)',
} as const

const round1 = (n: number) => Math.round(n * 10) / 10

/**
 * Course-level bars for the "All Instructors" chart.
 *
 * Spec 3.4: DNF is every non-passing grade (D-, D, D+, F and N). The backend
 * reports D, F and N (DNF) separately at course level, so they are summed here.
 */
export function courseDistribution(m: GlobalMetrics): GradeBar[] {
  return [
    { label: 'A', value: m.A, color: COLOR.A },
    { label: 'B', value: m.B, color: COLOR.B },
    { label: 'C', value: m.C, color: COLOR.C },
    { label: 'DNF', value: round1(m.D + m.F + m.DNF), color: COLOR.DNF },
  ]
}

/**
 * Instructor-level bars. The backend exposes the instructor's DNF already
 * defined per spec 3.4 (see student.py), so it is used as given.
 */
export function instructorDistribution(m: InstructorMetrics): GradeBar[] {
  return [
    { label: 'A', value: m.A, color: COLOR.A },
    { label: 'B', value: m.B, color: COLOR.B },
    { label: 'C', value: m.C, color: COLOR.C },
    { label: 'DNF', value: m.DNF, color: COLOR.DNF },
  ]
}

/** Spec 2.1.2 notation. AY16 is Fall 2016 through Summer 2017, stored as "2016". */
export function academicYearLabel(year: string): string {
  return `AY${year.slice(-2)}`
}

/** Spec 2.2.2: TERM is 1 for Fall, 2 for Winter, 3 for Spring. */
export function termName(term: number): string {
  switch (term) {
    case 1:
      return 'Fall'
    case 2:
      return 'Winter'
    case 3:
      return 'Spring'
    default:
      return `Term ${term}`
  }
}

export interface YearTermGroup {
  key: string
  year: number | null
  term: number | null
  courses: ReportCourse[]
}

/**
 * Partitions courses into Year/Term groups, preserving the backend's order.
 * If any course lacks year or term (an older server), everything falls into one
 * unlabelled group instead of rendering empty headings.
 */
export function groupByYearTerm(courses: ReportCourse[]): YearTermGroup[] {
  if (courses.some((c) => c.year == null || c.term == null)) {
    return [{ key: 'all', year: null, term: null, courses }]
  }
  const groups: YearTermGroup[] = []
  const byKey = new Map<string, YearTermGroup>()
  for (const course of courses) {
    const key = `${course.year}-${course.term}`
    let group = byKey.get(key)
    if (!group) {
      group = { key, year: course.year ?? null, term: course.term ?? null, courses: [] }
      byKey.set(key, group)
      groups.push(group)
    }
    group.courses.push(course)
  }
  return groups
}
