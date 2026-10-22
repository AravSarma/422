import type { ReportResponse } from './types'

/**
 * A hand-built report used only in development.
 *
 * The system ships with an empty grade_history, so without this there is
 * nothing to render against while building, and no way to confirm the charts,
 * sorting or the spec 3.2 redaction path behave. It is reachable only when
 * import.meta.env.DEV is true and is never bundled into a production build.
 *
 * Shaped to exercise the awkward cases, not the happy one: a course with a
 * single instructor, one with many, one that is fully redacted, and one whose
 * instructor name is missing upstream.
 */
export const SAMPLE_REPORT: ReportResponse = {
  report_title: 'Grades Assigned Across UO Classes for Computer Science (sample data)',
  time_frame: 'AY15-AY25',
  courses: [
    {
      year: 1,
      term: 1,
      subject: 'CS',
      number: '122',
      title: 'Introduction to Programming and Problem Solving',
      has_data: true,
      alert_message: '',
      global_metrics: { A: 48.2, B: 27.4, C: 12.1, D: 5.3, F: 4.6, DNF: 2.4 },
      instructors: [
        {
          instructor_name: 'Dana Whitfield',
          success_percentage: 88.1,
          metrics: { A: 61.3, B: 26.8, C: 7.4, DNF: 1.1 },
        },
        {
          instructor_name: 'Marcus Ibarra',
          success_percentage: 74.9,
          metrics: { A: 44.1, B: 30.8, C: 14.2, DNF: 3.0 },
        },
        {
          instructor_name: 'Priya Raghavan',
          success_percentage: 62.5,
          metrics: { A: 33.0, B: 29.5, C: 19.8, DNF: 5.2 },
        },
      ],
    },
    {
      year: 1,
      term: 1,
      subject: 'MATH',
      number: '112Z',
      title: 'Precalculus II: Trigonometry',
      has_data: true,
      alert_message: '',
      global_metrics: { A: 31.0, B: 24.8, C: 21.3, D: 11.7, F: 8.1, DNF: 3.1 },
      instructors: [
        {
          instructor_name: 'Alan Rhee',
          success_percentage: 58.4,
          metrics: { A: 32.1, B: 26.3, C: 22.0, DNF: 3.4 },
        },
      ],
    },
    {
      year: 1,
      term: 2,
      subject: 'CS',
      number: '210',
      title: 'Computer Science I',
      has_data: false,
      alert_message:
        'Class CS 210 is required for the major but no grade data are available.',
      global_metrics: { A: 0, B: 0, C: 0, D: 0, F: 0, DNF: 0 },
      instructors: [],
    },
    {
      year: 1,
      term: 2,
      subject: 'WR',
      number: '122Z',
      title: 'Composition II',
      has_data: true,
      alert_message: '',
      global_metrics: { A: 55.6, B: 30.2, C: 9.4, D: 2.1, F: 1.4, DNF: 1.3 },
      instructors: [
        {
          instructor_name: 'Unknown Instructor',
          success_percentage: 85.8,
          metrics: { A: 55.6, B: 30.2, C: 9.4, DNF: 1.3 },
        },
      ],
    },
    {
      year: 2,
      term: 1,
      subject: 'CS',
      number: '212',
      title: 'Computer Science III',
      has_data: true,
      alert_message: '',
      global_metrics: { A: 40.1, B: 29.9, C: 17.2, D: 6.4, F: 3.9, DNF: 2.5 },
      instructors: [
        {
          instructor_name: 'Dana Whitfield',
          success_percentage: 81.2,
          metrics: { A: 52.0, B: 29.2, C: 12.6, DNF: 1.8 },
        },
        {
          instructor_name: 'Soren Lindqvist',
          success_percentage: 55.3,
          metrics: { A: 26.4, B: 28.9, C: 24.7, DNF: 6.1 },
        },
      ],
    },
  ],
}
