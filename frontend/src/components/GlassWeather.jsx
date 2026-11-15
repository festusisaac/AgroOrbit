import { CloudRain, Droplets, ThermometerSun, Wind } from 'lucide-react'

const round = (n) => (Number.isFinite(Number(n)) ? Math.round(Number(n)) : null)

function Skeleton() {
  return (
    <div className="glass__grid" aria-hidden="true">
      {[0, 1, 2, 3].map((i) => (
        <div className="glass__tile glass__tile--skeleton" key={i}>
          <span className="skeleton skeleton--icon" />
          <span className="skeleton skeleton--line" />
        </div>
      ))}
    </div>
  )
}

export default function GlassWeather({ weather, status, location }) {
  const monthly = weather?.monthly || []
  const humidityVals = monthly.map((m) => Number(m.humidity) || 0).filter((v) => v > 0)
  const humidity = humidityVals.length
    ? humidityVals.reduce((a, b) => a + b, 0) / humidityVals.length
    : null
  const tmaxVals = monthly.map((m) => Number(m.tmax) || 0).filter((v) => v > 0)
  const temp = tmaxVals.length ? tmaxVals.reduce((a, b) => a + b, 0) / tmaxVals.length : null

  const stats = [
    {
      icon: CloudRain,
      label: 'Rain / season',
      value: round(weather?.season_rain_total?.median_mm),
      unit: 'mm',
      tone: 'blue',
    },
    {
      icon: Droplets,
      label: 'Humidity',
      value: humidity === null ? null : round(humidity),
      unit: '%',
      tone: 'cyan',
    },
    {
      icon: ThermometerSun,
      label: 'Max temp',
      value: temp === null ? null : round(temp),
      unit: '°C',
      tone: 'amber',
    },
    {
      icon: Wind,
      label: 'Dry spells',
      value: round(weather?.dry_spells?.avg_per_season),
      unit: '/season',
      tone: 'green',
    },
  ]

  const where = location?.zone
    ? `${location.label || location.name} · ${location.zone}`
    : location?.label || location?.name || 'Selected field'

  return (
    <div className="glass" aria-live="polite">
      <div className="glass__head">
        <span className="glass__dot" aria-hidden="true" />
        <div>
          <p className="glass__eyebrow">NASA POWER · this field</p>
          <h3 className="glass__place">{where}</h3>
        </div>
      </div>

      {status === 'loading' || status === 'idle' ? <Skeleton /> : null}

      {status === 'error' ? (
        <p className="glass__error">Weather data could not load. The recommendation still works.</p>
      ) : null}

      {status === 'ready' ? (
        <div className="glass__grid">
          {stats.map(({ icon: Icon, label, value, unit }) => (
            <div className="glass__tile" key={label}>
              <span className="glass__icon" aria-hidden="true">
                <Icon className="icon" />
              </span>
              <span className="glass__value">
                {value === null ? '—' : value}
                {value !== null && unit ? <small>{unit}</small> : null}
              </span>
              <span className="glass__label">{label}</span>
            </div>
          ))}
        </div>
      ) : null}

      <p className="glass__foot">
        30+ yrs NASA climate · Imagery © Esri/Maxar · Terrain © Mapterhorn
      </p>
    </div>
  )
}
