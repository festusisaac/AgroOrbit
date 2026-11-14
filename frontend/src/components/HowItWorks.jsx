import { useEffect, useRef } from 'react'
import { MapPin, SlidersHorizontal, ScanSearch, X } from 'lucide-react'

const STEPS = [
  {
    icon: MapPin,
    title: 'Pick a field',
    text: 'Tap the map or choose a location.',
  },
  {
    icon: SlidersHorizontal,
    title: 'Set your priorities',
    text: 'Slide what matters most to you.',
  },
  {
    icon: ScanSearch,
    title: 'Compare rotations',
    text: 'See the score, the reason and the evidence.',
  },
]

export default function HowItWorks({ open, onClose }) {
  const ref = useRef(null)

  useEffect(() => {
    const dialog = ref.current
    if (!dialog) return
    if (open && !dialog.open) dialog.showModal()
    if (!open && dialog.open) dialog.close()
  }, [open])

  return (
    <dialog
      ref={ref}
      className="modal"
      onClose={onClose}
      onClick={(e) => {
        if (e.target === ref.current) onClose()
      }}
    >
      <div className="modal__head">
        <h2>How it works</h2>
        <button type="button" className="linkbtn" onClick={onClose} aria-label="Close">
          <X className="icon" aria-hidden="true" />
        </button>
      </div>
      <div className="modal__body">
        <ol className="how-list">
          {STEPS.map(({ icon: Icon, title, text }, index) => (
            <li key={title}>
              <span className="step-no" aria-hidden="true">
                {index + 1}
              </span>
              <div>
                <h3>{title}</h3>
                <p>{text}</p>
              </div>
              <Icon className="icon" style={{ marginLeft: 'auto' }} aria-hidden="true" />
            </li>
          ))}
        </ol>

        <div className="modal__scale">
          <div>
            <b>75–100</b>
            <span>Strong fit</span>
          </div>
          <div>
            <b>55–74</b>
            <span>Moderate</span>
          </div>
          <div>
            <b>0–54</b>
            <span>Weak fit</span>
          </div>
        </div>

        <p className="hint">
          NASA climate describes a grid cell, not your field. Confirm decisions with local advice.
        </p>
      </div>
    </dialog>
  )
}
