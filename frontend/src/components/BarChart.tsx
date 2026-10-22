import type { GradeBar } from '../lib/grades'

interface BarChartProps {
  bars: GradeBar[]
  /** Printed under the axis, e.g. "All Instructors" or an instructor's name. */
  caption: string
  /** Rendered above the plot in smaller type. */
  note?: string
}

/*
 * Geometry. A fixed viewBox scaled by CSS keeps every chart on the page
 * identical in proportion regardless of the column it lands in, which matters
 * because these are read comparatively.
 */
const VIEW_W = 180
const VIEW_H = 132
const PLOT_LEFT = 32
const PLOT_RIGHT = 174
const PLOT_TOP = 12
const PLOT_BOTTOM = 92
const PLOT_H = PLOT_BOTTOM - PLOT_TOP

const GRIDLINES = [0, 50, 100] as const

/** Percentage to y pixel. The axis is fixed at 0-100 so charts stay comparable. */
const yFor = (value: number) => PLOT_BOTTOM - (Math.max(0, Math.min(100, value)) / 100) * PLOT_H

/**
 * A single grade-distribution chart: four bars on a fixed 0-100% axis.
 *
 * Written as inline SVG rather than pulled from a charting library. The shape
 * required by spec 3.6 is four bars against a fixed scale with three
 * gridlines, which is about sixty lines of SVG; a library would add a
 * dependency to justify under technical requirement 11 and bring a transitive
 * tree far larger than the thing it draws.
 */
export function BarChart({ bars, caption, note }: BarChartProps) {
  const slot = (PLOT_RIGHT - PLOT_LEFT) / bars.length
  const barWidth = Math.min(22, slot * 0.52)

  const summary = bars.map((b) => `${b.label} ${b.value}%`).join(', ')

  return (
    <figure className="m-0">
      {note ? (
        <figcaption className="mb-1 text-[11px] leading-tight text-ink-500">{note}</figcaption>
      ) : null}
      <svg
        viewBox={`0 0 ${VIEW_W} ${VIEW_H}`}
        className="w-full"
        role="img"
        aria-label={`${caption}: ${summary}`}
      >
        {GRIDLINES.map((pct) => {
          const y = yFor(pct)
          return (
            <g key={pct}>
              <line
                x1={PLOT_LEFT}
                x2={PLOT_RIGHT}
                y1={y}
                y2={y}
                stroke="var(--color-ink-200)"
                strokeWidth={1}
              />
              <text
                x={PLOT_LEFT - 6}
                y={y + 3.5}
                textAnchor="end"
                className="tnum"
                fontSize={9}
                fill="var(--color-ink-500)"
              >
                {pct}%
              </text>
            </g>
          )
        })}

        {bars.map((bar, i) => {
          const x = PLOT_LEFT + slot * i + (slot - barWidth) / 2
          const y = yFor(bar.value)
          const height = PLOT_BOTTOM - y
          return (
            <g key={bar.label}>
              {/* Zero-height rects are invisible; a 1px stub shows the bar exists
                  and is genuinely zero rather than missing. */}
              <rect
                x={x}
                y={height < 1 ? PLOT_BOTTOM - 1 : y}
                width={barWidth}
                height={height < 1 ? 1 : height}
                fill={bar.color}
                rx={1}
              />
              <text
                x={x + barWidth / 2}
                y={PLOT_BOTTOM + 12}
                textAnchor="middle"
                fontSize={10}
                fill="var(--color-ink-600)"
              >
                {bar.label}
              </text>
              <text
                x={x + barWidth / 2}
                y={PLOT_BOTTOM + 23}
                textAnchor="middle"
                className="tnum"
                fontSize={9}
                fill="var(--color-ink-400)"
              >
                {bar.value}
              </text>
            </g>
          )
        })}

        <line
          x1={PLOT_LEFT}
          x2={PLOT_RIGHT}
          y1={PLOT_BOTTOM}
          y2={PLOT_BOTTOM}
          stroke="var(--color-ink-300)"
          strokeWidth={1}
        />
      </svg>
      <figcaption className="mt-1 truncate text-center text-xs font-medium text-ink-700" title={caption}>
        {caption}
      </figcaption>
    </figure>
  )
}
