import { Check } from 'lucide-react'

const STEPS = [
  { id: 'location', label: 'Field location' },
  { id: 'profile', label: 'Farm profile' },
  { id: 'results', label: 'Compare rotations' },
]

export default function Stepper({ current, canGo, onNavigate }) {
  return (
    <nav className="stepper" aria-label="Progress">
      {STEPS.map((step, index) => {
        const state = index === current ? 'active' : index < current ? 'done' : 'upcoming'
        const interactive = state === 'done' && canGo?.(index)
        return (
          <button
            key={step.id}
            type="button"
            className="step"
            data-state={state}
            disabled={!interactive}
            aria-current={state === 'active' ? 'step' : undefined}
            onClick={interactive ? () => onNavigate?.(index) : undefined}
          >
            <span className="step__num" aria-hidden="true">
              {state === 'done' ? <Check className="icon" style={{ width: 13, height: 13 }} /> : index + 1}
            </span>
            <span className="step__label">{step.label}</span>
          </button>
        )
      })}
    </nav>
  )
}
