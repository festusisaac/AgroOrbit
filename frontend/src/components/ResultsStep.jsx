import { lazy, Suspense, useEffect, useState } from 'react'
import {
  AlertTriangle,
  ArrowLeft,
  CheckCircle2,
  CloudSun,
  Info,
  ListChecks,
  RotateCcw,
  ServerCog,
} from 'lucide-react'
import { api, mockApi } from '../api/client'
import { cropName } from '../api/mockData'
import RotationCard from './RotationCard'
import { ErrorState, LoadingState } from './StatusStates'

const ClimateView = lazy(() => import('./ClimateView'))

const OUTCOME = {
  clear_leader: {
    tone: 'leader',
    icon: CheckCircle2,
    title: 'A stronger option emerges',
    text: 'The top strategy leads on the evidence and your priorities. Review the details, then confirm with local advice.',
  },
  similar_options: {
    tone: 'similar',
    icon: Info,
    title: 'Options are close',
    text: 'The leading strategies score within a few points. Treat them as similar options and choose with local knowledge.',
  },
  no_clear_winner: {
    tone: 'none',
    icon: AlertTriangle,
    title: 'No clear winner yet',
    text: 'None of the evaluated strategies has enough supporting evidence for a confident recommendation. Additional local soil and agronomic information is needed.',
  },
}

