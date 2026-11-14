import { useCallback, useEffect, useRef, useState } from 'react'
import { BadgeCheck } from 'lucide-react'
import Sidebar from './components/Sidebar'
import MobileNav from './components/MobileNav'
import TopBar from './components/TopBar'
import Footer from './components/Footer'
import SetupPanel from './components/SetupPanel'
import EmptyState from './components/EmptyState'
import ResultsView from './components/ResultsView'
import HowItWorks from './components/HowItWorks'
import { api, mockApi, hasBackend } from './api/client'
import { CROPS, LOCATIONS } from './api/mockData'

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
const DEFAULT_LOCATION = { ...LOCATIONS[0], label: LOCATIONS[0].name }

export default function App() {
  const [location, setLocation] = useState(DEFAULT_LOCATION)
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
  const [howOpen, setHowOpen] = useState(false)
  const [activeSection, setActiveSection] = useState('top')

  const requestRef = useRef(0)
  const lastKeyRef = useRef('')
  const outputRef = useRef(null)
  const locationTouchedRef = useRef(false)
  const autoLocateRef = useRef(false)

  useEffect(() => {
    if (autoLocateRef.current || !navigator.geolocation) return
    autoLocateRef.current = true
    let active = true
    navigator.geolocation.getCurrentPosition(
      (position) => {
        if (!active || locationTouchedRef.current) return
        setLocation({
          lat: Number(position.coords.latitude.toFixed(4)),
          lon: Number(position.coords.longitude.toFixed(4)),
          label: 'My location',
        })
      },
      () => {},
      { enableHighAccuracy: false, timeout: 10000, maximumAge: 600000 },
    )
    return () => {
      active = false
    }
  }, [])

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
    locationTouchedRef.current = true
    setLocation(next)
  }

  const handleNavigate = (id) => {
    const target = document.getElementById(id) ? id : id === 'climate' ? 'compare' : 'top'
    setActiveSection(target)
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
    setLocation(DEFAULT_LOCATION)
    setForm(INITIAL_FORM)
    setUsingDemo(!hasBackend)
    setStatus('idle')
    setResults(null)
    setError(null)
    setClimate(null)
    setClimateStatus('idle')
    setRefreshing(false)
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
            <section className="hero" id="top">
              <img className="hero__img" src="/img/maize-sunset.jpg" alt="" />
              <div className="hero__shade" aria-hidden="true" />
              <div className="hero__body">
                <p className="hero__eyebrow">NASA Space Apps 2026 · Field Shift</p>
                <h1>Find the best rotation for your farm.</h1>
                <p>Pick a field. Set priorities. See what fits.</p>
              </div>
              <div className="hero__nasa">
                <span className="hero__nasa-ball">NASA</span>
                <span>
                  NASA data
                  <b>Powered</b>
                </span>
                <BadgeCheck className="icon" aria-hidden="true" />
              </div>
            </section>

            <div className="workspace">
              <SetupPanel
                locations={locations}
                location={location}
                onLocationChange={handleLocationChange}
                form={form}
                setForm={setForm}
                crops={crops}
              />

              <div className="output" id="compare" ref={outputRef} aria-live="polite">
                {status === 'idle' ? (
                  <EmptyState hasLocation={Boolean(location)} running={busy} onRun={handleRun} />
                ) : (
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
                )}
              </div>
            </div>

            <section className="method" id="about">
              <div>
                <p className="eyebrow">Score guide</p>
                <h2>Scored the same way.</h2>
                <p>NASA climate + crop rules + your priorities.</p>
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
