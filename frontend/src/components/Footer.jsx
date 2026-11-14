export default function Footer() {
  return (
    <footer className="site-footer">
      <div className="container site-footer__grid">
        <div>
          <p>
            <strong>Scope.</strong> AgroOrbit is designed for global environmental analysis, with
            its initial agricultural knowledge base focused on Nigeria’s northern savanna and
            Middle Belt. Recommendations outside that region are not validated.  
          </p>
          <p>
            AgroOrbit supports decisions. It does not replace local farmer knowledge or
            agricultural advisers.
          </p>
        </div>
        <div>
          <p>
            <strong>Team Kepler's Kids</strong> · Luxembourg · NASA Space Apps Challenge 2026
          </p>
          <div className="footer-meta">
            <span>Challenge: Field Shift</span>
            <span>Climate: NASA POWER</span>
            <span>No accounts · No tracking</span>
          </div>
        </div>
      </div>
    </footer>
  )
}
