import { Satellite } from 'lucide-react'
import BrandMark from './BrandMark'

export default function Header({ mode, onHome }) {
  const demo = mode !== 'live'
  return (
    <>
      <div className="topline">
        <div className="container topline__inner">
          <span>Team Kepler’s Kids</span>
          <span className="topline__sep" aria-hidden="true" />
          <span>NASA Space Apps 2026</span>
          <span className="spacer" />
          <span className="topline__right topline__right--long">
            Challenge · Field Shift: Adapting Farms with NASA Data
          </span>
          <span className="topline__right">Luxembourg</span>
        </div>
      </div>

      <header className="site-header">
        <div className="container site-header__inner">
          <a
            className="brand"
            href="/"
            onClick={(e) => {
              e.preventDefault()
              onHome?.()
            }}
            aria-label="AgroOrbit home"
          >
            <BrandMark />
            <span>
              <span className="brand__name">AgroOrbit</span>
              <span className="brand__sub">Rotation planning with NASA data</span>
            </span>
          </a>

          <div className="site-header__meta">
            <span className="header-badge">
              <Satellite className="icon" style={{ width: 13, height: 13 }} aria-hidden="true" />
              Field Shift
            </span>
            <span
              className={`mode-chip ${demo ? 'mode-chip--demo' : 'mode-chip--live'}`}
              title={
                demo
                  ? 'Showing built-in demo responses that match the API contract.'
                  : 'Connected to the live AgroOrbit backend.'
              }
            >
              <span className="dot" aria-hidden="true" />
              {demo ? 'Demo data' : 'Live API'}
            </span>
          </div>
        </div>
      </header>
    </>
  )
}
