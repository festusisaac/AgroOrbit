import {
  ArrowRight,
  ChevronDown,
  ClipboardList,
  Database,
  Lightbulb,
  ShieldAlert,
  Sprout,
  UserCheck,
} from 'lucide-react'
import ScoreRing from './ScoreRing'
import Term from './Term'
import { cropName } from '../api/mockData'

const CRITERIA_META = [
  { key: 'water_fit', label: 'Water fit' },
  { key: 'season_fit', label: 'Season fit' },
  { key: 'heat_drought_resilience', label: 'Heat & drought resilience' },
  { key: 'soil_health', label: 'Soil health' },
  { key: 'pest_break', label: 'Pest break' },
  { key: 'erosion_protection', label: 'Erosion protection' },
  { key: 'market_preference_fit', label: 'Market preference fit' },
  { key: 'forage_value', label: 'Forage value' },
]

const SOURCE_CLASS = {
  'NASA POWER': 'source-tag--nasa',
  'Farmer input': 'source-tag--input',
  'Crop knowledge base': 'source-tag--knowledge',
}

const toneFor = (value) => (value >= 70 ? 'strong' : value >= 50 ? 'moderate' : 'weak')

function LevelChip({ level }) {
  return (
    <span className="level-chip" data-level={level}>
      {level}
    </span>
  )
}

function RotationList({ items, tone, icon: Icon, title }) {
  if (!items || items.length === 0) return null
  return (
    <div className="list-block">
      <div className="subhead">
        <Icon className="icon" aria-hidden="true" />
        {title}
      </div>
      <ul>
        {items.map((item, index) => (
          <li key={index}>{item}</li>
        ))}
      </ul>
    </div>
  )
}

