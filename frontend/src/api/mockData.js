// Mock responses shaped exactly like the frozen Section 9 API contract.
// Used from the first hour and whenever no live backend is configured.

export const LOCATIONS = [
  { id: 'kano', name: 'Kano', lat: 12.0022, lon: 8.5919, zone: 'Sudan savanna' },
  { id: 'kaduna', name: 'Kaduna', lat: 10.5222, lon: 7.4383, zone: 'Guinea savanna' },
  { id: 'jos', name: 'Jos', lat: 9.8965, lon: 8.8583, zone: 'Jos Plateau' },
  { id: 'makurdi', name: 'Makurdi', lat: 7.7322, lon: 8.5391, zone: 'Middle Belt' },
  { id: 'sokoto', name: 'Sokoto', lat: 13.0059, lon: 5.2476, zone: 'Sahel savanna' },
  { id: 'zaria', name: 'Zaria', lat: 11.0855, lon: 7.7199, zone: 'Sudan savanna' },
]

export const CROPS = [
  {
    id: 'maize',
    name: 'Maize',
    family: 'cereal',
    traits_summary: '~120 days · 500–800 mm · moderate heat tolerance',
    verified_share: 0.2,
  },
  {
    id: 'sorghum',
    name: 'Sorghum',
    family: 'cereal',
    traits_summary: '~100 days · 400–650 mm · strong drought tolerance',
    verified_share: 0.2,
  },
  {
    id: 'pearl-millet',
    name: 'Pearl millet',
    family: 'cereal',
    traits_summary: '~85 days · 300–500 mm · very strong drought tolerance',
    verified_share: 0.2,
  },
  {
    id: 'cowpea',
    name: 'Cowpea',
    family: 'legume',
    traits_summary: '~75 days · 300–500 mm · nitrogen-fixing',
    verified_share: 0.2,
  },
  {
    id: 'groundnut',
    name: 'Groundnut',
    family: 'legume',
    traits_summary: '~110 days · 450–700 mm · nitrogen-fixing',
    verified_share: 0.2,
  },
  {
    id: 'soybean',
    name: 'Soybean',
    family: 'legume',
    traits_summary: '~100 days · 450–700 mm · nitrogen-fixing',
    verified_share: 0.2,
  },
]

const CROP_NAME = Object.fromEntries(CROPS.map((c) => [c.id, c.name]))
export const cropName = (id) => CROP_NAME[id] || id

const MONTHLY_BASE = [
  { month: 1, p20: 0, p50: 0, p80: 1, tmax: 30.4, wet: 0.05 },
  { month: 2, p20: 0, p50: 0, p80: 1, tmax: 33.1, wet: 0.04 },
  { month: 3, p20: 0, p50: 1, p80: 4, tmax: 36.2, wet: 0.04 },
  { month: 4, p20: 2, p50: 10, p80: 25, tmax: 38.1, wet: 0.06 },
  { month: 5, p20: 15, p50: 45, p80: 80, tmax: 36.9, wet: 0.15 },
  { month: 6, p20: 60, p50: 110, p80: 160, tmax: 33.8, wet: 0.35 },
  { month: 7, p20: 120, p50: 200, p80: 290, tmax: 30.9, wet: 0.55 },
  { month: 8, p20: 150, p50: 250, p80: 360, tmax: 29.7, wet: 0.65 },
  { month: 9, p20: 50, p50: 110, p80: 200, tmax: 31.6, wet: 0.45 },
  { month: 10, p20: 5, p50: 20, p80: 50, tmax: 34.0, wet: 0.2 },
  { month: 11, p20: 0, p50: 0, p80: 2, tmax: 32.8, wet: 0.08 },
  { month: 12, p20: 0, p50: 0, p80: 1, tmax: 30.2, wet: 0.05 },
]

const round = (n) => Math.round(n)
const round1 = (n) => Math.round(n * 10) / 10
const round2 = (n) => Math.round(n * 100) / 100
const clamp = (n, lo, hi) => Math.min(hi, Math.max(lo, n))

export function nearestLocation(lat, lon) {
  if (typeof lat !== 'number' || typeof lon !== 'number') return null
  let best = null
  let bestD = Infinity
  for (const loc of LOCATIONS) {
    const dx = loc.lon - lon
    const dy = loc.lat - lat
    const d = dx * dx + dy * dy
    if (d < bestD) {
      bestD = d
      best = loc
    }
  }
  return bestD <= 1.5 ? best : null
}

