import {
  CalendarRange,
  CloudRain,
  Database,
  Droplets,
  Info,
  MapPin,
  ThermometerSun,
  TrendingDown,
} from 'lucide-react'
import Term from './Term'
import { MONTHS, RainfallChart, TemperatureChart, WetnessChart } from './Charts'

const doyLabel = (doy) => {
  if (typeof doy !== 'number') return '—'
  const date = new Date(2023, 0, 1)
  date.setDate(doy)
  return `~${date.toLocaleDateString('en-GB', { month: 'short', day: 'numeric' })}`
}

export default function ClimateView({ climate }) {
  const {
    location,
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
  const bareMonths = (bare_field_window.months || []).map((m) => MONTHS[m - 1]).join(', ')
  const flags = data_quality.flags?.length ? data_quality.flags.join(', ') : 'None reported'

  return (
    <div className="stack">
      <div className="row row--wrap" style={{ alignItems: 'flex-end' }}>
        <div>
          <p className="eyebrow">NASA POWER climate record</p>
          <h2 style={{ marginTop: '0.15rem' }}>{location?.label || 'Selected field'}</h2>
        </div>
        <span className="spacer" />
        <span className="chip chip--green">
          <MapPin className="icon" aria-hidden="true" />
          {location?.lat}, {location?.lon}
        </span>
        <span className="chip">{dataset.period || '1991–2025'}</span>
        <span className="chip">Coarse grid · not field-level</span>
      </div>

      <div className="stat-grid">
        <div className="stat">
          <div className="stat__label">
            <CalendarRange className="icon" aria-hidden="true" />
            <Term k="season_length">Season length</Term>
          </div>
          <div className="stat__value">
            {season.length_days_median}
            <span className="stat__unit">days</span>
          </div>
          <div className="stat__foot">P20 {season.length_days_p20} days</div>
        </div>
        <div className="stat">
          <div className="stat__label">
            <CloudRain className="icon" aria-hidden="true" />
            <Term k="percentiles">Season rainfall</Term>
          </div>
          <div className="stat__value">
            {season_rain_total.median_mm}
            <span className="stat__unit">mm</span>
          </div>
          <div className="stat__foot">
            P20 {season_rain_total.p20_mm} mm · CV {season_rain_total.cv}
          </div>
        </div>
        <div className="stat">
          <div className="stat__label">
            <Term k="dry_spell">Dry spells</Term>
          </div>
          <div className="stat__value">
            {dry_spells.avg_per_season}
            <span className="stat__unit">/ season</span>
          </div>
          <div className="stat__foot">Longest median {dry_spells.longest_median_days} days</div>
        </div>
        <div className="stat">
          <div className="stat__label">
            <ThermometerSun className="icon" aria-hidden="true" />
            <Term k="heat_stress">Heat-stress days</Term>
          </div>
          <div className="stat__value">
            {heat_stress_days.median}
            <span className="stat__unit">days</span>
          </div>
          <div className="stat__foot">Above {threshold} °C</div>
        </div>
      </div>

      <div className="grid-2 grid-2--even">
        <section className="card">
          <div className="card__head">
            <span className="card__head-icon" aria-hidden="true">
              <CloudRain className="icon" />
            </span>
            <div>
              <h2 className="card__title">Monthly rainfall</h2>
              <p className="card__subtitle">
                <Term k="percentiles">P20, P50 and P80</Term> across the recorded years.
              </p>
            </div>
          </div>
          <div className="card__body">
            <div className="chart-box">
              <RainfallChart monthly={monthly} />
            </div>
            <div className="chart-legend">
              <span>
                <i style={{ background: '#d5dfd0' }} /> P20 · drier than usual
              </span>
              <span>
                <i style={{ background: '#8aa88f' }} /> P50 · typical
              </span>
              <span>
                <i style={{ background: '#2c5c40' }} /> P80 · wetter than usual
              </span>
            </div>
          </div>
        </section>

        <section className="card">
          <div className="card__head">
            <span className="card__head-icon" aria-hidden="true">
              <ThermometerSun className="icon" />
            </span>
            <div>
              <h2 className="card__title">Temperature</h2>
              <p className="card__subtitle">Monthly mean daily maximum, with the heat threshold.</p>
            </div>
          </div>
          <div className="card__body">
            <div className="chart-box">
              <TemperatureChart monthly={monthly} threshold={threshold} />
            </div>
            <p className="hint" style={{ marginTop: '0.5rem' }}>
              Heat-stress days count days above {threshold} °C inside each crop window. The
              threshold is configurable per crop.
            </p>
          </div>
        </section>
      </div>

      <div className="grid-2 grid-2--even">
        <section className="card">
          <div className="card__head">
            <span className="card__head-icon" aria-hidden="true">
              <Droplets className="icon" />
            </span>
            <div>
              <h2 className="card__title">Regional root-zone wetness indicator</h2>
              <p className="card__subtitle">GWETROOT monthly mean from NASA POWER.</p>
            </div>
          </div>
          <div className="card__body">
            <div className="chart-box">
              <WetnessChart monthly={monthly} />
            </div>
            <div className="callout" style={{ marginTop: '0.6rem' }}>
              <Info className="icon" aria-hidden="true" />
              <div>
                This is a <Term k="regional_wetness">regional wetness indicator</Term>, not a
                measurement of water available in the farmer’s field. It is kept separate from the
                soil information you enter.
              </div>
            </div>
          </div>
        </section>

        <section className="card">
          <div className="card__head">
            <span className="card__head-icon" aria-hidden="true">
              <TrendingDown className="icon" />
            </span>
            <div>
              <h2 className="card__title">Season, trend &amp; bare fields</h2>
              <p className="card__subtitle">Planning indicators, not forecasts.</p>
            </div>
          </div>
          <div className="card__body">
            <ul className="meta-list">
              <li>
                <span className="k">
                  <Term k="onset">Onset</Term> median
                </span>
                <span className="v">
                  Day {season.onset_doy_median} ({doyLabel(season.onset_doy_median)})
                </span>
              </li>
              <li>
                <span className="k">
                  <Term k="cessation">Cessation</Term> median
                </span>
                <span className="v">
                  Day {season.cessation_doy_median} ({doyLabel(season.cessation_doy_median)})
                </span>
              </li>
              <li>
                <span className="k">Season rule</span>
                <span className="v">
                  {season.method} · {season.years_ok} years OK, {season.years_flagged} flagged
                </span>
              </li>
              <li>
                <span className="k">Rain trend</span>
                <span className="v">
                  {trend.season_rain_mm_per_decade} mm / decade
                </span>
              </li>
              <li>
                <span className="k">
                  <Term k="bare_field">Bare-field window</Term>
                </span>
                <span className="v">
                  {bareMonths || '—'}{' '}
                  <span className="chip" style={{ marginLeft: '0.3rem' }}>
                    {bare_field_window.basis || 'proxy'}
                  </span>
                </span>
              </li>
            </ul>
            <p className="hint" style={{ marginTop: '0.6rem' }}>
              {trend.note || 'Indicative only, not a forecast.'} The bare-field window is estimated
              from climate proxies, not satellite vegetation imagery.
            </p>
          </div>
        </section>
      </div>

      <section className="card">
        <div className="card__head">
          <span className="card__head-icon" aria-hidden="true">
            <Database className="icon" />
          </span>
          <div>
            <h2 className="card__title">Data sources &amp; quality</h2>
            <p className="card__subtitle">What is NASA data, and what it can and cannot tell you.</p>
          </div>
        </div>
        <div className="card__body">
          <ul className="meta-list">
            <li>
              <span className="k">Dataset</span>
              <span className="v">{dataset.name || 'NASA POWER daily'}</span>
            </li>
            <li>
              <span className="k">Community</span>
              <span className="v">{dataset.community || 'AG'}</span>
            </li>
            <li>
              <span className="k">Time standard</span>
              <span className="v">{dataset.time_standard || 'UTC'}</span>
            </li>
            <li>
              <span className="k">Resolution</span>
              <span className="v">{dataset.resolution_note || 'coarse global grid, not field-level'}</span>
            </li>
            <li>
              <span className="k">Period</span>
              <span className="v">{dataset.period || '1991–2025'} (complete years only)</span>
            </li>
            <li>
              <span className="k">Missing data</span>
              <span className="v">{data_quality.missing_pct}%</span>
            </li>
            <li>
              <span className="k">Quality flags</span>
              <span className="v">{flags}</span>
            </li>
            <li>
              <span className="k">Served from cache</span>
              <span className="v">{data_quality.from_cache ? 'Yes' : 'No'}</span>
            </li>
          </ul>
          <div className="callout" style={{ marginTop: '0.8rem' }}>
            <Info className="icon" aria-hidden="true" />
            <div>
              NASA POWER describes the climate of a grid cell, not your field. Use these indicators
              to compare strategies and discuss them with an extension officer.
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}
