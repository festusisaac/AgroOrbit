import { AlertTriangle, CloudOff, RefreshCw, ServerCog } from 'lucide-react'

export function LoadingState({ title = 'Waking up the field station…', text, live = false }) {
  return (
    <div className="state" role="status" aria-live="polite">
      <span className="spinner" aria-hidden="true" />
      <h3 className="state__title" style={{ marginTop: '0.9rem' }}>
        {title}
      </h3>
      <p className="state__text">
        {text ||
          (live
            ? 'Free hosting can take 30–60 seconds to wake up on the first request. Thanks for waiting.'
            : 'Pulling the climate indicators and comparing rotations.')}
      </p>
    </div>
  )
}

export function ErrorState({
  title = 'We could not load this view',
  message = 'The server may be waking up or temporarily unavailable.',
  onRetry,
  onUseDemo,
  retrying = false,
}) {
  return (
    <div className="state state--error" role="alert">
      <span className="state__icon" aria-hidden="true">
        <CloudOff className="icon" />
      </span>
      <h3 className="state__title">{title}</h3>
      <p className="state__text">{message}</p>
      <div className="state__actions">
        {onRetry ? (
          <button type="button" className="btn btn-secondary" onClick={onRetry} disabled={retrying}>
            <RefreshCw className="icon" aria-hidden="true" />
            {retrying ? 'Retrying…' : 'Try again'}
          </button>
        ) : null}
        {onUseDemo ? (
          <button type="button" className="btn btn-ghost" onClick={onUseDemo}>
            <ServerCog className="icon" aria-hidden="true" />
            Use demo data instead
          </button>
        ) : null}
      </div>
    </div>
  )
}

export function InlineNotice({ children }) {
  return (
    <div className="callout">
      <AlertTriangle className="icon" aria-hidden="true" />
      <div>{children}</div>
    </div>
  )
}
