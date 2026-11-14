import BrandMark from './BrandMark'

export default function Footer() {
  return (
    <footer className="footer">
      <div className="container footer__inner">
        <div>
          <div className="footer__brand">
            <BrandMark />
            AgroOrbit
          </div>
          <p>
            <strong>Field Shift</strong> · NASA Space Apps Challenge 2026
          </p>
        </div>
        <div>
          <div className="footer__meta">
            <span>NASA POWER</span>
            <span>FAO-adapted rules</span>
            <span>Open source</span>
          </div>
          <p className="hint" style={{ marginTop: '0.4rem' }}>
            Supports decisions. Does not replace local advice.
          </p>
        </div>
      </div>
    </footer>
  )
}