function zoneFactors(zone = '') {
  if (zone.includes('Sahel')) return { rain: 0.78, temp: 1.2, wet: 0.85 }
  if (zone.includes('Sudan')) return { rain: 0.95, temp: 0.4, wet: 0.95 }
  if (zone.includes('Plateau')) return { rain: 1.05, temp: -1.4, wet: 1.05 }
  if (zone.includes('Middle')) return { rain: 1.28, temp: -1.0, wet: 1.2 }
  return { rain: 1, temp: 0, wet: 1 }
}

export function buildClimate(lat = 12.0, lon = 8.5) {
  const near = nearestLocation(lat, lon)
  const zone = near?.zone || ''
  const f = zoneFactors(zone)

  const monthly = MONTHLY_BASE.map((m) => ({
    month: m.month,
    rain_p20: round(m.p20 * f.rain),
    rain_p50: round(m.p50 * f.rain),
    rain_p80: round(m.p80 * f.rain),
    tmax: round1(m.tmax + f.temp),
    regional_root_zone_wetness: round2(clamp(m.wet * f.wet, 0, 1)),
  }))

  const heatMedian = clamp(34 - (zone.includes('Middle') ? 9 : zone.includes('Plateau') ? 13 : 0), 8, 48)

  return {
    location: {
      lat: round1(lat),
      lon: round1(lon),
      label: near ? `${near.name} (demo)` : 'Selected field',
    },
    datasets: [
      {
        name: 'NASA POWER daily',
        community: 'AG',
        time_standard: 'UTC',
        resolution_note: 'coarse global grid (~0.5°), not field-level',
        period: '1991-2025',
      },
    ],
    monthly,
    season: {
      onset_doy_median: 150,
      cessation_doy_median: 275,
      length_days_median: 125,
      length_days_p20: 98,
      method: 'simplified_v1',
      years_ok: 29,
      years_flagged: 1,
    },
    season_rain_total: {
      median_mm: round(760 * f.rain),
      p20_mm: round(610 * f.rain),
      cv: 0.18,
    },
    dry_spells: { avg_per_season: 2.1, longest_median_days: 11 },
    heat_stress_days: { median: heatMedian, threshold_c: 35 },
    trend: {
      season_rain_mm_per_decade: round(-12 * f.rain),
      note: 'indicative only, not a forecast',
    },
    bare_field_window: { months: [12, 1, 2, 3], basis: 'proxy' },
    data_quality: { from_cache: false, missing_pct: 0.4, flags: [] },
  }
}

// ---------- Recommendation mock ----------

const CRITERIA = [
  'water_fit',
  'season_fit',
  'heat_drought_resilience',
  'soil_health',
  'pest_break',
  'erosion_protection',
  'market_preference_fit',
  'forage_value',
]

const PRIORITY_MAP = {
  water_saving: { water_fit: 1 },
  soil_health: { soil_health: 0.5, pest_break: 0.5 },
  erosion: { erosion_protection: 1 },
  market_preference: { market_preference_fit: 1 },
  forage: { forage_value: 1 },
  resilience: { season_fit: 0.5, heat_drought_resilience: 0.5 },
}

export function weightsFromPriorities(priorities = {}) {
  const raw = Object.fromEntries(CRITERIA.map((c) => [c, 0]))
  let assigned = 0
  for (const [group, mapping] of Object.entries(PRIORITY_MAP)) {
    const value = Number(priorities?.[group] ?? 0)
    if (!value) continue
    for (const [criterion, share] of Object.entries(mapping)) raw[criterion] += value * share
    assigned += value
  }
  if (assigned <= 0) {
    for (const mapping of Object.values(PRIORITY_MAP)) {
      for (const [criterion, share] of Object.entries(mapping)) raw[criterion] += share
    }
  }
  const sum = CRITERIA.reduce((acc, c) => acc + raw[c], 0) || 1
  const weights = {}
  for (const c of CRITERIA) weights[c] = 0.9 * (raw[c] / sum)
  weights.season_fit += 0.1
  return weights
}

