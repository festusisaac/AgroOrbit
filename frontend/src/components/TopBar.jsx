import { HelpCircle, MapPin, Sprout } from 'lucide-react'
import BrandMark from './BrandMark'

export default function TopBar({ location, mode, onHowItWorks, onOpenOnboarding, onHome }) {
  const live = mode === 'live'
  return (
    <header className="topbar">
      <div className="container topbar__inner">
        <button type="button" className="brand topbar__brand" onClick={onHome} aria-label="AgroOrbit home">
          <BrandMark />
          <span>
            <span className="brand__name">AgroOrbit</span>
            <span className="brand__tag">Field Shift · NASA Space Apps</span>
          </span>
        </button>

        <span className="topbar__loc">
          <MapPin className="icon" aria-hidden="true" />
          {location ? (
            <>
              <span>{location.label || location.name || 'Selected field'}</span>
              <em>
                {Number(location.lat).toFixed(2)}, {Number(location.lon).toFixed(2)}
              </em>
            </>
          ) : (
            <span>No field selected</span>
          )}
        </span>

        <div className="topbar__actions">
          <button
            type="button"
            className="linkbtn"
            onClick={onOpenOnboarding}
            title="Edit farm profile & onboarding setup"
            style={{ fontWeight: 600, color: 'var(--green-700)', display: 'inline-flex', alignItems: 'center', gap: '0.35rem' }}
          >
            <Sprout className="icon" aria-hidden="true" />
            <span>Farm Setup</span>
          </button>
          <button type="button" className="linkbtn" onClick={onHowItWorks}>
            <HelpCircle className="icon" aria-hidden="true" />
            <span>How it works</span>
          </button>
          <span className={`status ${live ? 'status--live' : 'status--demo'}`}>
            <span className="status__dot" aria-hidden="true" />
            {live ? 'Live' : 'Demo'}
          </span>
          <span className="avatar" aria-hidden="true">AO</span>
        </div>
      </div>
    </header>
  )
}
