import { lazy, Suspense, useCallback, useEffect, useRef, useState } from 'react'
import { ChevronDown, Loader2, Sparkles } from 'lucide-react'
import Sidebar from './components/Sidebar'
import MobileNav from './components/MobileNav'
import TopBar from './components/TopBar'
import Footer from './components/Footer'
import SetupPanel from './components/SetupPanel'
import ResultsView from './components/ResultsView'
import HowItWorks from './components/HowItWorks'
import GlassWeather from './components/GlassWeather'
import { api, mockApi, hasBackend } from './api/client'
import { CROPS, LOCATIONS } from './api/mockData'
import {
  COUNTRIES,
  DEFAULT_COUNTRY,
  DEFAULT_REGION,
  findCountry,
  findRegion,
  locationFromRegion,
} from './data/regions'

const MapPicker = lazy(() => import('./components/MapPicker'))

const INITIAL_FORM = {
  current_rotation: ['maize', 'maize', 'maize'],
  soil: {
    texture: 'sandy',
    drainage: 'unknown',
    organic_matter: 'low',
    water_source: 'rain_fed',
    slope: 'unknown',
  },
  priorities: {
    water_saving: 4,
    soil_health: 4,
    erosion: 2,
    market_preference: 3,
    forage: 1,
    resilience: 4,
  },
  preferred_crops: ['maize', 'groundnut'],
  scenario: { rainfall_change_pct: 0, temperature_change_c: 0 },
}

const inputKeyOf = (location, form) => JSON.stringify([location, form])
const DEFAULT_LOCATION = locationFromRegion(findRegion(DEFAULT_COUNTRY, DEFAULT_REGION))

