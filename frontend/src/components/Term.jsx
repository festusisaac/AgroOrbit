import { GLOSSARY } from '../data/glossary'

export default function Term({ k, children }) {
  const definition = GLOSSARY[k]
  if (!definition) return <>{children}</>
  return (
    <span
      className="term"
      tabIndex={0}
      role="note"
      aria-label={`${typeof children === 'string' ? children : 'Term'}: ${definition}`}
    >
      {children}
      <span className="term__tip" role="tooltip">
        {definition}
      </span>
    </span>
  )
}