function marketFit(sequence, preferred) {
  if (!preferred || preferred.length === 0) return { value: 50, matched: 0, neutral: true }
  const matched = sequence.filter((id) => preferred.includes(id)).length
  return { value: round((100 * matched) / sequence.length), matched, neutral: false }
}

function fitCategory(score) {
  if (score >= 75) return 'strong'
  if (score >= 55) return 'moderate'
  return 'weak'
}

const TEMPLATES = [
  {
    id: 'alt-sorghum-groundnut',
    sequence: ['sorghum', 'groundnut', 'sorghum'],
    label: 'Alternative: sorghum → groundnut → sorghum',
    criteria: { water_fit: 92, season_fit: 94, heat_drought_resilience: 88, soil_health: 88, pest_break: 86, erosion_protection: 76, forage_value: 62 },
    evidenceYears: { water: 26, season: 27, dry: 4 },
    why: 'Leads on the indicators that matter most to you: rainfall reliability and season length, with a legume year that supports soil health and interrupts cereal pests.',
    benefits: [
      'Groundnut adds nitrogen and breaks cereal pest cycles.',
      'Sorghum and groundnut handle heat and dry spells better than continuous maize.',
      'Three-year crop-family diversity reduces back-to-back cereal pressure.',
    ],
    assumptions: [
      'Assumes a 3-year planning horizon with main-season crops only.',
      'Uses the simplified season rule and a 0–7 day planting delay.',
      'Crop traits are placeholders pending verification.',
    ],
    gaps: [
      'Crop water needs and season lengths are not yet verified against a cited source.',
      'Intercropping and double-cropping are out of scope.',
      'Local demand for sorghum and groundnut was not assessed.',
    ],
    risks: [
      'Groundnut is sensitive to poor drainage and some soil-borne diseases; confirm locally.',
      'Sorghum can face bird damage and Striga pressure in some areas.',
      'Sandy, low-organic-matter soil may limit water and nutrient holding.',
    ],
    review: ['Agricultural extension officer', 'Local agronomist'],
  },
  {
    id: 'alt-maize-cowpea',
    sequence: ['maize', 'cowpea', 'maize'],
    label: 'Alternative: maize → cowpea → maize',
    criteria: { water_fit: 69, season_fit: 84, heat_drought_resilience: 62, soil_health: 64, pest_break: 70, erosion_protection: 55, forage_value: 55 },
    evidenceYears: { water: 22, season: 26, dry: 7 },
    why: 'Keeps maize in the rotation while inserting cowpea to improve soil health and break pest cycles.',
    benefits: [
      'Cowpea fixes nitrogen and provides useful ground cover.',
      'Maize stays in the sequence, which fits part of your market preference.',
      'Better crop-family diversity than continuous maize.',
    ],
    assumptions: [
      'Assumes a 3-year planning horizon with main-season crops only.',
      'Uses the simplified season rule and a 0–7 day planting delay.',
      'Crop traits are placeholders pending verification.',
    ],
    gaps: [
      'Maize water requirement and cowpea duration are not yet verified against sources.',
      'Intercropping and double-cropping are out of scope.',
      'Local demand and price stability were not assessed.',
    ],
    risks: [
      'Maize is water-demanding; flowering dry spells remain a risk.',
      'Cowpea needs timely planting and pest monitoring.',
      'Yield and income are outside this tool’s scope.',
    ],
    review: ['Agricultural extension officer'],
  },
  {
    id: 'alt-millet-cowpea-sorghum',
    sequence: ['pearl-millet', 'cowpea', 'sorghum'],
    label: 'Alternative: millet → cowpea → sorghum',
    criteria: { water_fit: 76, season_fit: 90, heat_drought_resilience: 83, soil_health: 70, pest_break: 82, erosion_protection: 60, forage_value: 66 },
    evidenceYears: { water: 24, season: 28, dry: 5 },
    why: 'Prioritises resilience: short-season millet and drought-tolerant sorghum, with a legume year to support soil health.',
    benefits: [
      'Millet and sorghum are well adapted to heat and variable rainfall.',
      'A short crop duration reduces exposure to late-season dry spells.',
      'Cowpea adds nitrogen and ground cover.',
    ],
    assumptions: [
      'Assumes a 3-year planning horizon with main-season crops only.',
      'Uses the simplified season rule and a 0–7 day planting delay.',
      'Crop traits are placeholders pending verification.',
    ],
    gaps: [
      'Market preference fit may be low unless millet and sorghum are sellable for you.',
      'Crop traits are not yet verified against a cited source.',
      'Intercropping and double-cropping are out of scope.',
    ],
    risks: [
      'Millet and sorghum may have lower market demand in some areas.',
      'Bird damage and Striga pressure need local checks.',
      'Grows less maize than your current rotation.',
    ],
    review: ['Agricultural extension officer', 'Local agronomist'],
  },
]

