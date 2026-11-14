import {
  BookOpen,
  CloudSun,
  LayoutDashboard,
  Leaf,
  MapPin,
  Sprout,
} from 'lucide-react'
import BrandMark from './BrandMark'

const NAV = [
  { icon: LayoutDashboard, label: 'Dashboard', id: 'top', href: '#top' },
  { icon: MapPin, label: 'Field', id: 'field', href: '#field' },
  { icon: Sprout, label: 'Compare', id: 'compare', href: '#compare' },
  { icon: CloudSun, label: 'Climate', id: 'climate', href: '#climate' },
  { icon: BookOpen, label: 'About', id: 'about', href: '#about' },
]

export default function Sidebar({ active = 'top', onNavigate }) {
  return (
    <aside className="sidebar">
      <a
        className="sidebar__brand"
        href="#top"
        onClick={(e) => {
          e.preventDefault()
          onNavigate?.('top')
        }}
      >
        <span className="sidebar__logo">
          <BrandMark />
        </span>
        <span>
          <b>AgroOrbit</b>
          <small>Smarter Farming.<br />Brighter Tomorrow.</small>
        </span>
      </a>

      <nav className="sidebar__nav" aria-label="Sections">
        {NAV.map(({ icon: Icon, label, id, href }) => (
          <a
            key={label}
            href={href}
            className={active === id ? 'is-active' : ''}
            onClick={(e) => {
              e.preventDefault()
              onNavigate?.(id)
            }}
          >
            <Icon className="icon" aria-hidden="true" />
            {label}
          </a>
        ))}
      </nav>

      <div className="sidebar__spacer" />

      <img className="sidebar__art" src="/img/farmer-tablet.jpg" alt="" />

      <div className="sidebar__note">
        <Leaf className="icon" aria-hidden="true" />
        <span>Supports decisions. It does not replace local advice.</span>
      </div>
    </aside>
  )
}
