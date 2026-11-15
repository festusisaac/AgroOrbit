import { useEffect, useRef } from 'react'
import {
  Check,
  ChevronRight,
  Droplets,
  Globe2,
  MapPin,
  Mountain,
  ShieldCheck,
  Sparkles,
  Sprout,
  Store,
  Wheat,
  X,
} from 'lucide-react'
import CropGlyph from './CropGlyph'
import { COUNTRIES, findCountry } from '../data/regions'

const ROTATION_PRESETS = [
  { label: 'Continuous Maize', seq: ['maize', 'maize', 'maize'] },
  { label: 'Maize–Cowpea–Maize', seq: ['maize', 'cowpea', 'maize'] },
  { label: 'Sorghum–Groundnut–Sorghum', seq: ['sorghum', 'groundnut', 'sorghum'] },
]

const SOIL_TEXTURES = [
  { id: 'sandy', label: 'Sandy' },
  { id: 'loam', label: 'Loam' },
  { id: 'clay', label: 'Clay' },
]

const WATER_SOURCES = [
  { id: 'rain_fed', label: 'Rain-fed' },
  { id: 'limited_irrigation', label: 'Limited Irrigation' },
  { id: 'irrigated', label: 'Irrigated' },
]

export default function OnboardingModal({
  open,
  onClose,
  countryId,
  regionId,
  onCountryChange,
  onRegionChange,
  form,
  setForm,
  crops,
  onApply,
}) {
  const ref = useRef(null)

  useEffect(() => {
    const dialog = ref.current
    if (!dialog) return
    if (open && !dialog.open) dialog.showModal()
    if (!open && dialog.open) dialog.close()
  }, [open])

  const country = findCountry(countryId)
  const regions = country.regions

  const setYear = (index, cropId) => {
    setForm((prev) => {
      const next = [...prev.current_rotation]
      next[index] = cropId
      return { ...prev, current_rotation: next }
    })
  }

  const setSoil = (field, val) => {
    setForm((prev) => ({
      ...prev,
      soil: { ...prev.soil, [field]: val },
    }))
  }

  const setPriority = (key, val) => {
    setForm((prev) => ({
      ...prev,
      priorities: { ...prev.priorities, [key]: val },
    }))
  }

  return (
    <dialog
      ref={ref}
      className="modal modal--onboarding"
      onClose={onClose}
      onClick={(e) => {
        if (e.target === ref.current) onClose()
      }}
    >
      <div className="modal__head onboarding__head">
        <div className="onboarding__brand">
          <span className="onboarding__icon" aria-hidden="true">
            <Sprout className="icon onboarding__icon-svg" />
          </span>
          <div>
            <h2>Welcome to AgroOrbit</h2>
            <p className="onboarding__sub">
              Review or customize your prefilled farm details to see what grows best.
            </p>
          </div>
        </div>
        <button type="button" className="linkbtn" onClick={onClose} aria-label="Close">
          <X className="icon" aria-hidden="true" />
        </button>
      </div>

      <div className="modal__body onboarding__body">
        {/* Step 1: Location */}
        <section className="onboarding__section">
          <div className="onboarding__section-title">
            <span className="step-badge">1</span>
            <div>
              <h3>Farm Location</h3>
              <p>Where is your farm? We fetch 35+ years of NASA satellite climate data for this region.</p>
            </div>
          </div>

          <div className="onboarding__row">
            <label className="onboarding__field">
              <span>Country</span>
              <select value={countryId} onChange={(e) => onCountryChange(e.target.value)}>
                {COUNTRIES.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </select>
            </label>

            <label className="onboarding__field">
              <span>Region</span>
              <select value={regionId} onChange={(e) => onRegionChange(e.target.value)}>
                {regions.map((r) => (
                  <option key={r.id} value={r.id}>
                    {r.name} ({r.zone})
                  </option>
                ))}
              </select>
            </label>
          </div>
        </section>

        {/* Step 2: Current Rotation */}
        <section className="onboarding__section">
          <div className="onboarding__section-title">
            <span className="step-badge">2</span>
            <div>
              <h3>Current 3-Year Rotation</h3>
              <p>What have you been planting? (Prefilled: Continuous Maize monoculture)</p>
            </div>
          </div>

          <div className="onboarding__quick-presets">
            {ROTATION_PRESETS.map((preset) => {
              const active =
                preset.seq.join(',') === (form.current_rotation || []).join(',')
              return (
                <button
                  key={preset.label}
                  type="button"
                  className={`btn-chip ${active ? 'btn-chip--active' : ''}`}
                  onClick={() => setForm((prev) => ({ ...prev, current_rotation: preset.seq }))}
                >
                  {preset.label}
                </button>
              )
            })}
          </div>

          <div className="onboarding__year-row">
            {[0, 1, 2].map((idx) => (
              <div key={idx} className="onboarding__year-box">
                <span className="year-label">Year {idx + 1}</span>
                <select
                  value={form.current_rotation[idx] || 'maize'}
                  onChange={(e) => setYear(idx, e.target.value)}
                  className="crop-select"
                >
                  {crops.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name}
                    </option>
                  ))}
                </select>
              </div>
            ))}
          </div>
        </section>

        {/* Step 3: Soil & Water */}
        <section className="onboarding__section">
          <div className="onboarding__section-title">
            <span className="step-badge">3</span>
            <div>
              <h3>Soil & Water Situation</h3>
              <p>Tell us about your field conditions.</p>
            </div>
          </div>

          <div className="onboarding__pills-group">
            <div className="pills-subset">
              <span className="subset-label">Soil Texture</span>
              <div className="pills-row">
                {SOIL_TEXTURES.map((t) => (
                  <button
                    key={t.id}
                    type="button"
                    className={`pill ${form.soil.texture === t.id ? 'pill--active' : ''}`}
                    onClick={() => setSoil('texture', t.id)}
                  >
                    {t.label}
                  </button>
                ))}
              </div>
            </div>

            <div className="pills-subset">
              <span className="subset-label">Water Source</span>
              <div className="pills-row">
                {WATER_SOURCES.map((w) => (
                  <button
                    key={w.id}
                    type="button"
                    className={`pill ${form.soil.water_source === w.id ? 'pill--active' : ''}`}
                    onClick={() => setSoil('water_source', w.id)}
                  >
                    {w.label}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </section>

        {/* Step 4: Priorities */}
        <section className="onboarding__section">
          <div className="onboarding__section-title">
            <span className="step-badge">4</span>
            <div>
              <h3>What Matters Most to You?</h3>
              <p>We weigh our recommendations according to your goals.</p>
            </div>
          </div>

          <div className="onboarding__priorities-grid">
            {[
              { key: 'water_saving', name: 'Water Saving', icon: Droplets, val: form.priorities.water_saving },
              { key: 'soil_health', name: 'Soil Health', icon: Sprout, val: form.priorities.soil_health },
              { key: 'market_preference', name: 'Market Demand', icon: Store, val: form.priorities.market_preference },
            ].map(({ key, name, icon: Icon, val }) => (
              <div key={key} className="onboarding__priority-card">
                <div className="priority-card__top">
                  <Icon className="icon" />
                  <span>{name}</span>
                </div>
                <div className="priority-pips">
                  {[1, 3, 5].map((lvl) => (
                    <button
                      key={lvl}
                      type="button"
                      className={`pip-btn ${val === lvl ? 'pip-btn--active' : ''}`}
                      onClick={() => setPriority(key, lvl)}
                    >
                      {lvl === 5 ? 'High' : lvl === 3 ? 'Medium' : 'Low'}
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Footer Actions */}
        <div className="onboarding__actions">
          <button
            type="button"
            className="btn btn-primary btn-lg onboarding__cta"
            onClick={onApply}
          >
            <Sparkles className="icon" aria-hidden="true" />
            Launch Live NASA Analysis
          </button>
          <button
            type="button"
            className="btn btn-secondary onboarding__skip"
            onClick={onClose}
          >
            Explore Dashboard Directly
          </button>
        </div>
      </div>
    </dialog>
  )
}