export default function App() {
  const [location, setLocation] = useState(DEFAULT_LOCATION)
  const [countryId, setCountryId] = useState(DEFAULT_COUNTRY)
  const [regionId, setRegionId] = useState(DEFAULT_REGION)
  const [form, setForm] = useState(INITIAL_FORM)
  const [crops, setCrops] = useState(CROPS)
  const [locations, setLocations] = useState(LOCATIONS)
  const [usingDemo, setUsingDemo] = useState(!hasBackend)

  const [status, setStatus] = useState('idle')
  const [results, setResults] = useState(null)
  const [error, setError] = useState(null)
  const [refreshing, setRefreshing] = useState(false)
  const [climate, setClimate] = useState(null)
  const [climateStatus, setClimateStatus] = useState('idle')
  const [weather, setWeather] = useState(null)
  const [weatherStatus, setWeatherStatus] = useState('loading')
  const [howOpen, setHowOpen] = useState(false)
  const [setupOpen, setSetupOpen] = useState(false)
  const [activeSection, setActiveSection] = useState('top')

  const requestRef = useRef(0)
  const lastKeyRef = useRef('')
  const outputRef = useRef(null)

  const country = findCountry(countryId)
  const regions = country.regions

  useEffect(() => {
    let active = true
    const client = !hasBackend || usingDemo ? mockApi : api
    Promise.all([client.getLocations(), client.getCrops()])
      .then(([nextLocations, nextCrops]) => {
        if (!active) return
        if (Array.isArray(nextLocations) && nextLocations.length) setLocations(nextLocations)
        if (Array.isArray(nextCrops) && nextCrops.length) setCrops(nextCrops)
      })
      .catch(() => {
        if (!active) return
        setUsingDemo(true)
        setLocations(LOCATIONS)
        setCrops(CROPS)
      })
    return () => {
      active = false
    }
  }, [usingDemo])

  // Weather for the glass panel (independent of the comparison)
  useEffect(() => {
    let active = true
    setWeatherStatus('loading')
    setWeather(null)
    const client = !hasBackend || usingDemo ? mockApi : api
    client
      .getClimate(location.lat, location.lon)
      .then((next) => {
        if (!active) return
        setWeather(next)
        setWeatherStatus('ready')
      })
      .catch(() => {
        if (active) setWeatherStatus('error')
      })
    return () => {
      active = false
    }
  }, [location.lat, location.lon, usingDemo])

  const runComparison = useCallback(
    async ({ demo = false, quiet = false } = {}) => {
      if (!location) return
      const key = inputKeyOf(location, form)
      const id = ++requestRef.current
      const client = !hasBackend || usingDemo || demo ? mockApi : api

      if (quiet) {
        setRefreshing(true)
      } else {
        setStatus('loading')
        setResults(null)
        setError(null)
        setClimate(null)
        setClimateStatus('loading')
        if (window.innerWidth < 1020) {
          window.setTimeout(
            () => outputRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }),
            60,
          )
        }
      }

      try {
        const [rec, clim] = await Promise.allSettled([
          client.postRecommend({
            lat: location.lat,
            lon: location.lon,
            current_rotation: form.current_rotation,
            soil: form.soil,
            priorities: form.priorities,
            preferred_crops: form.preferred_crops,
            scenario: form.scenario,
          }),
          client.getClimate(location.lat, location.lon),
        ])

        if (id !== requestRef.current) return
        if (rec.status === 'rejected') throw rec.reason

        lastKeyRef.current = key
        setResults(rec.value)
        setStatus('ready')

        if (clim.status === 'fulfilled') {
          setClimate(clim.value)
          setClimateStatus('ready')
          setWeather(clim.value)
          setWeatherStatus('ready')
        } else if (!quiet) {
          setClimateStatus('error')
        }
      } catch (err) {
        if (id !== requestRef.current || quiet) return
        setStatus('error')
        setError(err)
      } finally {
        if (id === requestRef.current) setRefreshing(false)
      }
    },
    [location, form, usingDemo],
  )

  useEffect(() => {
    if (status !== 'ready' || !location) return
    if (inputKeyOf(location, form) === lastKeyRef.current) return
    const timer = window.setTimeout(() => runComparison({ quiet: true }), 650)
    return () => window.clearTimeout(timer)
  }, [location, form, status, runComparison])

  const busy = status === 'loading' || refreshing

  const handleLocationChange = (next) => {
    setLocation(next)
  }

  const handleCountry = (id) => {
    const nextCountry = findCountry(id)
    const nextRegion = nextCountry.regions[0]
    setCountryId(id)
    setRegionId(nextRegion.id)
    setLocation(locationFromRegion(nextRegion))
  }

  const handleRegion = (id) => {
    setRegionId(id)
    setLocation(locationFromRegion(findRegion(countryId, id)))
  }

  const handleNavigate = (id) => {
    const target =
      id === 'field' ? 'top' : document.getElementById(id) ? id : id === 'climate' ? 'compare' : 'top'
    setActiveSection(id)
    document.getElementById(target)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }

  const handleHome = () => {
    setActiveSection('top')
    restart()
  }

  const handleRun = () => {
    if (status === 'ready') runComparison({ quiet: true })
    else runComparison()
  }

  const handleUseDemo = () => {
    setUsingDemo(true)
    runComparison({ demo: true })
  }

  const restart = () => {
    requestRef.current += 1
    lastKeyRef.current = ''
    setCountryId(DEFAULT_COUNTRY)
    setRegionId(DEFAULT_REGION)
    setLocation(DEFAULT_LOCATION)
    setForm(INITIAL_FORM)
    setUsingDemo(!hasBackend)
    setStatus('idle')
    setResults(null)
    setError(null)
    setClimate(null)
    setClimateStatus('idle')
    setRefreshing(false)
    setSetupOpen(false)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  return (
    <div className="shell">
      <Sidebar active={activeSection} onNavigate={handleNavigate} />

      <div className="main">
        <TopBar
          location={location}
          mode={usingDemo ? 'demo' : 'live'}
          onHowItWorks={() => setHowOpen(true)}
          onHome={handleHome}
        />

        <main className="page">
          <div className="container page__inner">
            <section className="explore" id="top">
              <div className="explore__map">
                <Suspense
                  fallback={
                    <div className="map-frame map-frame--hero">
                      <div className="map map--gl map--loading">
                        <span>Loading map…</span>
                      </div>
                    </div>
                  }
                >
                  <MapPicker
                    lat={location?.lat}
                    lon={location?.lon}
                    onPick={(lat, lon) =>
                      handleLocationChange({ lat, lon, label: 'Custom field' })
                    }
                  />
                </Suspense>
                <GlassWeather weather={weather} status={weatherStatus} location={location} />
              </div>

              <div className="explore__panel">
                <p className="eyebrow">NASA Space Apps 2026 · Field Shift</p>
                <h1>See what grows best on your land.</h1>
                <p className="explore__sub">
                  Choose a country and region. We read 30+ years of NASA satellite climate —
                  anywhere in the world.
                </p>

                <div className="region-picker">
                  <label className="region-field">
                    <span>Country</span>
                    <select value={countryId} onChange={(e) => handleCountry(e.target.value)}>
                      {COUNTRIES.map((c) => (
                        <option key={c.id} value={c.id}>
                          {c.flag} {c.name}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label className="region-field">
                    <span>Region</span>
                    <select value={regionId} onChange={(e) => handleRegion(e.target.value)}>
                      {regions.map((r) => (
                        <option key={r.id} value={r.id}>
                          {r.name}
                        </option>
                      ))}
                    </select>
                  </label>
                </div>

                <button
                  type="button"
                  className="btn btn-primary btn-lg explore__cta"
                  onClick={handleRun}
                  disabled={busy}
                >
                  {busy ? (
                    <Loader2 className="icon spin" aria-hidden="true" />
                  ) : (
                    <Sparkles className="icon" aria-hidden="true" />
                  )}
                  {busy ? 'Reading the climate…' : 'Compare rotations'}
                </button>
                <p className="explore__hint">
                  {usingDemo ? 'Demo data' : 'Live NASA data'} · works worldwide
                </p>

                <button
                  type="button"
                  className="setup-toggle"
                  aria-expanded={setupOpen}
                  onClick={() => setSetupOpen((v) => !v)}
                >
                  {setupOpen ? 'Hide advanced setup' : 'Advanced setup · optional'}
                  <ChevronDown className={`icon ${setupOpen ? 'is-open' : ''}`} aria-hidden="true" />
                </button>

                {setupOpen ? (
                  <div className="explore__setup">
                    <SetupPanel
                      locations={locations}
                      location={location}
                      onLocationChange={handleLocationChange}
                      form={form}
                      setForm={setForm}
                      crops={crops}
                      showField={false}
                    />
                  </div>
                ) : null}
              </div>
            </section>

            {status !== 'idle' ? (
              <div className="output" id="compare" ref={outputRef} aria-live="polite">
                <ResultsView
                  status={status}
                  data={results}
                  error={error}
                  climate={climate}
                  climateStatus={climateStatus}
                  location={location}
                  crops={crops}
                  usingDemo={usingDemo || !hasBackend}
                  refreshing={refreshing}
                  onRetry={handleRun}
                  onUseDemo={handleUseDemo}
                />
              </div>
            ) : null}

            <section className="method" id="about">
              <div>
                <p className="eyebrow">How it works</p>
                <h2>NASA climate + crop rules.</h2>
                <p>30+ years of satellites, scored the same way everywhere.</p>
              </div>
              <div className="scale">
                <div className="scale__item scale__item--strong">
                  <b>75–100</b>
                  <span>Strong fit</span>
                  <div className="scale__bar">
                    <i />
                  </div>
                </div>
                <div className="scale__item scale__item--moderate">
                  <b>55–74</b>
                  <span>Moderate</span>
                  <div className="scale__bar">
                    <i />
                  </div>
                </div>
                <div className="scale__item scale__item--weak">
                  <b>0–54</b>
                  <span>Weak fit</span>
                  <div className="scale__bar">
                    <i />
                  </div>
                </div>
              </div>
            </section>
          </div>
        </main>

        <Footer />
        <MobileNav active={activeSection} onNavigate={handleNavigate} />
      </div>

      <HowItWorks open={howOpen} onClose={() => setHowOpen(false)} />
    </div>
  )
}
