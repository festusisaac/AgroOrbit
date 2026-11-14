export default function BrandMark({ className = 'brand__mark' }) {
  return (
    <svg className={className} viewBox="0 0 40 40" fill="none" aria-hidden="true">
      <ellipse
        cx="20"
        cy="20"
        rx="17"
        ry="6.4"
        transform="rotate(-32 20 20)"
        stroke="#2c5c40"
        strokeWidth="1.2"
        opacity="0.5"
      />
      <circle cx="20" cy="20" r="11" stroke="#2c5c40" strokeWidth="1.1" opacity="0.2" />
      <circle cx="29.6" cy="9.4" r="1.9" fill="#2c5c40" />
      <path d="M20 29c0-5.6 3.1-9.6 8.6-11.4-.8 6.4-3.3 9.8-8.6 11.4Z" fill="#387151" />
      <path d="M19.4 31c-5.8-.7-9-3.8-10-9.4 6.3.7 9.4 3.7 10 9.4Z" fill="#9fbfa4" />
      <path d="M20 30.5v-7.6" stroke="#1d3b29" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  )
}