function makeEvidence(template, market) {
  const seq = template.sequence
  const legumes = seq.filter((id) => CROPS.find((c) => c.id === id)?.family === 'legume').length
  const years = template.evidenceYears
  const evidence = [
    {
      source: 'NASA POWER',
      metric: 'Crop-window rainfall ≥ requirement',
      value: `${years.water} of 30 years`,
      meaning: 'Rainfall during the crop growing window met the crop water need in most recorded years.',
    },
    {
      source: 'NASA POWER',
      metric: 'Growing window fits the season',
      value: `${years.season} of 30 years`,
      meaning: 'The estimated rainy season was long enough for the crop to finish.',
    },
    {
      source: 'NASA POWER',
      metric: 'Critical-window dry spells',
      value: `${years.dry} of 30 years`,
      meaning: 'A dry spell struck the flowering or grain-filling window in these years.',
    },
    {
      source: 'Crop knowledge base',
      metric: 'Legume years in sequence',
      value: `${legumes} of 3`,
      meaning:
        legumes > 0
          ? 'At least one legume year can add nitrogen and diversify crop families.'
          : 'No legume year, so soil-nitrogen benefits are limited.',
    },
  ]
  if (market.neutral) {
    evidence.push({
      source: 'Farmer input',
      metric: 'Preferred crops',
      value: 'None stated',
      meaning: 'Market preference fit is treated as neutral because no preferred crops were selected.',
    })
  } else {
    evidence.push({
      source: 'Farmer input',
      metric: 'Preferred crops',
      value: `${market.matched} of 3 crops on your list`,
      meaning: 'This is a preference match only, not an income forecast.',
    })
  }
  return evidence
}

function switchTemplate(template, payload) {
  return {
    ...template,
    is_existing: false,
    sequence: template.sequence,
    label: template.label,
  }
}

