import { useEffect, useState } from 'react'
import {
  Check,
  Droplets,
  Loader2,
  LocateFixed,
  MapPin,
  Mountain,
  ShieldCheck,
  SlidersHorizontal,
  Sprout,
  Store,
  Wheat,
} from 'lucide-react'
import MapPicker from './MapPicker'

const SOIL_OPTIONS = {
  texture: [
    ['sandy', 'Sandy'],
    ['loam', 'Loam'],
    ['clay', 'Clay'],
    ['unknown', "Don't know"],
  ],
  drainage: [
    ['good', 'Good'],
    ['moderate', 'Moderate'],
    ['poor', 'Poor'],
    ['unknown', "Don't know"],
  ],
  organic_matter: [
    ['low', 'Low'],
    ['medium', 'Medium'],
    ['high', 'High'],
    ['unknown', "Don't know"],
  ],
  water_source: [
    ['rain_fed', 'Rain-fed'],
    ['limited_irrigation', 'Limited irrigation'],
    ['irrigated', 'Irrigated'],
    ['unknown', "Don't know"],
  ],
  slope: [
    ['flat', 'Flat'],
    ['gentle', 'Gentle'],
    ['steep', 'Steep'],
    ['unknown', "Don't know"],
  ],
}

const PRIORITIES = [
  { key: 'water_saving', name: 'Water', icon: Droplets },
  { key: 'soil_health', name: 'Soil', icon: Sprout },
  { key: 'erosion', name: 'Erosion', icon: Mountain },
  { key: 'market_preference', name: 'Market', icon: Store },
  { key: 'forage', name: 'Forage', icon: Wheat },
  { key: 'resilience', name: 'Resilience', icon: ShieldCheck },
]

const ROTATION_PRESETS = [
  { label: 'Maize ×3', seq: ['maize', 'maize', 'maize'] },
  { label: 'Maize–cowpea–maize', seq: ['maize', 'cowpea', 'maize'] },
  { label: 'Sorghum–groundnut–sorghum', seq: ['sorghum', 'groundnut', 'sorghum'] },
]

const isNum = (v) => v !== '' && Number.isFinite(Number(v))

