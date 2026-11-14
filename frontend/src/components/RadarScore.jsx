const AXES = [
  ['water_fit', 'Water'],
  ['season_fit', 'Season'],
  ['heat_drought_resilience', 'Heat'],
  ['soil_health', 'Soil'],
  ['pest_break', 'Pests'],
  ['erosion_protection', 'Erosion'],
  ['market_preference_fit', 'Market'],
  ['forage_value', 'Forage'],
]

const W = 264
const H = 248
const CX = W / 2
const CY = H / 2
const R = 76

const angleFor = (index) => -Math.PI / 2 + (index * 2 * Math.PI) / AXES.length

function point(value, index, radius = R) {
  const angle = angleFor(index)
  return [CX + Math.cos(angle) * radius * value, CY + Math.sin(angle) * radius * value]
}

export default function RadarScore({ criteria = {}, tone = 'strong' }) {
  const ring = (pct) => AXES.map((_, i) => point(pct, i).join(',')).join(' ')
  const values = AXES.map(([key]) => Math.max(6, Math.min(100, Number(criteria[key] ?? 0))))
  const shape = values.map((value, i) => point(value / 100, i).join(',')).join(' ')

  return (
    <svg
      className={`radar radar--${tone}`}
      viewBox={`0 0 ${W} ${H}`}
      role="img"
      aria-label="Score profile across water, season, heat, soil, pests, erosion, market and forage"
    >
      {[0.33, 0.66, 1].map((pct) => (
        <polygon
          key={pct}
          points={ring(pct)}
          fill="none"
          stroke="var(--line)"
          strokeWidth={pct === 1 ? 1.1 : 0.8}
        />
      ))}
      {AXES.map((_, i) => {
        const [x, y] = point(1, i)
        return <line key={i} x1={CX} y1={CY} x2={x} y2={y} stroke="var(--line)" strokeWidth="0.8" />
      })}
      <polygon points={shape} fill="currentColor" fillOpacity="0.16" stroke="currentColor" strokeWidth="2" />
      {values.map((value, i) => {
        const [x, y] = point(value / 100, i)
        return <circle key={i} cx={x} cy={y} r="2.6" fill="currentColor" />
      })}
      {AXES.map(([, label], i) => {
        const [x, y] = point(1, i, R + 21)
        const anchor = x > CX + 6 ? 'start' : x < CX - 6 ? 'end' : 'middle'
        return (
          <text
            key={label}
            x={x}
            y={y + 3}
            textAnchor={anchor}
            fontSize="8.4"
            fontWeight="600"
            fill="var(--ink-3)"
          >
            {label}
          </text>
        )
      })}
    </svg>
  )
}
