import { AlertTriangle, ArrowRight, CheckCircle2, Info, Loader2, RefreshCw, ServerCog } from 'lucide-react'
import ClimatePanel from './ClimatePanel'
import StrategyCard from './StrategyCard'

const OUTCOME = {
  clear_leader: {
    title: 'A stronger rotation emerges.',
    text: 'It leads on your priorities and this climate record.',
  },
  similar_options: {
    title: 'The top options are close.',
    text: 'Choose the one that fits your farm and market.',
  },
  no_clear_winner: {
    title: 'No clear winner yet.',
    text: 'Add soil details or ask a local adviser.',
  },
}

function LoadingView({ location }) {
  return (
    <div className="loading-card">
      <div className="spinner" />
      <h2>Reading the climate record…</h2>
      <p>Comparing rotations for {location?.label || 'this field'}.</p>
      <div className="loading-steps">
        <span>
          <CheckCircle2 className="icon" aria-hidden="true" />
          NASA POWER
        </span>
        <span>
          <CheckCircle2 className="icon" aria-hidden="true" />
          Crop rules
        </span>
        <span>
          <CheckCircle2 className="icon" aria-hidden="true" />
          Your priorities
        </span>
      </div>
    </div>
  )
}

function ErrorView({ message, onRetry, onUseDemo }) {
  return (
    <div className="error-card">
      <span className="error-card__icon" aria-hidden="true">
        <AlertTriangle className="icon" />
      </span>
      <h2>Could not load the comparison.</h2>
      <p>{message || 'The server may be unavailable.'}</p>
      <div className="error-card__actions">
        <button type="button" className="btn btn-primary" onClick={onRetry}>
          <RefreshCw className="icon" aria-hidden="true" />
          Try again
        </button>
        {onUseDemo ? (
          <button type="button" className="btn btn-secondary" onClick={onUseDemo}>
            <ServerCog className="icon" aria-hidden="true" />
            Use demo data
          </button>
        ) : null}
      </div>
    </div>
  )
}

export default function ResultsView({
  status,
  data,
  error,
  climate,
  climateStatus,
  location,
  crops,
  usingDemo,
  refreshing,
  onRetry,
  onUseDemo,
}) {
  if (status === 'loading') return <LoadingView location={location} />
  if (status === 'error') {
    return <ErrorView message={error?.message} onRetry={onRetry} onUseDemo={usingDemo ? null : onUseDemo} />
  }
  if (!data) return null

  const cropMap = Object.fromEntries(crops.map((c) => [c.id, c]))
  const rotations = data.rotations || []
  const existing = rotations.find((r) => r.is_existing)
  const alternatives = rotations.filter((r) => !r.is_existing)
  const options = alternatives.length ? alternatives : rotations
  const baselineScore = existing?.score
  const period = rotations[0]?.trace?.climate_period || '1991–2023'
  const outcome = OUTCOME[data.overall_outcome] || OUTCOME.similar_options

  return (
    <div>
      <div className="results-topline">
        <span className="tag">{rotations.length} rotations</span>
        <span className="tag tag--mono">{period}</span>
        {usingDemo ? <span className="tag tag--amber">Demo data</span> : null}
        {refreshing ? (
          <span className="tag">
            <Loader2 className="icon spin" aria-hidden="true" />
            Updating…
          </span>
        ) : null}
      </div>

      <div className="rec-banner">
        <span className="rec-banner__icon" aria-hidden="true">
          <CheckCircle2 className="icon" />
        </span>
        <div className="rec-banner__body">
          <h2>{outcome.title}</h2>
          <p>{data.outcome_message || outcome.text}</p>
        </div>
        <a className="btn btn-banner" href="#climate">
          Climate details
          <ArrowRight className="icon" aria-hidden="true" />
        </a>
      </div>

      <div className="strategy-grid">
        {options.map((rotation) => (
          <StrategyCard
            key={rotation.id}
            rotation={rotation}
            cropMap={cropMap}
            isTop={rotation.rank === 1}
            delta={typeof baselineScore === 'number' ? rotation.score - baselineScore : undefined}
          />
        ))}
      </div>

      {existing ? (
        <div className="baseline">
          <div className="baseline__label">Current rotation</div>
          <div className="baseline__seq">
            {existing.sequence.map((id, index) => (
              <span key={`${id}-${index}`} style={{ display: 'inline-flex', alignItems: 'center', gap: 3 }}>
                {index > 0 ? <span aria-hidden="true">→</span> : null}
                {cropMap[id]?.name || id}
              </span>
            ))}
          </div>
          <div className="baseline__score">
            {Math.round(existing.score)}
            <small>/100</small>
          </div>
          <span className={`tag ${existing.fit_category === 'weak' ? 'tag--red' : 'tag--amber'}`}>
            {existing.fit_category === 'strong'
              ? 'Strong fit'
              : existing.fit_category === 'moderate'
                ? 'Moderate'
                : 'Weak fit'}
          </span>
        </div>
      ) : null}

      <ClimatePanel climate={climate} status={climateStatus} location={location} />

      <p className="disclaimer">
        <Info className="icon" aria-hidden="true" />
        {data.disclaimer || 'Supports decisions. Does not replace local advice.'}
      </p>
    </div>
  )
}
