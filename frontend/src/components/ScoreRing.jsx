const RADIUS = 28
const CIRCUMFERENCE = 2 * Math.PI * RADIUS

export default function ScoreRing({ score, fit }) {
  const clamped = Math.max(0, Math.min(100, Number(score) || 0))
  const filled = (clamped / 100) * CIRCUMFERENCE
  return (
    <div
      className="score-ring"
      data-tone={fit}
      role="img"
      aria-label={`Score ${clamped} out of 100, ${fit} fit`}
    >
      <svg viewBox="0 0 68 68" aria-hidden="true">
        <circle className="score-ring__track" cx="34" cy="34" r={RADIUS} />
        <circle
          className="score-ring__fill"
          cx="34"
          cy="34"
          r={RADIUS}
          strokeDasharray={`${filled} ${CIRCUMFERENCE}`}
        />
      </svg>
      <span className="score-ring__value">
        <span className="score-ring__num">{clamped}</span>
        <span className="score-ring__cap">score</span>
      </span>
    </div>
  )
}
