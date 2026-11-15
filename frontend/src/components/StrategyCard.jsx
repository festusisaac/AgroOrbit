import { Fragment, useState } from 'react'
import {
  AlertTriangle,
  ArrowRight,
  Bug,
  CheckCircle2,
  ChevronDown,
  Droplets,
  Store,
  Sun,
  ThumbsUp,
  Trophy,
  UserCheck,
} from 'lucide-react'
import CropGlyph from './CropGlyph'
import RadarScore from './RadarScore'

const FIT = {
  strong: { label: 'Very good', icon: CheckCircle2 },
  moderate: { label: 'Good', icon: ThumbsUp },
  weak: { label: 'Fair', icon: AlertTriangle },
}

const RATINGS = [
  ['water_fit', 'Water', Droplets],
  ['heat_drought_resilience', 'Heat & dry', Sun],
  ['pest_break', 'Pests', Bug],
  ['market_preference_fit', 'Market', Store],
]

const LEVEL_BARS = { high: 3, medium: 2, low: 1 }

const scoreTone = (value) => (value >= 70 ? 'strong' : value >= 45 ? 'moderate' : 'weak')

const pretty = (text = '') =>
  text
    .replace(/_/g, ' ')
    .replace(/\b(maize|cowpea|sorghum|groundnut|pearl millet|soybean)\b/gi, (word) =>
      word.charAt(0).toUpperCase() + word.slice(1).toLowerCase(),
    )

function Rating({ icon: Icon, label, value }) {
  const pct = Math.max(0, Math.min(100, Number(value) || 0))
  const steps = Math.max(1, Math.round((pct / 100) * 3))
  const tone = scoreTone(pct)
  return (
    <div className="rate-row" data-tone={tone}>
      <span className="rate-row__icon" aria-hidden="true">
        <Icon className="icon" />
      </span>
      <span className="rate-row__label">{label}</span>
      <span className="rate-bars" aria-label={`${label}: ${steps} of 3`}>
        {[1, 2, 3].map((i) => (
          <i key={i} data-on={i <= steps} />
        ))}
      </span>
    </div>
  )
}

function Level({ label, level = 'low' }) {
  const filled = LEVEL_BARS[level] || 1
  return (
    <div className="level">
      <span className="level__label">{label}</span>
      <span className="level__value">{level}</span>
      <span className="level__bars" aria-hidden="true">
        {[1, 2, 3].map((i) => (
          <i key={i} data-on={i <= filled} />
        ))}
      </span>
    </div>
  )
}

export default function StrategyCard({ rotation, cropMap, isTop, delta }) {
  const [open, setOpen] = useState(false)
  const {
    label,
    sequence = [],
    score = 0,
    fit_category = 'weak',
    rank = 0,
    criteria = {},
    data_confidence = {},
    knowledge_support = {},
    why_suggested = '',
    evidence = [],
    benefits = [],
    information_gaps = [],
    risks_for_local_review = [],
    review_recommended_by = [],
  } = rotation

  const fit = FIT[fit_category] || FIT.weak
  const FitIcon = fit.icon

  return (
    <article className={`strategy ${isTop ? 'strategy--top' : ''}`}>
      <div className="strategy__top">
        <span className={`strategy__rank ${isTop ? 'strategy__rank--top' : ''}`}>
          {isTop ? <Trophy className="icon" aria-hidden="true" /> : null}
          {isTop ? 'Best choice' : `Option ${rank}`}
        </span>
        <span className={`fit-pill fit-pill--${fit_category}`}>
          <FitIcon className="icon" aria-hidden="true" />
          {fit.label}
        </span>
      </div>

      <div className="strategy__head">
        <h3 className="strategy__title">{pretty(label)}</h3>
        <div className="score-pill">
          <b>{Math.round(score)}</b>
          <span>/100</span>
        </div>
      </div>

      <div className="score-track" aria-hidden="true">
        <i data-tone={fit_category} style={{ width: `${Math.max(0, Math.min(100, score))}%` }} />
      </div>

      {typeof delta === 'number' && delta !== 0 ? (
        <span className={`delta ${delta > 0 ? 'delta--up' : 'delta--down'}`}>
          {delta > 0 ? <span aria-hidden="true">▲</span> : <span aria-hidden="true">▼</span>}
          {delta > 0 ? 'Better than what you grow now' : 'Below what you grow now'}
        </span>
      ) : null}

      <div className="seq" aria-label="Crop sequence">
        {sequence.map((cropId, index) => {
          const crop = cropMap[cropId]
          const legume = crop?.family === 'legume'
          return (
            <Fragment key={`${cropId}-${index}`}>
              {index > 0 ? <ArrowRight className="seq__arrow" aria-hidden="true" /> : null}
              <span className={`crop-tile ${legume ? 'crop-tile--legume' : 'crop-tile--cereal'}`}>
                <CropGlyph id={cropId} />
                <small>{crop?.name || cropId}</small>
              </span>
            </Fragment>
          )
        })}
      </div>

      <div className="rating-list">
        {RATINGS.map(([key, name, Icon]) => (
          <Rating key={key} icon={Icon} label={name} value={criteria[key]} />
        ))}
      </div>

      <button
        type="button"
        className="details-toggle"
        aria-expanded={open}
        onClick={() => setOpen((v) => !v)}
      >
        {open ? 'Hide' : 'Why this one?'}
        <ChevronDown className="icon" aria-hidden="true" />
      </button>

      {open ? (
        <div className="strategy__details">
          {why_suggested ? <p className="strategy__why">{why_suggested}</p> : null}

          <div className="strategy__profile">
            <RadarScore criteria={criteria} tone={fit_category} />
            <div className="strategy__levels">
              <Level label="Data" level={data_confidence.level} />
              <Level label="Knowledge" level={knowledge_support.level} />
            </div>
          </div>

          {evidence.length ? (
            <div className="ev-list">
              {evidence.map((item, index) => (
                <div className="ev-row" key={index}>
                  <div className="ev-row__head">
                    <span>{item.metric}</span>
                    <em>{item.source}</em>
                  </div>
                  <p>
                    {item.value} — {item.meaning}
                  </p>
                </div>
              ))}
            </div>
          ) : null}

          <div className="mini-cols">
            <div>
              <h4>Helps</h4>
              <ul>
                {benefits.slice(0, 3).map((item, index) => (
                  <li key={index}>{item}</li>
                ))}
              </ul>
            </div>
            <div className="warn">
              <h4>Watch</h4>
              <ul>
                {[...information_gaps, ...risks_for_local_review].slice(0, 4).map((item, index) => (
                  <li key={index}>{item}</li>
                ))}
              </ul>
            </div>
          </div>

          {review_recommended_by.length ? (
            <div className="review-line">
              <UserCheck className="icon" aria-hidden="true" />
              Review with {review_recommended_by.join(' · ')}
            </div>
          ) : null}
        </div>
      ) : null}
    </article>
  )
}
