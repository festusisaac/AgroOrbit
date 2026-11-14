import { Sparkles } from 'lucide-react'

export default function EmptyState({ hasLocation, running, onRun }) {
  return (
    <div className="empty">
      <div className="empty__art">
        <img src="/img/farmer-tablet.jpg" alt="" />
      </div>
      <div className="empty__body">
        <p className="eyebrow">Your comparison</p>
        <h2>Pick a field. See what fits.</h2>
        <p>Results appear here.</p>
        <button
          type="button"
          className="btn btn-primary btn-lg"
          style={{ marginTop: '1rem', alignSelf: 'flex-start' }}
          onClick={onRun}
          disabled={!hasLocation || running}
        >
          <Sparkles className="icon" aria-hidden="true" />
          {running ? 'Comparing…' : 'Compare rotations'}
        </button>
      </div>
    </div>
  )
}
