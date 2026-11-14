import { ArrowLeft, ArrowRight, Check, Info, Leaf, SlidersHorizontal, Sprout, Waves } from 'lucide-react'
import Term from './Term'

const SOIL_OPTIONS = {
  texture: [
    ['sandy', 'Sandy'],
    ['loam', 'Loam'],
    ['clay', 'Clay'],
    ['unknown', "I don't know"],
  ],
  drainage: [
    ['good', 'Good'],
    ['moderate', 'Moderate'],
    ['poor', 'Poor / waterlogs'],
    ['unknown', "I don't know"],
  ],
  organic_matter: [
    ['low', 'Low'],
    ['medium', 'Medium'],
    ['high', 'High'],
    ['unknown', "I don't know"],
  ],
  water_source: [
    ['rain_fed', 'Rain-fed'],
    ['limited_irrigation', 'Limited irrigation'],
    ['irrigated', 'Irrigated'],
    ['unknown', "I don't know"],
  ],
  slope: [
    ['flat', 'Flat'],
    ['gentle', 'Gentle'],
    ['steep', 'Steep'],
    ['unknown', "I don't know"],
  ],
}

const PRIORITIES = [
  { key: 'water_saving', name: 'Water saving', hint: 'Rainfall reliability during the crop window' },
  { key: 'soil_health', name: 'Soil health', hint: 'Organic matter, nitrogen and pest breaks' },
  { key: 'erosion', name: 'Erosion control', hint: 'Ground cover and slope protection' },
  { key: 'market_preference', name: 'Market preference', hint: 'Crops you prefer to grow or sell' },
  { key: 'forage', name: 'Forage', hint: 'Residue and fodder value' },
  { key: 'resilience', name: 'Resilience', hint: 'Season fit and heat/drought tolerance' },
]

const ROTATION_PRESETS = [
  { label: 'Continuous maize', seq: ['maize', 'maize', 'maize'] },
  { label: 'Maize–cowpea–maize', seq: ['maize', 'cowpea', 'maize'] },
  { label: 'Sorghum–groundnut–sorghum', seq: ['sorghum', 'groundnut', 'sorghum'] },
]