export function buildRecommend(payload = {}) {
  const priorities = payload.priorities || {}
  const preferred = payload.preferred_crops || []
  const soil = payload.soil || {}
  const weights = weightsFromPriorities(priorities)

  const existingSeq =
    Array.isArray(payload.current_rotation) && payload.current_rotation.length
      ? payload.current_rotation
      : ['maize', 'maize', 'maize']

  const existing = {
    id: 'existing',
    sequence: existingSeq,
    label: `Your current rotation: ${existingSeq.map(cropName).join(' → ')}`,
    is_existing: true,
    criteria: {
      water_fit: 52,
      season_fit: 78,
      heat_drought_resilience: 44,
      soil_health: 26,
      pest_break: 12,
      erosion_protection: 38,
      forage_value: 28,
    },
    evidenceYears: { water: 18, season: 25, dry: 11 },
    why: 'This is your current rotation, shown as the baseline for comparison. Alternatives are assessed with the same data and rules.',
    benefits: [
      'Familiar and already practiced on your field.',
      'Keeps maize, which matches part of your market preference.',
      'Simple to manage year to year.',
    ],
    assumptions: [
      'Assumes the same main-season crop each year.',
      'Uses the simplified season rule and a 0–7 day planting delay.',
      'Crop traits are placeholders pending verification.',
    ],
    gaps: [
      'No legume year, so nitrogen and soil-health benefits are limited.',
      'Crop traits are not yet verified against a cited source.',
      'Local pest and disease pressure was not assessed.',
    ],
    risks: [
      'Continuous maize increases pest, disease and soil-fertility pressure.',
      'Water demand is high; flowering dry spells are a recurring risk.',
      'Low crop-family diversity across years.',
    ],
    review: ['Agricultural extension officer', 'Local agronomist'],
  }

  const candidates = [existing, ...TEMPLATES.map((t) => switchTemplate(t, payload))]

  const rotations = candidates.map((t) => {
    const sequence = t.sequence
    const market = marketFit(sequence, preferred)
    const criteria = { ...t.criteria, market_preference_fit: market.value }

    if (soil.texture === 'sandy') criteria.water_fit = Math.max(0, criteria.water_fit - 5)
    if (soil.organic_matter === 'low') criteria.soil_health = Math.max(0, criteria.soil_health - 3)
    if (soil.slope === 'steep') criteria.erosion_protection = Math.min(100, criteria.erosion_protection + 4)

    const contributions = {}
    let score = 0
    for (const c of CRITERIA) {
      const contribution = weights[c] * criteria[c]
      contributions[c] = round1(contribution)
      score += contribution
    }
    score = Math.round(score)

    const soilLabels = {
      texture: 'soil texture',
      drainage: 'drainage',
      organic_matter: 'organic matter',
      water_source: 'water source',
      slope: 'slope',
    }
    const unknownSoil = Object.keys(soilLabels).filter((k) => !soil[k] || soil[k] === 'unknown')
    const unknownNames = unknownSoil.map((k) => soilLabels[k])
    const dataLevel = unknownSoil.length >= 3 ? 'low' : unknownSoil.length >= 1 ? 'medium' : 'high'
    const dataReasons = []
    if (unknownSoil.length) dataReasons.push(`${unknownNames.join(', ')} not provided for this field`)
    dataReasons.push('NASA POWER is a coarse grid, not a field measurement')

    const gaps = [...t.gaps]
    if (!market.neutral) {
      // no-op: market fit is already represented in evidence
    } else {
      gaps.push('No preferred crops were selected, so market preference fit is neutral.')
    }
    if (unknownSoil.length) {
      gaps.push(`Soil information missing: ${unknownNames.join(', ')}.`)
    }

    const risks = [...t.risks]
    if (soil.drainage === 'poor') {
      risks.push('Poor drainage may waterlog sensitive crops; confirm field drainage locally.')
    }
    if (soil.texture === 'sandy') {
      risks.push('Sandy soil holds less water and nutrients; water stress may be worse than the grid average.')
    }

    return {
      id: t.id,
      label: t.label,
      is_existing: Boolean(t.is_existing),
      sequence,
      score,
      fit_category: fitCategory(score),
      rank: 0,
      similar_to: [],
      criteria,
      data_confidence: { level: dataLevel, reasons: dataReasons },
      knowledge_support: {
        level: 'low',
        reasons: [
          'Most crop traits are not yet verified against published sources.',
          'Treat rankings as a starting point for local review.',
        ],
      },
      why_suggested: t.why,
      evidence: makeEvidence(t, market),
      benefits: t.benefits,
      assumptions: t.assumptions,
      information_gaps: gaps,
      risks_for_local_review: risks,
      review_recommended_by: t.review,
      trace: {
        algorithm_version: '0.2.0-mock',
        climate_period: '1991-2025',
        priority_weights_applied: weights,
        criteria_contributions: contributions,
      },
    }
  })

  rotations.sort((a, b) => b.score - a.score)
  rotations.forEach((r, i) => {
    r.rank = i + 1
  })
  for (let i = 0; i < rotations.length; i++) {
    for (let j = i + 1; j < rotations.length; j++) {
      if (Math.abs(rotations[i].score - rotations[j].score) < 5) {
        rotations[i].similar_to.push(rotations[j].id)
        rotations[j].similar_to.push(rotations[i].id)
      }
    }
  }

  const [first, second] = rotations
  const leaderGap = first && second ? first.score - second.score : 99
  const bothLow =
    first?.data_confidence.level === 'low' && first?.knowledge_support.level === 'low'

  let overall = 'clear_leader'
  let message = null
  if (first?.fit_category === 'weak' || bothLow) {
    overall = 'no_clear_winner'
    message =
      'None of the evaluated strategies has enough supporting evidence for a confident recommendation. Additional local soil and agronomic information is needed.'
  } else if (leaderGap < 5) {
    overall = 'similar_options'
    message =
      'The leading strategies score within a few points. Treat them as similar options and choose with local knowledge.'
  }

  return {
    overall_outcome: overall,
    outcome_message: message,
    rotations,
    disclaimer:
      'AgroOrbit supports decisions. It does not replace local farmer knowledge or agricultural advisers.',
  }
}
