import { useEffect, useState } from 'react'
import { Info } from 'lucide-react'
import Header from './components/Header'
import Footer from './components/Footer'
import Stepper from './components/Stepper'
import LocationStep from './components/LocationStep'
import ProfileStep from './components/ProfileStep'
import ResultsStep from './components/ResultsStep'
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

const PAGE_META = [
  {
    eyebrow: 'Step 1 · Field location',
    title: 'Start with the field, not the crop.',
    text: 'Choose a location. AgroOrbit pulls the NASA climate record for that point and turns it into growing-season indicators you can inspect.',
  },
  {
    eyebrow: 'Step 2 · Farm profile',
    title: 'Tell us how you farm and what matters.',
    text: 'Your current rotation, optional soil notes and priorities shape the comparison. Only the rotation is required.',
  },
  {
    eyebrow: 'Step 3 · Comparison',
    title: 'Compare rotations on the same evidence.',
    text: 'Every strategy is judged with the same NASA record and rules. Open the evidence on any card to see the metric behind each claim.',
  },
]

const SCOPE =
  'AgroOrbit is designed for global environmental analysis, with its initial agricultural knowledge base focused on Nigeria’s northern savanna and Middle Belt. Recommendations outside that region are not validated.'

export default function App() {
  const [step, setStep] = useState(0)
  const [location, setLocation] = useState(null)
  const [form, setForm] = useState(INITIAL_FORM)
  const [crops, setCrops] = useState(CROPS)
  const [locations, setLocations] = useState(LOCATIONS)
  const [usingDemo, setUsingDemo] = useState(!hasBackend)

  useEffect(() => {
    let active = true
    const client = hasBackend && !usingDemo ? api : mockApi
    Promise.all([client.getLocations(), client.getCrops()])
      .then(([nextLocations, nextCrops]) => {
        if (!active) return
        if (Array.isArray(nextLocations)) setLocations(nextLocations)
        if (Array.isArray(nextCrops)) setCrops(nextCrops)
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

  useEffect(() => {
    window.scrollTo(0, 0)
  }, [step])

  const restart = () => {
    setStep(0)
    setLocation(null)
    setForm(INITIAL_FORM)
    setUsingDemo(!hasBackend)
  }

  const meta = PAGE_META[step]

  return (
    <div className="app-shell">
      <Header mode={usingDemo ? 'demo' : 'live'} onHome={restart} />

      <main className="page">
        <div className="container">
          <Stepper current={step} canGo={(index) => index < step} onNavigate={setStep} />

          <div className="page-intro">
            <p className="eyebrow">{meta.eyebrow}</p>
            <h1>{meta.title}</h1>
            <p>{meta.text}</p>
            {step === 0 ? (
              <div className="scope-note">
                <Info className="icon" aria-hidden="true" />
                <span>{SCOPE}</span>
              </div>
            ) : null}
          </div>

          {step === 0 ? (
            <LocationStep
              value={location}
              locations={locations}
              onChange={setLocation}
              onContinue={() => {
                if (location) setStep(1)
              }}
            />
          ) : null}

          {step === 1 ? (
            <ProfileStep
              form={form}
              setForm={setForm}
              crops={crops}
              location={location}
              onBack={() => setStep(0)}
              onSubmit={() => setStep(2)}
            />
          ) : null}

          {step === 2 && location ? (
            <ResultsStep
              location={location}
              form={form}
              crops={crops}
              usingDemo={usingDemo}
              onUseDemo={() => setUsingDemo(true)}
              onBack={() => setStep(1)}
              onRestart={restart}
            />
          ) : null}
        </div>
      </main>

      <Footer />
    </div>
  )
}