export default function ResultsStep({ location, form, crops, usingDemo, onUseDemo, onBack, onRestart }) {
  const [tab, setTab] = useState('recommend')
  const [rec, setRec] = useState({ status: 'loading' })
  const [climate, setClimate] = useState({ status: 'loading' })
  const [recRetry, setRecRetry] = useState(0)
  const [climateRetry, setClimateRetry] = useState(0)

  const client = usingDemo ? mockApi : api
  const scenario = form.scenario || { rainfall_change_pct: 0, temperature_change_c: 0 }
  const scenarioActive =
    Number(scenario.rainfall_change_pct) !== 0 || Number(scenario.temperature_change_c) !== 0

  const cropNameById = (id) => crops.find((c) => c.id === id)?.name || cropName(id)

  useEffect(() => {
    let active = true
    setRec({ status: 'loading' })
    client
      .postRecommend({
        lat: location.lat,
        lon: location.lon,
        current_rotation: form.current_rotation,
        soil: form.soil,
        priorities: form.priorities,
        preferred_crops: form.preferred_crops,
        scenario,
      })
      .then((data) => {
        if (active) setRec({ status: 'ready', data })
      })
      .catch((error) => {
        if (active) setRec({ status: 'error', error })
      })
    return () => {
      active = false
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [location.lat, location.lon, form, usingDemo, recRetry])

  useEffect(() => {
    let active = true
    setClimate({ status: 'loading' })
    client
      .getClimate(location.lat, location.lon)
      .then((data) => {
        if (active) setClimate({ status: 'ready', data })
      })
      .catch((error) => {
        if (active) setClimate({ status: 'error', error })
      })
    return () => {
      active = false
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [location.lat, location.lon, usingDemo, climateRetry])

  const data = rec.status === 'ready' ? rec.data : null
  const outcome = data ? OUTCOME[data.overall_outcome] || OUTCOME.similar_options : null
  const OutcomeIcon = outcome?.icon
  const rotations = data?.rotations || []
  const byId = Object.fromEntries(rotations.map((r) => [r.id, r]))
  const tracePeriod = rotations[0]?.trace?.climate_period

  return (
    <>
      <div className="tabs" role="tablist" aria-label="Results views">
        <button
          type="button"
          className="tab"
          role="tab"
          aria-selected={tab === 'recommend'}
          onClick={() => setTab('recommend')}
        >
          <ListChecks className="icon" aria-hidden="true" />
          Recommendations
        </button>
        <button
          type="button"
          className="tab"
          role="tab"
          aria-selected={tab === 'climate'}
          onClick={() => setTab('climate')}
        >
          <CloudSun className="icon" aria-hidden="true" />
          Climate view
          <span className="tab__label-extra">for this field</span>
        </button>
      </div>

      {usingDemo ? (
        <div className="callout" style={{ marginBottom: '1rem' }}>
          <ServerCog className="icon" aria-hidden="true" />
          <div>
            Showing built-in demo data shaped exactly like the API contract. Set{' '}
            <code>VITE_API_BASE_URL</code> to the FastAPI server to switch this view to live results.
          </div>
        </div>
      ) : null}

      {tab === 'recommend' ? (
        rec.status === 'loading' ? (
          <LoadingState
            live={!usingDemo}
            title="Waking up the field station…"
            text="Comparing rotations against the NASA climate record and your priorities."
          />
        ) : rec.status === 'error' ? (
          <ErrorState
            title="The comparison could not load"
            message={rec.error?.message || 'The server may be waking up or temporarily unavailable.'}
            onRetry={() => setRecRetry((n) => n + 1)}
            onUseDemo={!usingDemo ? onUseDemo : undefined}
          />
        ) : (
          <>
            <div className={`outcome outcome--${outcome.tone}`}>
              <span className="outcome__icon" aria-hidden="true">
                <OutcomeIcon className="icon" />
              </span>
              <div>
                <h2 className="outcome__title">{outcome.title}</h2>
                <p className="outcome__text">{data.outcome_message || outcome.text}</p>
              </div>
            </div>

            <div className="row row--wrap" style={{ marginBottom: '0.8rem' }}>
              <span className="chip chip--green">{rotations.length} strategies compared</span>
              <span className="chip">Sorted by score · climate {tracePeriod || '1991–2025'}</span>
              {scenarioActive ? (
                <span className="chip chip--amber">
                  Hypothetical scenario · rain {scenario.rainfall_change_pct > 0 ? '+' : ''}
                  {scenario.rainfall_change_pct}% · temp +{scenario.temperature_change_c} °C
                </span>
              ) : null}
            </div>

            <div className="results-stack">
              {rotations.map((rotation) => {
                const similarLabels = (rotation.similar_to || [])
                  .map((id) => byId[id])
                  .filter(Boolean)
                  .map((r) => r.sequence.map(cropNameById).join(' → '))
                return (
                  <RotationCard
                    key={rotation.id}
                    rotation={rotation}
                    highlight={rotation.rank === 1 && data.overall_outcome === 'clear_leader'}
                    similarLabels={similarLabels}
                  />
                )
              })}
            </div>

            <div className="disclaimer">
              <Info className="icon" aria-hidden="true" />
              <span>{data.disclaimer}</span>
            </div>
          </>
        )
      ) : climate.status === 'loading' ? (
        <LoadingState
          live={!usingDemo}
          title="Loading the climate indicators…"
          text="Turning the NASA POWER daily record into monthly and seasonal indicators."
        />
      ) : climate.status === 'error' ? (
        <ErrorState
          title="The climate view could not load"
          message={climate.error?.message || 'The server may be waking up or temporarily unavailable.'}
          onRetry={() => setClimateRetry((n) => n + 1)}
          onUseDemo={!usingDemo ? onUseDemo : undefined}
        />
      ) : (
        <Suspense
          fallback={
            <LoadingState
              title="Loading the charts…"
              text="Preparing the climate visualisations for this field."
            />
          }
        >
          <ClimateView climate={climate.data} />
        </Suspense>
      )}

      <div className="action-bar">
        <button type="button" className="btn btn-secondary" onClick={onBack}>
          <ArrowLeft className="icon" aria-hidden="true" />
          Edit farm profile
        </button>
        <span className="spacer" />
        <button type="button" className="btn btn-ghost" onClick={onRestart}>
          <RotateCcw className="icon" aria-hidden="true" />
          Start over
        </button>
      </div>
    </>
  )
}
