import { useState } from 'react'
import { AdminPanel } from './components/AdminPanel'
import { StudentReport } from './components/StudentReport'

type View = 'student' | 'admin'

const TABS: { id: View; label: string }[] = [
  { id: 'student', label: 'Student Report' },
  { id: 'admin', label: 'Administration' },
]

/**
 * Shell for the two user classes described in the ConOps.
 *
 * Switching is plain component state rather than a router. Spec 2.3.1 forbids
 * logins, so there is nothing to guard and no session to restore, and the app
 * has exactly two destinations - not enough to justify a routing dependency
 * under technical requirement 11. The cost is that neither view is
 * deep-linkable and a refresh returns to the student view.
 */
export default function App() {
  const [view, setView] = useState<View>('student')

  return (
    <div className="min-h-full">
      <header className="border-b border-ink-200 bg-white">
        <div className="mx-auto max-w-6xl px-4 py-4">
          <div className="flex flex-wrap items-baseline justify-between gap-x-6 gap-y-1">
            <div>
              <h1 className="text-xl font-semibold tracking-tight text-ink-900">MaxGPA</h1>
              <p className="text-sm text-ink-500">
                Grade distributions across the required courses of a University of Oregon major.
              </p>
            </div>
            <p className="text-xs text-ink-400">CS 422 Software Methodologies &middot; Project 1</p>
          </div>

          <nav className="mt-4 flex gap-1" aria-label="Views">
            {TABS.map((tab) => {
              const active = tab.id === view
              return (
                <button
                  key={tab.id}
                  type="button"
                  onClick={() => setView(tab.id)}
                  aria-current={active ? 'page' : undefined}
                  className={`rounded-t-md border-b-2 px-3 py-2 text-sm font-medium transition-colors ${
                    active
                      ? 'border-brand text-brand'
                      : 'border-transparent text-ink-500 hover:border-ink-300 hover:text-ink-700'
                  }`}
                >
                  {tab.label}
                </button>
              )
            })}
          </nav>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-4 py-6">
        {view === 'student' ? <StudentReport /> : <AdminPanel />}
      </main>

      <footer className="mx-auto max-w-6xl px-4 pb-10 text-xs text-ink-400">
        <p>
          DNF covers all non-passing grades (D-, D, D+, F and N). Percentages are of all students
          who received a grade, pooled across sections rather than averaged per section.
        </p>
      </footer>
    </div>
  )
}
