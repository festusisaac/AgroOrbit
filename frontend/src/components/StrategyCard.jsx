import { Fragment, useState } from 'react'
import { ArrowRight, ChevronDown, Sprout, Trophy, UserCheck, Wheat } from 'lucide-react'
import RadarScore from './RadarScore'

const FIT_LABEL = {
  strong: 'Strong fit',
  moderate: 'Moderate fit',
  weak: 'Weak fit',
}

const LEVEL_BARS = { high: 3, medium: 2, low: 1 }

const pretty = (text = '') =>
  text
    .replace(/_/g, ' ')
    .replace(/\b(maize|cowpea|sorghum|groundnut|pearl millet|soybean)\b/gi, (word) =>
      word.charAt(0).toUpperCase() + word.slice(1).toLowerCase(),
    )

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

  return (
    <article className={`strategy ${isTop ? 'strategy--top' : ''}`}>
      <div className="strategy__top">
        <span className={`strategy__rank ${isTop ? 'strategy__rank--top' : ''}`}>
          {isTop ? <Trophy className="icon" aria-hidden="true" /> : null}
          {isTop ? '#1 Recommended' : `Option ${rank}`}
        </span>
        <span className={`fit-pill fit-pill--${fit_category}`}>{FIT_LABEL[fit_category] || fit_category}</span>
      </div>

      <div className="strategy__head">
        <h3 className="strategy__title">{pretty(label)}</h3>
        <div className="score-pill">
          <b>{Math.round(score)}</b>
          <span>/100</span>
        </div>
      </div>

      {typeof delta === 'number' && delta !== 0 ? (
        <span className={`delta ${delta > 0 ? 'delta--up' : 'delta--down'}`}>
          {delta > 0 ? '+' : ''}
          {Math.round(delta)} vs current
        </span>
      ) : null}

      <div className="seq" aria-label="Crop sequence">
        {sequence.map((cropId, index) => {
          const crop = cropMap[cropId]
          const legume = crop?.family === 'legume'
          const Icon = legume ? Sprout : Wheat
          return (
            <Fragment key={`${cropId}-${index}`}>
              {index > 0 ? <ArrowRight className="seq__arrow" aria-hidden="true" /> : null}
              <span className={`crop-tile ${legume ? 'crop-tile--legume' : 'crop-tile--cereal'}`}>
                <Icon className="icon" aria-hidden="true" />
                <small>{crop?.name || cropId}</small>
              </span>
            </Fragment>
          )
        })}
      </div>

      <RadarScore criteria={criteria} tone={fit_category} />

      <p className="strategy__why">{why_suggested}</p>

      <div className="strategy__levels">
        <Level label="Data" level={data_confidence.level} />
        <Level label="Knowledge" level={knowledge_support.level} />
      </div>

      <button
        type="button"
        className="details-toggle"
        aria-expanded={open}
        onClick={() => setOpen((v) => !v)}
      >
        {open ? 'Hide details' : 'Why this rotation?'}
        <ChevronDown className="icon" aria-hidden="true" />
      </button>

      {open ? (
        <div className="strategy__details">
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
