import { CloudSun, Home, MapPin, Sparkles, Sprout } from 'lucide-react'

const ITEMS = [
  { icon: Home, label: 'Home', id: 'top', href: '#top' },
  { icon: MapPin, label: 'Field', id: 'field', href: '#field' },
  { icon: Sparkles, label: 'Compare', id: 'compare', href: '#compare' },
  { icon: CloudSun, label: 'Climate', id: 'climate', href: '#climate' },
  { icon: Sprout, label: 'About', id: 'about', href: '#about' },
]

export default function MobileNav({ active = 'top', onNavigate }) {
  return (
    <nav className="mobilenav" aria-label="Sections">
      {ITEMS.map(({ icon: Icon, label, id, href }) => (
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
          <span>{label}</span>
        </a>
      ))}
    </nav>
  )
}
