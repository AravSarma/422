import type { ReportCourse } from '../types'
import { courseDistribution } from '../lib/grades'
import { BarChart } from './BarChart'
import { InstructorTable } from './InstructorTable'
import { Callout } from './ui'

/**
 * One required course from the degree plan.
 *
 * Renders in one of two states. A course with no usable grade history shows
 * the backend's own spec 3.2 sentence instead of an empty axis, because an
 * all-zero chart would read as "everyone failed" rather than "the university
 * redacted this".
 */
export function CourseCard({ course }: { course: ReportCourse }) {
  const heading = `${course.subject} ${course.number}`

  return (
    <article className="border-t border-ink-200 px-4 py-4 first:border-t-0">
      <header className="mb-3">
        <h4 className="text-sm font-semibold text-ink-900">
          {heading}
          <span className="font-normal text-ink-600"> &ndash; {course.title}</span>
        </h4>
      </header>

      {!course.has_data ? (
        <Callout tone="warning">
          {course.alert_message ||
            `Class ${heading} is required for the major but no grade data are available.`}
        </Callout>
      ) : (
        <div className="grid gap-5 lg:grid-cols-[13rem_1fr]">
          <div>
            <BarChart bars={courseDistribution(course.global_metrics)} caption="All Instructors" />
          </div>

          <div className="min-w-0">
            {course.instructors.length > 0 ? (
              <>
                <InstructorTable instructors={course.instructors} />
                {/*
                  Surfaced per course rather than once per page: the two DNF
                  figures on this row are computed from different inputs, and a
                  reader comparing them deserves to be told where they differ.
                */}
                <p className="mt-2 text-[11px] leading-snug text-ink-400">
                  All Instructors DNF counts D, F and N per spec 3.4. Per-instructor DNF counts N
                  only, because the API does not expose D and F for an instructor.
                </p>
              </>
            ) : (
              <p className="text-sm text-ink-500">
                Grade data exist for this course, but no instructor is named on any record.
              </p>
            )}
          </div>
        </div>
      )}
    </article>
  )
}
