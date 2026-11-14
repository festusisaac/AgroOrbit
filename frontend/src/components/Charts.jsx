import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

export const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

const RAIN_COLORS = { p20: '#cfe4d5', p50: '#7fb394', p80: '#2c6647' }
const TEMP_COLOR = '#a9762f'
const WET_COLOR = '#4e8f74'
const GRID = '#e8ece6'
const AXIS = '#e2e7df'

function ChartTooltip({ active, payload, label, unit = '' }) {
  if (!active || !payload || payload.length === 0) return null
  const title = typeof label === 'number' ? MONTHS[label - 1] : label
  return (
    <div className="chart-tooltip">
      <div className="chart-tooltip__title">{title}</div>
      {payload.map((entry) => (
        <div className="chart-tooltip__row" key={entry.dataKey || entry.name}>
          <i style={{ background: entry.color || entry.fill || entry.stroke }} />
          <span>{entry.name}</span>
          <b>
            {entry.value}
            {unit}
          </b>
        </div>
      ))}
    </div>
  )
}

export function RainfallChart({ monthly }) {
  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={monthly} margin={{ top: 6, right: 6, left: -18, bottom: 0 }} barGap={2}>
        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={GRID} />
        <XAxis dataKey="month" tickFormatter={(m) => MONTHS[m - 1]} tickLine={false} axisLine={{ stroke: AXIS }} />
        <YAxis tickLine={false} axisLine={false} width={46} />
        <Tooltip content={<ChartTooltip unit=" mm" />} cursor={{ fill: 'rgba(44, 102, 71, 0.06)' }} />
        <Bar dataKey="rain_p20" name="P20 · dry" fill={RAIN_COLORS.p20} radius={[2, 2, 0, 0]} isAnimationActive={false} />
        <Bar dataKey="rain_p50" name="P50 · typical" fill={RAIN_COLORS.p50} radius={[2, 2, 0, 0]} isAnimationActive={false} />
        <Bar dataKey="rain_p80" name="P80 · wet" fill={RAIN_COLORS.p80} radius={[2, 2, 0, 0]} isAnimationActive={false} />
      </BarChart>
    </ResponsiveContainer>
  )
}

export function TemperatureChart({ monthly, threshold = 35 }) {
  return (
    <ResponsiveContainer width="100%" height={260}>
      <LineChart data={monthly} margin={{ top: 8, right: 8, left: -18, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={GRID} />
        <XAxis dataKey="month" tickFormatter={(m) => MONTHS[m - 1]} tickLine={false} axisLine={{ stroke: AXIS }} />
        <YAxis tickLine={false} axisLine={false} width={46} unit="°" />
        <Tooltip content={<ChartTooltip unit=" °C" />} />
        <ReferenceLine
          y={threshold}
          stroke="#b4472f"
          strokeDasharray="4 4"
          label={{ value: `Heat threshold ${threshold}°C`, position: 'insideTopLeft', fill: '#9f2d2d', fontSize: 10 }}
        />
        <Line
          type="monotone"
          dataKey="tmax"
          name="Max temperature"
          stroke={TEMP_COLOR}
          strokeWidth={2}
          dot={{ r: 2.5, fill: TEMP_COLOR, strokeWidth: 0 }}
          activeDot={{ r: 4 }}
          isAnimationActive={false}
        />
      </LineChart>
    </ResponsiveContainer>
  )
}

export function WetnessChart({ monthly }) {
  return (
    <ResponsiveContainer width="100%" height={260}>
      <AreaChart data={monthly} margin={{ top: 8, right: 8, left: -18, bottom: 0 }}>
        <defs>
          <linearGradient id="wetnessFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={WET_COLOR} stopOpacity={0.28} />
            <stop offset="100%" stopColor={WET_COLOR} stopOpacity={0.02} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={GRID} />
        <XAxis dataKey="month" tickFormatter={(m) => MONTHS[m - 1]} tickLine={false} axisLine={{ stroke: AXIS }} />
        <YAxis domain={[0, 1]} ticks={[0, 0.5, 1]} tickFormatter={(v) => v.toFixed(1)} tickLine={false} axisLine={false} width={46} />
        <Tooltip content={<ChartTooltip />} />
        <Area
          type="monotone"
          dataKey="regional_root_zone_wetness"
          name="Root-zone wetness"
          stroke={WET_COLOR}
          strokeWidth={2}
          fill="url(#wetnessFill)"
          dot={{ r: 2.5, fill: WET_COLOR, strokeWidth: 0 }}
          isAnimationActive={false}
        />
      </AreaChart>
    </ResponsiveContainer>
  )
}
