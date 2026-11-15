import { CloudRain, CloudSun, Droplets, ThermometerSun, Wind } from 'lucide-react'
import { MONTHS, RainfallChart, TemperatureChart } from './Charts'

export default function ClimatePanel({ climate, status, location: field }) {
  if (status === 'loading' || !climate) {
    return (
      <section className="climate" id="climate">
        <div className="climate__head">
          <div>
            <p className="eyebrow">NASA POWER</p>
            <h2>Climate here</h2>
          </div>
        </div>
        <div className="climate__body">
          <div className="inline-loading">
            <span className="spinner" style={{ width: 16, height: 16, borderWidth: 2 }} />
            Loading climate…
          </div>
        </div>
      </section>
    )
  }

  if (status === 'error') {
    return (
      <section className="climate" id="climate">
        <div className="climate__head">
          <div>
            <p className="eyebrow">NASA POWER</p>
            <h2>Climate here</h2>
          </div>
        </div>
        <div className="climate__body">
          <p className="hint">Climate indicators could not load. The rotation scores are still shown.</p>
        </div>
      </section>
    )
  }

  const {
    datasets = [],
    monthly = [],
    season = {},
    season_rain_total = {},
    dry_spells = {},
    heat_stress_days = {},
    trend = {},
    bare_field_window = {},
    data_quality = {},
  } = climate
  const dataset = datasets[0] || {}
  const threshold = heat_stress_days.threshold_c ?? 35

  const rain = Number(season_rain_total.median_mm) || 0
  const seasonLen = Number(season.length_days_median) || 0
  const heat = Number(heat_stress_days.median) || 0
  const dry = Number(dry_spells.avg_per_season) || 0
  const verdicts = [
    {
      icon: CloudRain,
      label: rain >= 700 ? 'Plenty of rain' : rain >= 400 ? 'Some rain' : 'Little rain',
      tone: rain >= 400 ? 'good' : rain >= 250 ? 'warn' : 'bad',
    },
    {
      icon: CloudSun,
      label: seasonLen >= 150 ? 'Long season' : seasonLen >= 110 ? 'Normal season' : 'Short season',
      tone: seasonLen >= 110 ? 'good' : 'warn',
    },
    {
      icon: ThermometerSun,
      label: heat >= 40 ? 'Very hot days' : heat >= 15 ? 'Some hot days' : 'Cool enough',
      tone: heat >= 40 ? 'bad' : heat >= 15 ? 'warn' : 'good',
    },
    {
      icon: Wind,
      label: dry >= 3 ? 'Dry breaks' : dry >= 2 ? 'Some dry breaks' : 'Steady rain',
      tone: dry >= 3 ? 'warn' : 'good',
    },
  ]

  return (
    <section className="climate" id="climate">
      <div className="climate__head">
        <div>
          <p className="eyebrow">NASA POWER · {dataset.period || '1991–2023'}</p>
          <h2>Climate here</h2>
          <p>
            {field?.label || field?.name || 'Selected field'} · {Number(field?.lat).toFixed(2)},{' '}
            {Number(field?.lon).toFixed(2)}
          </p>
        </div>
        <span className="tag tag--mono">Grid cell</span>
      </div>

      <div className="climate__body">
        <div className="climate-verdict" aria-label="Season summary">
          {verdicts.map(({ icon: Icon, label, tone }) => (
            <span className="climate-verdict__chip" data-tone={tone} key={label}>
              <Icon className="icon" aria-hidden="true" />
              {label}
            </span>
          ))}
        </div>

        <div className="climate__stats">
          <div className="climate-stat">
            <span className="climate-stat__icon"><CloudSun className="icon" aria-hidden="true" /></span>
            <div className="l">Season</div>
            <div className="v">
              {season.length_days_median ?? '—'}
              <small>d</small>
            </div>
            <div className="f">P20 {season.length_days_p20 ?? '—'} d</div>
          </div>
          <div className="climate-stat">
            <span className="climate-stat__icon"><CloudRain className="icon" aria-hidden="true" /></span>
            <div className="l">Season rain</div>
            <div className="v">
              {season_rain_total.median_mm ?? '—'}
              <small>mm</small>
            </div>
            <div className="f">P20 {season_rain_total.p20_mm ?? '—'} mm</div>
          </div>
          <div className="climate-stat">
            <span className="climate-stat__icon"><Wind className="icon" aria-hidden="true" /></span>
            <div className="l">Dry spells</div>
            <div className="v">
              {dry_spells.avg_per_season ?? '—'}
              <small>/ season</small>
            </div>
            <div className="f">Longest {dry_spells.longest_median_days ?? '—'} d</div>
          </div>
          <div className="climate-stat">
            <span className="climate-stat__icon"><ThermometerSun className="icon" aria-hidden="true" /></span>
            <div className="l">Heat days</div>
            <div className="v">
              {heat_stress_days.median ?? '—'}
              <small>d</small>
            </div>
            <div className="f">Above {threshold}°C</div>
          </div>
        </div>

        <div className="monthstrip" aria-label="Monthly rainfall">
          {monthly.map((m) => {
            const max = Math.max(1, ...monthly.map((item) => Number(item.rain_p50) || 0))
            const pct = Math.max(5, Math.round(((Number(m.rain_p50) || 0) / max) * 100))
            const wet = (Number(m.rain_p50) || 0) >= 60
            return (
              <div
                className="monthstrip__col"
                key={m.month}
                title={`${MONTHS[m.month - 1]} · ${m.rain_p50} mm`}
              >
                <span className="monthstrip__bar" style={{ height: `${pct}%` }} data-wet={wet} />
                <span className="monthstrip__m">{MONTHS[m.month - 1]}</span>
              </div>
            )
          })}
        </div>

        <div className="monthstrip-legend">
          <span>
            <i data-wet="true" /> Rainy
          </span>
          <span>
            <i /> Dry
          </span>
        </div>

        <div className="climate__charts">
          <div className="chart-card">
            <h3>
              <CloudRain style={{ width: 13, height: 13, verticalAlign: -2, marginRight: 4 }} aria-hidden="true" />
              Rainfall
            </h3>
            <RainfallChart monthly={monthly} />
            <div className="chart-legend">
              <span>
                <i style={{ background: '#dbeafe' }} /> Dry
              </span>
              <span>
                <i style={{ background: '#93c5fd' }} /> Typical
              </span>
              <span>
                <i style={{ background: '#2f80ed' }} /> Wet
              </span>
            </div>
          </div>

          <div className="chart-card">
            <h3>
              <ThermometerSun style={{ width: 13, height: 13, verticalAlign: -2, marginRight: 4 }} aria-hidden="true" />
              Temperature
            </h3>
            <TemperatureChart monthly={monthly} threshold={threshold} />
            <div className="chart-legend">
              <span>
                <i style={{ background: '#f59e0b' }} /> Max temp
              </span>
              <span>
                <i style={{ background: '#ef4444' }} /> {threshold}°C threshold
              </span>
            </div>
          </div>
        </div>

        <details className="climate__more">
          <summary>
            <Droplets style={{ width: 13, height: 13, verticalAlign: -2, marginRight: 4 }} aria-hidden="true" />
            Season timing &amp; data
          </summary>
          <ul className="meta-list" style={{ marginTop: '0.5rem' }}>
            <li>
              <span className="k">Onset</span>
              <span className="v">Day {season.onset_doy_median ?? '—'}</span>
            </li>
            <li>
              <span className="k">Cessation</span>
              <span className="v">Day {season.cessation_doy_median ?? '—'}</span>
            </li>
            <li>
              <span className="k">Rain trend</span>
              <span className="v">{trend.season_rain_mm_per_decade ?? '—'} mm / decade</span>
            </li>
            <li>
              <span className="k">Bare-field</span>
              <span className="v">
                {(bare_field_window.months || []).join(', ') || '—'} · {bare_field_window.basis || 'proxy'}
              </span>
            </li>
            <li>
              <span className="k">Missing</span>
              <span className="v">{data_quality.missing_pct ?? 0}%</span>
            </li>
          </ul>
          <p className="hint" style={{ marginTop: '0.45rem' }}>
            Grid-cell climate, not field measurements. Not a forecast.
          </p>
        </details>
      </div>
    </section>
  )
}
