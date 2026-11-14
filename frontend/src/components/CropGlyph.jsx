const GLYPHS = {
  maize: (
    <g>
      <path d="M24 38c-3-4-3-11 0-16 3 5 3 12 0 16Z" fill="#5B8C3E" />
      <ellipse cx="24" cy="25" rx="8.5" ry="13" fill="#F5C542" stroke="#C9951F" strokeWidth="1.2" />
      <g fill="#FBE08A" stroke="#D9A300" strokeWidth="0.55">
        <circle cx="21" cy="17" r="1.5" />
        <circle cx="27" cy="17" r="1.5" />
        <circle cx="21" cy="22" r="1.5" />
        <circle cx="27" cy="22" r="1.5" />
        <circle cx="21" cy="27" r="1.5" />
        <circle cx="27" cy="27" r="1.5" />
        <circle cx="24" cy="31" r="1.5" />
      </g>
      <path d="M24 12c0-2 1-3 2-4" fill="none" stroke="#8A6200" strokeWidth="1.1" strokeLinecap="round" />
    </g>
  ),
  cowpea: (
    <g>
      <path d="M30 10c4-3 9-3 11 0-3 2-8 2-11 0Z" fill="#5B8C3E" />
      <g transform="rotate(-18 24 25)">
        <rect x="18" y="9" width="12" height="30" rx="6" fill="#7CB342" stroke="#4E7A23" strokeWidth="1.2" />
        <circle cx="24" cy="16" r="2.2" fill="#A5D66D" />
        <circle cx="24" cy="25" r="2.2" fill="#A5D66D" />
        <circle cx="24" cy="34" r="2.2" fill="#A5D66D" />
      </g>
    </g>
  ),
  sorghum: (
    <g>
      <path d="M24 42V22" stroke="#6B8F3C" strokeWidth="2" strokeLinecap="round" />
      <g fill="#D8A13A" stroke="#9A6A17" strokeWidth="0.6">
        <circle cx="20" cy="10" r="3" />
        <circle cx="26" cy="8" r="3" />
        <circle cx="30" cy="13" r="3" />
        <circle cx="17" cy="16" r="3" />
        <circle cx="24" cy="15" r="3.2" />
        <circle cx="31" cy="19" r="3" />
        <circle cx="20" cy="22" r="2.6" />
        <circle cx="27" cy="21" r="2.8" />
      </g>
    </g>
  ),
  groundnut: (
    <g>
      <g transform="rotate(-14 24 25)">
        <rect x="14" y="13" width="20" height="23" rx="9" fill="#C08A4B" stroke="#8A5A2B" strokeWidth="1.2" />
        <path
          d="M18 17c2 2 4 2 6 0M18 25c2 2 4 2 6 0M18 33c2 2 4 2 6 0"
          fill="none"
          stroke="#8A5A2B"
          strokeWidth="1"
          strokeLinecap="round"
        />
      </g>
    </g>
  ),
  pearl_millet: (
    <g>
      <path d="M24 42V20" stroke="#6B8F3C" strokeWidth="2" strokeLinecap="round" />
      <g fill="#A9B783" stroke="#6F7F4E" strokeWidth="0.55">
        <circle cx="20" cy="9" r="2.2" />
        <circle cx="26" cy="8" r="2.2" />
        <circle cx="29" cy="12" r="2.2" />
        <circle cx="17" cy="14" r="2.2" />
        <circle cx="23" cy="13" r="2.4" />
        <circle cx="29" cy="17" r="2.2" />
        <circle cx="20" cy="19" r="2.2" />
        <circle cx="26" cy="18" r="2.2" />
      </g>
    </g>
  ),
  soybean: (
    <g>
      <g transform="rotate(-14 24 25)">
        <rect x="16" y="10" width="16" height="28" rx="7" fill="#8BC34A" stroke="#558B2F" strokeWidth="1.2" />
        <circle cx="24" cy="17" r="2.4" fill="#C5E1A5" />
        <circle cx="24" cy="24" r="2.4" fill="#C5E1A5" />
        <circle cx="24" cy="31" r="2.4" fill="#C5E1A5" />
      </g>
      <path d="M31 9c3-2 7-2 9 0-3 1.5-6 1.5-9 0Z" fill="#5B8C3E" />
    </g>
  ),
}

export default function CropGlyph({ id, className = 'crop-glyph' }) {
  return (
    <svg viewBox="0 0 48 48" className={className} aria-hidden="true">
      {GLYPHS[id] || (
        <g>
          <path d="M24 40V22" stroke="#5B8C3E" strokeWidth="2" strokeLinecap="round" />
          <path d="M24 22c-8-2-10-9-8-15 8 1 11 7 8 15Z" fill="#7CB342" />
          <path d="M24 22c8-2 10-9 8-15-8 1-11 7-8 15Z" fill="#A5D66D" />
        </g>
      )}
    </svg>
  )
}
