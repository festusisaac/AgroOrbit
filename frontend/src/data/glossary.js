export const GLOSSARY = {
  onset:
    'When the rainy season is judged to start, using a simplified rule (3-day rainfall and a 7-day dry-spell check). Indicative, not an official definition.',
  cessation:
    'When the rainy season is judged to end: the last 5-day window with at least 15 mm of rain. A short dry spell does not end the season if rain returns later.',
  season_length:
    'Days between the estimated onset and cessation. A planning indicator, not a guarantee for any single year.',
  fit_category:
    'A band for the score: strong (75+), moderate (55–74), weak (below 55). It summarises fit, not a guarantee.',
  score:
    'A 0–100 ordering value from the weighted criteria. It helps compare options; it is not a probability or a yield estimate.',
  data_confidence:
    'How complete and reliable the climate record and your inputs are for this location.',
  knowledge_support:
    'How much of the crop knowledge used here has been checked against published sources. Low means treat results as a starting point.',
  regional_wetness:
    'A gridded NASA estimate for the surrounding region. It is not a measurement of water in your field.',
  dry_spell:
    'A run of days with less than 1 mm of rain. A long spell during flowering can reduce yields.',
  heat_stress:
    'Days above the crop heat threshold (35 °C by default) during the growing window.',
  percentiles:
    'Typical outcomes: P20 is a drier-than-usual year (1 in 5), P50 is the middle year, P80 is a wetter-than-usual year.',
  bare_field:
    'Months when the ground is likely bare and low in moisture. Estimated from climate proxies, not satellite imagery.',
  market_fit:
    'How many of the rotation crops are on your preferred or sellable list. Not an income forecast.',
  season_fit:
    'How often the crop growing window fits inside the available rainy season.',
  water_fit:
    'How often rainfall during the crop window meets the crop water requirement without a critical dry spell.',
  feasibility:
    'If a crop cannot finish in most years, the strategy is capped at weak regardless of how it scores elsewhere.',
  similar:
    'These strategies score within 5 points. The tool does not imply one is better.',
  scenario:
    'A hypothetical change applied to the climate record. It is a sensitivity test, not a forecast.',
  evidence:
    'The actual metric behind a claim, labelled by source: NASA POWER, your input, or the crop knowledge base.',
}

export const CONFIDENCE_LABEL = {
  high: 'High',
  medium: 'Medium',
  low: 'Low',
}