function FieldSection({ locations, value, onChange }) {
  const [latText, setLatText] = useState(value ? String(value.lat) : '')
  const [lonText, setLonText] = useState(value ? String(value.lon) : '')
  const [error, setError] = useState('')
  const [locating, setLocating] = useState(false)
  const [gpsError, setGpsError] = useState('')

  useEffect(() => {
    setLatText(value ? String(value.lat) : '')
    setLonText(value ? String(value.lon) : '')
  }, [value?.lat, value?.lon])

  const activeId = value
    ? locations.find(
        (l) => Math.abs(l.lat - value.lat) < 0.0002 && Math.abs(l.lon - value.lon) < 0.0002,
      )?.id
    : null

  const pickPreset = (loc) => {
    setError('')
    setLatText(String(loc.lat))
    setLonText(String(loc.lon))
    onChange({ ...loc, label: loc.name })
  }

  const pickMap = (lat, lon) => {
    setError('')
    setLatText(String(lat))
    setLonText(String(lon))
    onChange({ lat, lon, label: 'Custom field' })
  }

  const useGps = () => {
    if (!navigator.geolocation) {
      setGpsError('Location is not supported on this device.')
      return
    }
    setGpsError('')
    setLocating(true)
    navigator.geolocation.getCurrentPosition(
      (position) => {
        const lat = Number(position.coords.latitude.toFixed(4))
        const lon = Number(position.coords.longitude.toFixed(4))
        setLocating(false)
        setError('')
        setLatText(String(lat))
        setLonText(String(lon))
        onChange({ lat, lon, label: 'My location' })
      },
      (err) => {
        setLocating(false)
        setGpsError(
          err.code === 1
            ? 'Location permission denied.'
            : 'Could not get your location. Try again.',
        )
      },
      { enableHighAccuracy: true, timeout: 12000, maximumAge: 60000 },
    )
  }

  const applyManual = () => {
    if (!isNum(latText) || !isNum(lonText)) {
      setError('Enter both coordinates.')
      return
    }
    const lat = Number(latText)
    const lon = Number(lonText)
    if (lat < -90 || lat > 90 || lon < -180 || lon > 180) {
      setError('Coordinates are out of range.')
      return
    }
    setError('')
    onChange({ lat: Number(lat.toFixed(4)), lon: Number(lon.toFixed(4)), label: 'Custom field' })
  }

  return (
    <section className="setup-card" id="field">
      <div className="setup-card__head">
        <span className="step-no" aria-hidden="true">
          1
        </span>
        <div>
          <h2>Choose a field</h2>
          <p>Tap the map or pick a location.</p>
        </div>
      </div>
      <div className="setup-card__body">
        <div className="preset-grid">
          {locations.map((loc) => (
            <button
              key={loc.id}
              type="button"
              className="preset"
              data-active={activeId === loc.id}
              onClick={() => pickPreset(loc)}
            >
              <span className="preset__pin" aria-hidden="true">
                <MapPin className="icon" />
              </span>
              <span className="preset__text">
                <span className="preset__name">{loc.name}</span>
                <span className="preset__zone">{loc.zone}</span>
              </span>
            </button>
          ))}
        </div>

        <MapPicker lat={value?.lat} lon={value?.lon} onPick={pickMap} />

        <div className="field-readout" aria-live="polite">
          {value ? (
            <>
              <MapPin className="icon" aria-hidden="true" />
              <span>
                <b>{value.label || value.name || 'Custom field'}</b> · {Number(value.lat).toFixed(2)},{' '}
                {Number(value.lon).toFixed(2)}
              </span>
            </>
          ) : (
            <span>No field selected.</span>
          )}
        </div>

        <div className="field-actions">
          <button type="button" className="btn btn-secondary btn-sm" onClick={useGps} disabled={locating}>
            {locating ? (
              <Loader2 className="icon spin" aria-hidden="true" />
            ) : (
              <LocateFixed className="icon" aria-hidden="true" />
            )}
            {locating ? 'Locating…' : 'Use my location'}
          </button>
        </div>
        {gpsError ? (
          <p className="field-error" role="alert" style={{ marginTop: '0.35rem' }}>
            {gpsError}
          </p>
        ) : null}

        <details className="more">
          <summary>
            <LocateFixed className="icon" aria-hidden="true" />
            Enter coordinates
          </summary>
          <div className="more__body">
            <div className="input-row">
              <div className="field">
                <label className="label" htmlFor="lat-input">
                  Latitude
                </label>
                <input
                  id="lat-input"
                  className={`input ${error ? 'input--error' : ''}`}
                  inputMode="decimal"
                  value={latText}
                  placeholder="12.0022"
                  onChange={(e) => setLatText(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && applyManual()}
                />
              </div>
              <div className="field">
                <label className="label" htmlFor="lon-input">
                  Longitude
                </label>
                <input
                  id="lon-input"
                  className={`input ${error ? 'input--error' : ''}`}
                  inputMode="decimal"
                  value={lonText}
                  placeholder="8.5919"
                  onChange={(e) => setLonText(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && applyManual()}
                />
              </div>
            </div>
            {error ? (
              <p className="field-error" role="alert" style={{ marginTop: '0.35rem' }}>
                {error}
              </p>
            ) : null}
            <button type="button" className="btn btn-secondary btn-sm" style={{ marginTop: '0.4rem' }} onClick={applyManual}>
              Use these coordinates
            </button>
          </div>
        </details>
      </div>
    </section>
  )
}

function RotationSection({ form, setForm, crops }) {
  const setYear = (index, cropId) =>
    setForm((prev) => {
      const next = [...prev.current_rotation]
      next[index] = cropId
      return { ...prev, current_rotation: next }
    })

  return (
    <section className="setup-card">
      <div className="setup-card__head">
        <span className="step-no" aria-hidden="true">
          2
        </span>
        <div>
          <h2>Current rotation</h2>
          <p>One crop per year.</p>
        </div>
      </div>
      <div className="setup-card__body">
        <div className="rotation-row">
          {[0, 1, 2].map((index) => (
            <div className="year-select" key={index}>
              <label className="label" htmlFor={`year-${index}`}>
                Year {index + 1}
              </label>
              <select
                id={`year-${index}`}
                className="select"
                value={form.current_rotation[index] || 'maize'}
                onChange={(e) => setYear(index, e.target.value)}
              >
                {crops.map((crop) => (
                  <option key={crop.id} value={crop.id}>
                    {crop.name}
                  </option>
                ))}
              </select>
            </div>
          ))}
        </div>
        <div className="quick-fills">
          {ROTATION_PRESETS.map((preset) => (
            <button
              key={preset.label}
              type="button"
              onClick={() => setForm((prev) => ({ ...prev, current_rotation: preset.seq }))}
            >
              {preset.label}
            </button>
          ))}
        </div>
      </div>
    </section>
  )
}

function PrioritiesSection({ form, setForm }) {
  const setPriority = (key, value) =>
    setForm((prev) => ({ ...prev, priorities: { ...prev.priorities, [key]: value } }))

  return (
    <section className="setup-card">
      <div className="setup-card__head">
        <span className="step-no" aria-hidden="true">
          3
        </span>
        <div>
          <h2>What matters</h2>
          <p>0 low · 5 high</p>
        </div>
        <SlidersHorizontal className="icon" style={{ marginLeft: 'auto', width: 16, height: 16 }} aria-hidden="true" />
      </div>
      <div className="setup-card__body">
        <div className="priority-grid">
          {PRIORITIES.map(({ key, name, icon: Icon }) => {
            const value = Number(form.priorities[key] ?? 0)
            return (
              <div className="priority-row" key={key}>
                <div className="priority-row__top">
                  <Icon className="icon" aria-hidden="true" />
                  <span>{name}</span>
                  <b>{value}</b>
                </div>
                <input
                  className="range"
                  type="range"
                  min="0"
                  max="5"
                  step="1"
                  value={value}
                  aria-label={name}
                  style={{ '--fill': `${(value / 5) * 100}%` }}
                  onChange={(e) => setPriority(key, Number(e.target.value))}
                />
              </div>
            )
          })}
        </div>
      </div>
    </section>
  )
}

function ExtrasSection({ form, setForm, crops }) {
  const setSoil = (key, value) =>
    setForm((prev) => ({ ...prev, soil: { ...prev.soil, [key]: value } }))

  const setScenario = (key, value) =>
    setForm((prev) => ({ ...prev, scenario: { ...prev.scenario, [key]: value } }))

  const togglePreferred = (cropId) =>
    setForm((prev) => {
      const has = prev.preferred_crops.includes(cropId)
      return {
        ...prev,
        preferred_crops: has
          ? prev.preferred_crops.filter((id) => id !== cropId)
          : [...prev.preferred_crops, cropId],
      }
    })

  return (
    <details className="setup-card">
      <summary style={{ display: 'flex', alignItems: 'center', gap: '0.55rem', padding: '0.8rem 0.95rem', cursor: 'pointer', listStyle: 'none' }}>
        <span className="step-no" aria-hidden="true">
          4
        </span>
        <div style={{ flex: 1 }}>
          <h2 style={{ fontFamily: 'var(--font-sans)', fontSize: '0.9rem', fontWeight: 650 }}>
            Soil, crops &amp; scenario
          </h2>
        </div>
        <span className="tag">Optional</span>
      </summary>
      <div className="setup-card__body" style={{ paddingTop: '0.2rem' }}>
        <div className="soil-grid">
          {Object.entries(SOIL_OPTIONS).map(([key, options]) => (
            <div className="field" key={key}>
              <label className="label" htmlFor={`soil-${key}`}>
                {key === 'organic_matter'
                  ? 'Organic matter'
                  : key === 'water_source'
                    ? 'Water source'
                    : key.charAt(0).toUpperCase() + key.slice(1)}
              </label>
              <select
                id={`soil-${key}`}
                className="select"
                value={form.soil[key]}
                onChange={(e) => setSoil(key, e.target.value)}
              >
                {options.map(([v, l]) => (
                  <option key={v} value={v}>
                    {l}
                  </option>
                ))}
              </select>
            </div>
          ))}
        </div>

        <p className="label" style={{ marginTop: '0.75rem' }}>
          Preferred crops
        </p>
        <div className="chip-picker" style={{ marginTop: '0.3rem' }}>
          {crops.map((crop) => {
            const selected = form.preferred_crops.includes(crop.id)
            return (
              <button
                key={crop.id}
                type="button"
                className="pick-chip"
                data-selected={selected}
                aria-pressed={selected}
                onClick={() => togglePreferred(crop.id)}
              >
                <Check className="tick" aria-hidden="true" />
                {crop.name}
              </button>
            )
          })}
        </div>

        <div className="input-row" style={{ marginTop: '0.85rem' }}>
          <div className="field">
            <label className="label" htmlFor="rain-change">
              Rain {form.scenario.rainfall_change_pct > 0 ? '+' : ''}
              {form.scenario.rainfall_change_pct}%
            </label>
            <input
              id="rain-change"
              className="range"
              type="range"
              min="-30"
              max="30"
              step="5"
              value={form.scenario.rainfall_change_pct}
              style={{ '--fill': `${((form.scenario.rainfall_change_pct + 30) / 60) * 100}%` }}
              onChange={(e) => setScenario('rainfall_change_pct', Number(e.target.value))}
            />
          </div>
          <div className="field">
            <label className="label" htmlFor="temp-change">
              Temp +{form.scenario.temperature_change_c}°C
            </label>
            <input
              id="temp-change"
              className="range"
              type="range"
              min="0"
              max="3"
              step="0.5"
              value={form.scenario.temperature_change_c}
              style={{ '--fill': `${(form.scenario.temperature_change_c / 3) * 100}%` }}
              onChange={(e) => setScenario('temperature_change_c', Number(e.target.value))}
            />
          </div>
        </div>

        <p className="hint" style={{ marginTop: '0.5rem' }}>
          Don’t know? Leave it. Confidence adjusts automatically.
        </p>
      </div>
    </details>
  )
}

export default function SetupPanel({
  locations,
  location,
  onLocationChange,
  form,
  setForm,
  crops,
}) {
  const cropMap = Object.fromEntries(crops.map((c) => [c.id, c]))
  const rotation = (form.current_rotation || []).map((id) => cropMap[id]?.name || id)
  const activePriorities = PRIORITIES.filter((p) => Number(form.priorities[p.key]) > 0).length

  return (
    <aside className="setup">
      <FieldSection locations={locations} value={location} onChange={onLocationChange} />
      <RotationSection form={form} setForm={setForm} crops={crops} />
      <PrioritiesSection form={form} setForm={setForm} />
      <ExtrasSection form={form} setForm={setForm} crops={crops} />

      <div className="runbar runbar--plain">
        <div className="runbar__summary">
          <b>{location?.label || location?.name || 'No field selected'}</b>
          <span>
            {rotation.join(' → ')} · {activePriorities} priorities
          </span>
        </div>
      </div>
    </aside>
  )
}