export default function ProfileStep({ form, setForm, crops, location, onBack, onSubmit }) {
  const cropMap = Object.fromEntries(crops.map((c) => [c.id, c]))

  const setSoil = (key, value) =>
    setForm((prev) => ({ ...prev, soil: { ...prev.soil, [key]: value } }))

  const setPriority = (key, value) =>
    setForm((prev) => ({ ...prev, priorities: { ...prev.priorities, [key]: value } }))

  const setYear = (index, cropId) =>
    setForm((prev) => {
      const next = [...prev.current_rotation]
      next[index] = cropId
      return { ...prev, current_rotation: next }
    })

  const setRotation = (seq) => setForm((prev) => ({ ...prev, current_rotation: seq }))

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

  const setScenario = (key, value) =>
    setForm((prev) => ({ ...prev, scenario: { ...prev.scenario, [key]: value } }))

  const activePriorities = PRIORITIES.filter((p) => Number(form.priorities[p.key]) > 0).sort(
    (a, b) => form.priorities[b.key] - form.priorities[a.key],
  )
  const scenarioActive =
    Number(form.scenario.rainfall_change_pct) !== 0 ||
    Number(form.scenario.temperature_change_c) !== 0

  return (
    <>
      <div className="grid-2">
        <div className="stack">
          <section className="card">
            <div className="card__head">
              <span className="card__head-icon" aria-hidden="true">
                <Sprout className="icon" />
              </span>
              <div>
                <h2 className="card__title">Your current rotation</h2>
                <p className="card__subtitle">Three main-season crops, one per year.</p>
              </div>
            </div>
            <div className="card__body">
              <div className="rotation-grid">
                {[0, 1, 2].map((index) => (
                  <div className="rotation-year" key={index}>
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
              <p className="hint" style={{ marginTop: '0.75rem' }}>
                Intercropping and double-cropping are out of scope. Quick start:
              </p>
              <div className="row row--wrap" style={{ marginTop: '0.45rem' }}>
                {ROTATION_PRESETS.map((preset) => (
                  <button
                    key={preset.label}
                    type="button"
                    className="btn btn-secondary"
                    style={{ fontSize: '0.78rem', padding: '0.4rem 0.6rem' }}
                    onClick={() => setRotation(preset.seq)}
                  >
                    {preset.label}
                  </button>
                ))}
              </div>
            </div>
          </section>

          <section className="card">
            <div className="card__head">
              <span className="card__head-icon" aria-hidden="true">
                <Waves className="icon" />
              </span>
              <div>
                <h2 className="card__title">Soil &amp; water</h2>
                <p className="card__subtitle">
                  Optional. “I don’t know” is a valid answer and only lowers data confidence.
                </p>
              </div>
            </div>
            <div className="card__body">
              <div className="grid-2 grid-2--even" style={{ gap: '0.9rem' }}>
                <div className="field">
                  <label className="label" htmlFor="soil-texture">
                    Soil texture <span className="label__optional">· optional</span>
                  </label>
                  <select
                    id="soil-texture"
                    className="select"
                    value={form.soil.texture}
                    onChange={(e) => setSoil('texture', e.target.value)}
                  >
                    {SOIL_OPTIONS.texture.map(([v, l]) => (
                      <option key={v} value={v}>
                        {l}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="field">
                  <label className="label" htmlFor="soil-drainage">
                    Drainage <span className="label__optional">· optional</span>
                  </label>
                  <select
                    id="soil-drainage"
                    className="select"
                    value={form.soil.drainage}
                    onChange={(e) => setSoil('drainage', e.target.value)}
                  >
                    {SOIL_OPTIONS.drainage.map(([v, l]) => (
                      <option key={v} value={v}>
                        {l}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="field">
                  <label className="label" htmlFor="soil-om">
                    Organic matter <span className="label__optional">· optional</span>
                  </label>
                  <select
                    id="soil-om"
                    className="select"
                    value={form.soil.organic_matter}
                    onChange={(e) => setSoil('organic_matter', e.target.value)}
                  >
                    {SOIL_OPTIONS.organic_matter.map(([v, l]) => (
                      <option key={v} value={v}>
                        {l}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="field">
                  <label className="label" htmlFor="soil-water">
                    Water source
                  </label>
                  <select
                    id="soil-water"
                    className="select"
                    value={form.soil.water_source}
                    onChange={(e) => setSoil('water_source', e.target.value)}
                  >
                    {SOIL_OPTIONS.water_source.map(([v, l]) => (
                      <option key={v} value={v}>
                        {l}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="field">
                  <label className="label" htmlFor="soil-slope">
                    Slope <span className="label__optional">· optional</span>
                  </label>
                  <select
                    id="soil-slope"
                    className="select"
                    value={form.soil.slope}
                    onChange={(e) => setSoil('slope', e.target.value)}
                  >
                    {SOIL_OPTIONS.slope.map(([v, l]) => (
                      <option key={v} value={v}>
                        {l}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
              <div className="callout" style={{ marginTop: '0.9rem' }}>
                <Info className="icon" aria-hidden="true" />
                <div>
                  These answers steer soil-related criteria only. They never override the season
                  feasibility check.
                </div>
              </div>
            </div>
          </section>

          <section className="card">
            <div className="card__head">
              <span className="card__head-icon" aria-hidden="true">
                <SlidersHorizontal className="icon" />
              </span>
              <div>
                <h2 className="card__title">What matters to you</h2>
                <p className="card__subtitle">0 = not a priority, 5 = very important.</p>
              </div>
            </div>
            <div className="card__body">
              {PRIORITIES.map((priority) => {
                const value = Number(form.priorities[priority.key] ?? 0)
                return (
                  <div className="priority" key={priority.key}>
                    <div className="priority__top">
                      <span className="priority__name">{priority.name}</span>
                      <span className="priority__value" data-high={value >= 4}>
                        {value}
                      </span>
                    </div>
                    <p className="hint" style={{ marginBottom: '0.25rem' }}>
                      {priority.hint}
                    </p>
                    <input
                      className="range"
                      type="range"
                      min="0"
                      max="5"
                      step="1"
                      value={value}
                      style={{ '--fill': `${(value / 5) * 100}%` }}
                      aria-label={priority.name}
                      onChange={(e) => setPriority(priority.key, Number(e.target.value))}
                    />
                    <div className="priority__scale" aria-hidden="true">
                      <span>Not a priority</span>
                      <span>Very important</span>
                    </div>
                  </div>
                )
              })}
              {activePriorities.length === 0 ? (
                <div className="callout">
                  <Info className="icon" aria-hidden="true" />
                  <div>
                    All priorities are zero, so the comparison will use equal weights across all
                    criteria.
                  </div>
                </div>
              ) : null}
            </div>
          </section>

          <section className="card">
            <div className="card__head">
              <span className="card__head-icon" aria-hidden="true">
                <Leaf className="icon" />
              </span>
              <div>
                <h2 className="card__title">Crops you prefer to grow or sell</h2>
                <p className="card__subtitle">
                  Optional. Used for <Term k="market_fit">market preference fit</Term>, not income.
                </p>
              </div>
            </div>
            <div className="card__body">
              <div className="chip-picker">
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
              <p className="hint" style={{ marginTop: '0.7rem' }}>
                Leaving this empty is fine. Market preference fit is then treated as neutral and
                listed as an information gap.
              </p>
            </div>
          </section>

          <section className="card">
            <div className="card__head">
              <span className="card__head-icon" aria-hidden="true">
                <SlidersHorizontal className="icon" />
              </span>
              <div>
                <h2 className="card__title">Hypothetical scenario</h2>
                <p className="card__subtitle">
                  Optional sensitivity test — <Term k="scenario">not a forecast</Term>.
                </p>
              </div>
              <span className="spacer" />
              <span className={`chip ${scenarioActive ? 'chip--amber' : ''}`}>
                {scenarioActive ? 'Scenario active' : 'Baseline'}
              </span>
            </div>
            <div className="card__body">
              <div className="field">
                <label className="label" htmlFor="rain-change">
                  Rainfall change: {form.scenario.rainfall_change_pct > 0 ? '+' : ''}
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
                  style={{
                    '--fill': `${((form.scenario.rainfall_change_pct + 30) / 60) * 100}%`,
                  }}
                  onChange={(e) => setScenario('rainfall_change_pct', Number(e.target.value))}
                />
              </div>
              <div className="field">
                <label className="label" htmlFor="temp-change">
                  Temperature change: +{form.scenario.temperature_change_c} °C
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
              <div className="callout" style={{ marginTop: '0.6rem' }}>
                <Info className="icon" aria-hidden="true" />
                <div>
                  This scales daily rainfall and shifts daily temperature, then re-runs the same
                  analysis. It does not change rainfall timing patterns.
                </div>
              </div>
            </div>
          </section>
        </div>

        <aside className="sticky-side">
          <section className="card">
            <div className="card__head">
              <div>
                <h2 className="card__title">Your setup</h2>
                <p className="card__subtitle">A quick check before comparing.</p>
              </div>
            </div>
            <div className="card__body">
              <ul className="summary-list">
                <li>
                  <span className="k">Field</span>
                  <span className="v">{location?.label || 'Selected field'}</span>
                </li>
                <li>
                  <span className="k">Coordinates</span>
                  <span className="v num">
                    {location?.lat}, {location?.lon}
                  </span>
                </li>
              </ul>

              <div style={{ marginTop: '0.85rem' }}>
                <p className="label">Current rotation</p>
                <div className="mini-seq">
                  {form.current_rotation.map((cropId, index) => (
                    <div className="mini-seq__row" key={index}>
                      <span className="mini-seq__year">Year {index + 1}</span>
                      <span>{cropMap[cropId]?.name || cropId}</span>
                    </div>
                  ))}
                </div>
              </div>

              <hr className="divider" />

              <p className="label">Top priorities</p>
              {activePriorities.length ? (
                <div className="row row--wrap" style={{ marginTop: '0.35rem' }}>
                  {activePriorities.slice(0, 4).map((p) => (
                    <span className="chip chip--green" key={p.key}>
                      {p.name} · {form.priorities[p.key]}
                    </span>
                  ))}
                </div>
              ) : (
                <p className="hint" style={{ marginTop: '0.3rem' }}>
                  None set — equal weights will be used.
                </p>
              )}

              <hr className="divider" />

              <p className="label">Preferred crops</p>
              <p className="hint" style={{ marginTop: '0.25rem' }}>
                {form.preferred_crops.length
                  ? form.preferred_crops.map((id) => cropMap[id]?.name || id).join(', ')
                  : 'None selected'}
              </p>

              <div className="side-note" style={{ marginTop: '0.9rem' }}>
                Answers are used only to build this comparison. There are no accounts and nothing is
                stored after you leave.
              </div>
            </div>
          </section>
        </aside>
      </div>

      <div className="action-bar">
        <button type="button" className="btn btn-secondary" onClick={onBack}>
          <ArrowLeft className="icon" aria-hidden="true" />
          Back
        </button>
        <span className="spacer" />
        <button type="button" className="btn btn-primary btn-lg" onClick={() => onSubmit()}>
          Compare rotations
          <ArrowRight className="icon" aria-hidden="true" />
        </button>
      </div>
    </>
  )
}
