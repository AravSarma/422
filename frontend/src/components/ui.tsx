import type { ReactNode } from 'react'

/* Small shared primitives. Kept in one file because each is a handful of lines
   and they are always imported together. */

type Tone = 'info' | 'warning' | 'danger' | 'neutral'

const TONE_CLASSES: Record<Tone, string> = {
  info: 'border-sky-200 bg-sky-50 text-sky-900',
  warning: 'border-amber-200 bg-amber-50 text-amber-900',
  danger: 'border-red-200 bg-red-50 text-red-900',
  neutral: 'border-ink-200 bg-ink-50 text-ink-700',
}

export function Callout({
  tone = 'info',
  title,
  children,
}: {
  tone?: Tone
  title?: string
  children: ReactNode
}) {
  return (
    <div className={`rounded-md border px-3 py-2 text-sm ${TONE_CLASSES[tone]}`}>
      {title ? <p className="font-semibold">{title}</p> : null}
      <div className={title ? 'mt-0.5' : ''}>{children}</div>
    </div>
  )
}

/**
 * Empty states name the action that resolves them. The system ships with an
 * unpopulated database, so "no majors" is the expected first-run state rather
 * than an error, and the screen should say what to do about it.
 */
export function EmptyState({
  title,
  children,
}: {
  title: string
  children?: ReactNode
}) {
  return (
    <div className="rounded-lg border border-dashed border-ink-300 bg-white px-6 py-10 text-center">
      <p className="text-sm font-semibold text-ink-700">{title}</p>
      {children ? (
        <div className="mx-auto mt-1 max-w-prose text-sm text-ink-500">{children}</div>
      ) : null}
    </div>
  )
}

export function Button({
  children,
  onClick,
  variant = 'secondary',
  disabled,
  type = 'button',
}: {
  children: ReactNode
  onClick?: () => void
  variant?: 'primary' | 'secondary' | 'ghost'
  disabled?: boolean
  type?: 'button' | 'submit'
}) {
  const base =
    'inline-flex items-center justify-center rounded-md px-3 py-1.5 text-sm font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand'
  const variants = {
    primary: 'bg-brand text-white hover:bg-brand-light',
    secondary: 'border border-ink-300 bg-white text-ink-700 hover:bg-ink-50',
    ghost: 'text-ink-600 hover:bg-ink-100',
  }
  return (
    <button type={type} onClick={onClick} disabled={disabled} className={`${base} ${variants[variant]}`}>
      {children}
    </button>
  )
}

export function Spinner({ label }: { label: string }) {
  return (
    <p className="flex items-center gap-2 text-sm text-ink-500" role="status">
      <span
        aria-hidden
        className="size-3.5 animate-spin rounded-full border-2 border-ink-300 border-t-brand"
      />
      {label}
    </p>
  )
}

export function Card({ children, className = '' }: { children: ReactNode; className?: string }) {
  return (
    <section className={`rounded-lg border border-ink-200 bg-white ${className}`}>{children}</section>
  )
}

export function SectionHeading({ children, hint }: { children: ReactNode; hint?: string }) {
  return (
    <div className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
      <h2 className="text-base font-semibold text-ink-900">{children}</h2>
      {hint ? <p className="text-xs text-ink-500">{hint}</p> : null}
    </div>
  )
}
