import { useEffect, useState } from 'react'
import { ArrowRight, LocateFixed, MapPin, Navigation } from 'lucide-react'
import MapPicker from './MapPicker'

const isNum = (v) => v !== '' && Number.isFinite(Number(v))

export default function LocationStep({ value, locations, onChange, onContinue }) {
  const [latText, setLatText] = useState(value ? String(value.lat) : '')
  const [lonText, setLonText] = useState(value ? String(value.lon) : '')
  const [error, setError] = useState('')

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
    onChange({ lat: loc.lat, lon: loc.lon, label: loc.name })
  }

  const pickMap = (lat, lon) => {
    setError('')
    setLatText(String(lat))
    setLonText(String(lon))
    onChange({ lat, lon, label: 'Custom location' })
  }

  const applyManual = () => {
    if (!isNum(latText) || !isNum(lonText)) {
      setError('Enter both a latitude and a longitude.')
      return
    }
    const lat = Number(latText)
    const lon = Number(lonText)
    if (lat < -90 || lat > 90) {
      setError('Latitude must be between -90 and 90.')
      return
    }
    if (lon < -180 || lon > 180) {
      setError('Longitude must be between -180 and 180.')
      return
    }
    setError('')
    onChange({ lat: Number(lat.toFixed(4)), lon: Number(lon.toFixed(4)), label: 'Custom location' })
  }

  return (
    <>
      <div className="grid-2">
        <section className="card">
          <div className="card__head">
            <span className="card__head-icon" aria-hidden="true">
              <MapPin className="icon" />
            </span>
            <div>
              <h2 className="card__title">Pick your field</h2>
              <p className="card__subtitle">Click or tap the map to place a pin. You can fine-tune manually.</p>
            </div>
          </div>
          <div className="card__body">
            <MapPicker lat={value?.lat} lon={value?.lon} onPick={pickMap} />
            <div className="coord-readout" aria-live="polite">
              {value ? (
                <>
                  <span>
                    Selected: <b>{value.label || 'Custom location'}</b>
                  </span>
                  <span>
                    Lat <b>{value.lat}</b> · Lon <b>{value.lon}</b>
                  </span>
                </>
              ) : (
                <span>No field selected yet — tap the map or choose a demo location.</span>
              )}
            </div>
          </div>
        </section>

        <div className="stack">
          <section className="card">
            <div className="card__head">
              <span className="card__head-icon" aria-hidden="true">
                <Navigation className="icon" />
              </span>
              <div>
                <h2 className="card__title">Demo locations</h2>
                <p className="card__subtitle">Northern Nigeria and the Middle Belt.</p>
              </div>
            </div>
            <div className="card__body card__body--tight">
              <ul className="preset-list">
                {locations.map((loc) => (
                  <li key={loc.id}>
                    <button
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
                      <span className="preset__coords">
                        {loc.lat.toFixed(2)}, {loc.lon.toFixed(2)}
                      </span>
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          </section>

          <section className="card">
            <div className="card__head">
              <span className="card__head-icon" aria-hidden="true">
                <LocateFixed className="icon" />
              </span>
              <div>
                <h2 className="card__title">Enter coordinates</h2>
                <p className="card__subtitle">Decimal degrees, WGS 84.</p>
              </div>
            </div>
            <div className="card__body">
              <div className="input-row">
                <div className="field">
                  <label className="label" htmlFor="lat-input">
                    Latitude
                  </label>
                  <input
                    id="lat-input"
                    className={`input ${error ? 'input--error' : ''}`}
                    inputMode="decimal"
                    placeholder="12.0022"
                    value={latText}
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
                    placeholder="8.5919"
                    value={lonText}
                    onChange={(e) => setLonText(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && applyManual()}
                  />
                </div>
              </div>
              {error ? (
                <p className="field-error" role="alert" style={{ marginTop: '0.5rem' }}>
                  {error}
                </p>
              ) : (
                <p className="hint" style={{ marginTop: '0.55rem' }}>
                  NASA POWER works on a coarse grid, so nearby coordinates can share the same climate record.
                </p>
              )}
              <button
                type="button"
                className="btn btn-secondary btn-block"
                style={{ marginTop: '0.7rem' }}
                onClick={applyManual}
              >
                Apply coordinates
              </button>
            </div>
          </section>
        </div>
      </div>

      <div className="action-bar">
        <span className="muted" style={{ fontSize: '0.8rem' }}>
          Step 1 of 3 · Location is used to pull the NASA climate record.
        </span>
        <span className="spacer" />
        <button
          type="button"
          className="btn btn-primary btn-lg"
          disabled={!value}
          onClick={() => onContinue()}
        >
          Continue to farm profile
          <ArrowRight className="icon" aria-hidden="true" />
        </button>
      </div>
    </>
  )
}