export default function RotationCard({ rotation, highlight, similarLabels = [] }) {
  const {
    label = 'Strategy',
    sequence = [],
    score = 0,
    fit_category = 'weak',
    rank = 0,
    is_existing = false,
    criteria = {},
    data_confidence = { level: 'low', reasons: [] },
    knowledge_support = { level: 'low', reasons: [] },
    why_suggested = '',
    evidence = [],
    benefits = [],
    assumptions = [],
    information_gaps = [],
    risks_for_local_review = [],
    review_recommended_by = [],
    trace = {},
  } = rotation

  return (
    <article
      className={`rotation-card ${highlight ? 'rotation-card--top' : ''} ${
        is_existing ? 'rotation-card--existing' : ''
      }`}
      aria-label={`Rank ${rank}: ${label}`}
    >
      <header className="rotation-card__head">
        <span className="rank" aria-label={`Rank ${rank}`}>
          #{rank}
        </span>
        <div className="rotation-card__heading">
          <p className="rotation-card__eyebrow">
            {is_existing ? 'Your current rotation' : 'Alternative strategy'}
          </p>
          <h3 className="rotation-card__title">{label}</h3>
          <div className="rotation-card__sequence" aria-label="Crop sequence">
            {sequence.map((cropId, index) => (
              <span key={`${cropId}-${index}`} style={{ display: 'inline-flex', alignItems: 'center', gap: '0.3rem' }}>
                {index > 0 ? <ArrowRight className="seq-arrow" aria-hidden="true" /> : null}
                <span className="seq-crop">{cropName(cropId)}</span>
              </span>
            ))}
          </div>
          <div className="rotation-card__chips">
            <span className="fit-chip" data-tone={fit_category}>
              {fit_category}
            </span>
            {similarLabels.length ? (
              <span className="chip" title="Scores are within 5 points; the tool does not imply a winner.">
                <Term k="similar">Similar to {similarLabels.join(', ')}</Term>
              </span>
            ) : null}
            {is_existing ? <span className="chip">Baseline</span> : null}
          </div>
        </div>
        <ScoreRing score={score} fit={fit_category} />
      </header>

      <div className="rotation-card__body">
        <div className="rotation-main">
          <div className="why-block">
            <div className="why-label">
              <Lightbulb className="icon" aria-hidden="true" />
              Why this appears
            </div>
            {why_suggested}
          </div>

          <details className="evidence">
            <summary>
              <Database className="icon" aria-hidden="true" />
              Evidence behind this recommendation
              <span className="evidence__count">{evidence.length}</span>
              <ChevronDown className="icon evidence__chevron" aria-hidden="true" />
            </summary>
            <div className="evidence__body">
              {evidence.map((item, index) => (
                <div className="evidence-item" key={index}>
                  <div className="evidence-item__top">
                    <span className={`source-tag ${SOURCE_CLASS[item.source] || ''}`}>
                      {item.source}
                    </span>
                    <span className="evidence-item__metric">{item.metric}</span>
                    <span className="spacer" />
                    <span className="evidence-item__value">{item.value}</span>
                  </div>
                  <p className="evidence-item__meaning">{item.meaning}</p>
                </div>
              ))}
            </div>
          </details>

          <RotationList items={benefits} icon={Sprout} title="Benefits" />
          <div className="list-block list-block--gap">
            <div className="subhead">
              <ClipboardList className="icon" aria-hidden="true" />
              Information gaps
            </div>
            <ul>
              {information_gaps.map((item, index) => (
                <li key={index}>{item}</li>
              ))}
            </ul>
          </div>
          <div className="list-block list-block--risk">
            <div className="subhead">
              <ShieldAlert className="icon" aria-hidden="true" />
              Risks needing local review
            </div>
            <ul>
              {risks_for_local_review.map((item, index) => (
                <li key={index}>{item}</li>
              ))}
            </ul>
          </div>

          {review_recommended_by.length ? (
            <div className="review-note">
              <UserCheck className="icon" aria-hidden="true" />
              <span>
                Recommended review by: <strong>{review_recommended_by.join(' · ')}</strong>
              </span>
            </div>
          ) : null}
        </div>

        <aside className="rotation-side">
          <div className="conf-block">
            <div className="conf-block__head">
              <span className="conf-block__name">
                <Term k="data_confidence">Data confidence</Term>
              </span>
              <LevelChip level={data_confidence.level} />
            </div>
            <ul className="conf-reasons">
              {(data_confidence.reasons || []).map((reason, index) => (
                <li key={index}>{reason}</li>
              ))}
            </ul>
          </div>

          <div className="conf-block">
            <div className="conf-block__head">
              <span className="conf-block__name">
                <Term k="knowledge_support">Knowledge support</Term>
              </span>
              <LevelChip level={knowledge_support.level} />
            </div>
            <ul className="conf-reasons">
              {(knowledge_support.reasons || []).map((reason, index) => (
                <li key={index}>{reason}</li>
              ))}
            </ul>
          </div>

          <hr className="divider" />

          <div className="subhead">
            <ClipboardList className="icon" aria-hidden="true" />
            Criteria breakdown
          </div>
          <div className="criteria">
            {CRITERIA_META.map(({ key, label: criterionLabel }) => {
              const value = Math.round(Number(criteria[key] ?? 0))
              return (
                <div className="criterion" key={key}>
                  <div className="criterion__top">
                    <span className="criterion__name">{criterionLabel}</span>
                    <span className="criterion__val">{value}</span>
                  </div>
                  <div className="bar">
                    <div
                      className="bar__fill"
                      data-tone={toneFor(value)}
                      style={{ width: `${Math.max(0, Math.min(100, value))}%` }}
                    />
                  </div>
                </div>
              )
            })}
          </div>

          <details className="trace">
            <summary>Assumptions &amp; trace</summary>
            <ul className="conf-reasons" style={{ marginTop: '0.4rem' }}>
              {assumptions.map((item, index) => (
                <li key={index}>{item}</li>
              ))}
            </ul>
            <pre>{JSON.stringify(trace, null, 2)}</pre>
          </details>
        </aside>
      </div>
    </article>
  )
}
