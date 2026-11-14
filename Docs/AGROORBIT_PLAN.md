# AgroOrbit — Implementation Plan v2

NASA Space Apps Challenge 2026 · **Field Shift: Adapting Farms with NASA Data**
Team: Kepler's Kids · Local event: Luxembourg · Hackathon: Nov 14–15, 2026

## What changed from v1 (read this first)

1. **Season cessation rule redesigned** (v1 could mistake a mid-September dry spell for the end of the season).
2. **Crop water fit now uses timing and dry spells, not just seasonal totals**, and is expressed as "in X of N years" frequencies taken directly from NASA data.
3. **Priorities map explicitly to scoring criteria** (v1 left this open).
4. **Scores are paired with fit categories**, and two separate confidences are reported: *data confidence* and *knowledge support*. A **"no clear winner / insufficient evidence"** outcome is allowed.
5. **Rotation is precisely defined** as a year-by-year sequence of main-season crops.
6. **Crop traits are verified per trait** (value + source + verified flag).
7. **Cache keys, time standard, record length, and data latency** are specified.
8. **Wording fixed:** no global agronomic claims, no income claims ("market preference fit"), soil wetness is a *regional indicator*.
9. **Scope tightened** into P0 / P1 / P2, with realistic time-boxes and freeze points.

---

## 1. One-paragraph summary

AgroOrbit is a decision-support web tool. A farmer picks a field location and tells us about their soil, current rotation, and priorities. AgroOrbit pulls NASA climate data for that location, turns it into explainable growing-season indicators, and **compares at least three crop-rotation strategies (the farmer's existing rotation plus alternatives)** against those indicators and the farmer's priorities. For each strategy it shows why it was suggested, the evidence, benefits, information gaps, and risks needing local review. It supports farmer judgment and never replaces it.

**Scope statement (use this exact framing everywhere):**
"AgroOrbit is designed for global environmental analysis, with its initial agricultural knowledge base focused on Nigeria's northern savanna and Middle Belt. Recommendations outside that region are not validated."

## 2. Challenge requirements checklist

Must have:
- [ ] Decision-support tool using NASA Earth observations + local soil information + crop characteristics + farmer priorities
- [ ] **≥ 3 rotation strategies compared, including the farmer's existing rotation**
- [ ] For each: why suggested · supporting evidence · benefits · information gaps · risks needing local review
- [ ] Clear message: supports, does not replace, farmers and local experts
- [ ] Plain-language explanations; uncertainty and limits stated

## 3. Priorities (P0 / P1 / P2)

| Tier | Item | Rule |
|---|---|---|
| **P0** | API contract + working frontend against mock data | Must complete |
| **P0** | NASA POWER pipeline + climate indicators (cached) | Must complete |
| **P0** | Crop/rotation knowledge base with per-trait sources | Must complete |
| **P0** | Scoring + explanations + confidence + ≥ 3 rotations | Must complete |
| **P0** | Mobile-friendly results with NASA evidence next to each recommendation | Must complete |
| **P0** | Deployment, demo video, project description, submission | Must complete |
| **P1** | Scenario exploration (rainfall / temperature sensitivity) | Only when P0 works end to end |
| **P2** | Real NDVI / SMAP, GIBS layers, slope/erosion, GPM IMERG rainfall | Defer; mention as next steps |
| **P2** | Hausa labels, printable summary | Defer |

**Do not compromise P0 for P2.** One reliable NASA data pipeline and defensible, transparent recommendations beat five half-working satellite integrations.

## 4. Non-goals

- No yield, profit, or income prediction. No guarantees.
- No user accounts.
- No US-only datasets (Web Soil Survey, SSURGO, CDL, PRISM, NAIP, NLCD, CoCoRaHS, NWIS, OpenET, USDA market data).
- No heavy satellite downloads during the demo.
- **Never invent data.** Any assumption is recorded in `ASSUMPTIONS.md` and flagged `verified: false` in data files.

## 5. Architecture

```
[ Frontend (React) ]  <--JSON/REST-->  [ Backend (FastAPI, Python) ]
  map · forms · charts                   ├─ nasa_power.py   fetch + cache + missing-data handling
  comparison cards + evidence            ├─ climate.py      season, dry spells, heat, per-crop-window indicators
                                         ├─ knowledge.py    crops.json, rotations.json (per-trait sources)
                                         ├─ scoring.py      criteria, weights, categories, outcome
                                         ├─ explain.py      why / evidence / benefits / gaps / risks
                                         ├─ quality.py      data confidence + knowledge support (small helper)
                                         └─ scenarios.py    (P1) perturb daily series, re-run pipeline
```

- **Backend:** Python 3.11+, FastAPI, Pydantic, httpx, pandas, numpy, pytest
- **Frontend:** React (Vite or Next.js), Leaflet, Recharts or Chart.js
- **Hosting (free):** backend on Render free web service (sleeps after ~15 min idle; 30–60 s cold start; **re-check current limits**), frontend on Vercel/Netlify/GitHub Pages
- **State:** no database. Knowledge base = JSON in repo. Cache = files in `data/cache/` committed for demo locations.

### Repo layout
```
agroorbit/
├─ README.md
├─ AGROORBIT_PLAN_v2.md
├─ ASSUMPTIONS.md              # every assumption / constant / unverified value, with owner + status
├─ backend/
│  ├─ app/ (main.py config.py models.py nasa_power.py climate.py knowledge.py
│  │        scoring.py explain.py quality.py scenarios.py)
│  ├─ data/
│  │  ├─ crops.json  rotations.json  locations.json  soil_modifiers.json
│  │  └─ cache/
│  ├─ tests/
│  └─ requirements.txt
└─ frontend/
```

## 6. NASA data layer

### 6.1 NASA POWER (primary)
- Endpoint: `https://power.larc.nasa.gov/api/temporal/daily/point` with `parameters`, `community=AG`, `longitude`, `latitude`, `start=YYYYMMDD`, `end=YYYYMMDD`, `format=JSON`, **`time-standard=UTC`**.
- Parameters to request: `PRECTOTCORR` (rainfall), `T2M`, `T2M_MAX`, `T2M_MIN`, `RH2M`, `ALLSKY_SFC_SW_DWN`; soil wetness `GWETTOP`, `GWETROOT`.
- **First task of Phase 2: verify parameter names and compatibility.** Check the POWER parameter dictionary / list-parameters for the AG community at the daily level. **Do not assume all parameters can be requested together;** if soil wetness fails in a combined request, make a second request and merge. Max parameters per request is limited (about 20), so stay well under it.
- **Record length:** daily data exists from 1981. Use **1991 → last complete calendar year (≥ 30 years)** by default; make `START_YEAR` configurable. Document the choice in `ASSUMPTIONS.md`.
- **Latency:** recent days are incomplete (meteorology ≈ days, solar longer). **Never analyze the current partial year.** End the record at the last complete year.
- **Missing values:** `-999` → NaN. Never convert to zero. Track `missing_pct` per parameter and per season.
- **Response shape:** values live under `properties.parameter.<NAME>.<YYYYMMDD>`.
- **Cache key** must include: resolved lat/lon (rounded to a documented grid, e.g. 0.25°), sorted parameter list, start, end, community, time-standard. Store the raw response + fetch timestamp.
- Robustness: timeouts, 2 retries, fall back to cache and set `data_quality.from_cache = true`.
- Resolution honesty: POWER meteorology is a coarse global grid (not field-level). State this in the UI.

### 6.2 Derived indicators (`climate.py`) — all per year, then summarized across years

**Season (simplified, configurable, labelled as such):**
- **Onset:** first date after `ONSET_SEARCH_START` (default Apr 1) where rainfall over 3 consecutive days ≥ 20 mm **and** no dry spell longer than 7 days (daily rain < 1 mm) occurs in the following 30 days.
- **Cessation (redesigned):** the **end of the last 5-day window** between Aug 15 and Dec 31 whose total rainfall ≥ 15 mm. (This avoids the v1 flaw: a September dry spell cannot end the season if meaningful rain returns later, because later rain moves the "last wet window" later.)
- **Season length** = cessation − onset.
- Return per year: `onset`, `cessation`, `length_days`, `method`, `quality_flag` ∈ {`ok`, `onset_not_found`, `cessation_not_found`, `incomplete_year`, `high_missing_data`}.
- Do not present these rules as universal definitions. Thresholds live in `config.py` and are listed in `ASSUMPTIONS.md`. **Validate** on 2–3 known wet and dry years; adjust only with a written reason.

**Crop-window indicators (the explainable core):** for each crop, for each year, define the crop window = `onset + planting_delay` to `+ crop duration` (crop duration = midpoint of `season_days`; delay default 0–7 days, configurable). Then compute:
1. `can_complete`: crop duration (+ buffer) ≤ available season length
2. `window_rain_mm`: total rainfall in the window
3. `water_ok`: `window_rain_mm ≥ water_need_min`
4. `mid_season_dry_spell`: any run > 7 days (rain < 1 mm) inside the flowering/critical window (e.g., 25–60% of the crop window)
5. `heat_days`: days with Tmax above the crop-relevant threshold (default 35 °C, configurable)
Aggregate across years into **frequencies** (e.g., "water requirement met in 22 of 30 years"). These frequencies are the evidence shown to farmers.

**Other summaries:** monthly rainfall P20/P50/P80; seasonal rainfall total, median and CV; dry-spell stats; heat-stress days; trend of seasonal rainfall and onset (linear slope, **"indicative, not a forecast"**); regional soil-wetness monthly means.

**Soil wetness wording (mandatory):** call `GWETTOP` the *regional surface soil wetness indicator* and `GWETROOT` the *regional root-zone wetness indicator*. They are gridded estimates, **not** measurements of water available in the farmer's field. Keep NASA-derived indicators separate from farmer-entered soil information in the UI and API.

**Bare-field window (proxy):** low-rain, low-wetness months. Always label `basis: "proxy"`. If real NDVI is added later, switch to `basis: "observed"`.

### 6.3 Optional (P2)
MODIS/VIIRS NDVI, SMAP, SRTM slope, GIBS tiles, GPM IMERG (≈ 0.1° rainfall; investigate only after POWER works; keep rainfall source swappable). Pre-process offline into small JSON files; document the product and method.

### 6.4 Farmer soil input
All optional; "unknown" is valid and lowers *data confidence*: texture (sandy / loam / clay / unknown), drainage, organic matter (low / medium / high / unknown), water source (rain-fed / limited irrigation / irrigated), slope (flat / gentle / steep / unknown).

## 7. Knowledge base

### 7.1 Rotation definition
A **rotation = an ordered sequence of main-season crops across successive years** (default horizon: 3 years). Example:

| Year | Existing strategy | Alternative A | Alternative B |
|---|---|---|---|
| 1 | Maize | Maize | Sorghum |
| 2 | Maize | Cowpea | Groundnut |
| 3 | Maize | Maize | Sorghum |

Continuous maize is a valid baseline. Intercropping and double-cropping are **out of scope**; say so in the UI notes.

### 7.2 `crops.json` — per-trait verification
```json
{
  "id": "cowpea",
  "name": "Cowpea",
  "family": "legume",
  "traits": {
    "season_days":        {"value": {"min": 60, "max": 90},  "verified": false, "source": null},
    "water_need_mm":      {"value": {"min": 300, "max": 500}, "verified": false, "source": null},
    "drought_tolerance":  {"value": 4, "verified": false, "source": null},
    "heat_tolerance":     {"value": 4, "verified": false, "source": null},
    "nitrogen_fixing":    {"value": true, "verified": false, "source": null},
    "residue_organic_matter": {"value": 3, "verified": false, "source": null},
    "ground_cover_erosion":   {"value": 4, "verified": false, "source": null},
    "forage_value":       {"value": 4, "verified": false, "source": null},
    "root_depth":         {"value": "shallow", "verified": false, "source": null}
  },
  "pest_disease_notes": {"value": "Example: pod borers/aphids; rotate with cereals.", "verified": false, "source": null}
}
```
**The values above are illustrative placeholders, not validated agronomy.** Scales 1–5 (higher = better for that trait). Starting crops (northern Nigeria): maize, sorghum, pearl millet, cowpea, groundnut, soybean. Keep to ~5–6 crops.

**Rules:**
- A trait may be used in scoring while unverified, **but** it must (a) be listed in the rotation's `information_gaps`, (b) lower `knowledge_support`, and (c) appear in `ASSUMPTIONS.md`.
- **Time-box verification** (≈ 1–2 h, split across the team): fill `source` for the highest-impact traits first (season_days, water_need_mm, drought_tolerance, nitrogen_fixing) using FAO, IITA, or national extension references. Set `verified: true` only when a source supports the value.

### 7.3 Candidate rotations
- `rotations.json` holds a small library (6–8 sequences), including continuous baselines.
- The engine **also generates candidates** from the crop list (3-year sequences) with simple constraints (e.g., include at least one legume option and one drought-tolerant option), evaluates **all** candidates with identical data and rules, removes duplicates, and returns:
  1. the farmer's **existing rotation** (always, even if not in the library),
  2. at least **two genuinely different alternatives** (differ by ≥ 1 crop in sequence),
  3. optionally more (cap at 5 total).
- **Never hardcode the three outputs.** Rankings must change when priorities or climate change.

### 7.4 `soil_modifiers.json`
Documented heuristics only (all `verified: false` until reviewed), e.g.: sandy texture → reduce water-fit for high-water-need crops and increase the value of organic-matter-building crops; poor drainage → add a waterlogging note for sensitive crops; unknown → no modifier, add an information gap. Modifiers never override a failed feasibility gate.

## 8. Scoring engine

### 8.1 Criteria (each 0–100 per rotation, averaged across the years of the sequence)
| Criterion | Rule (screening heuristic, not a crop water-balance model) |
|---|---|
| `water_fit` | Share of years where `water_ok` is true **and** no critical-window dry spell; reduced by soil modifiers |
| `season_fit` | Share of years where `can_complete` is true |
| `heat_drought_resilience` | `100 × (1 − exposure × (1 − tolerance_factor))`, where exposure = share of years with a critical dry spell or heat stress in the window, and tolerance_factor = trait/5 clamped to 0.2–1.0 |
| `soil_health` | Nitrogen-fixing crop in sequence, residue/organic matter, root-depth diversity; context-adjusted by farmer OM |
| `pest_break` | Crop-family diversity across consecutive years; same family back-to-back is penalized |
| `erosion_protection` | Ground-cover trait; increased weight if slope is steep; "unknown slope" → neutral + gap |
| `market_preference_fit` | Share of sequence crops among the farmer's **stated** preferred/sellable crops; none stated → neutral + gap |
| `forage_value` | Forage trait |

Constants live in `config.py` and `ASSUMPTIONS.md`.

### 8.2 Priority → criteria mapping (fixed)
| Farmer priority (0–5) | Criteria it weights |
|---|---|
| Water saving | `water_fit` |
| Soil health | `soil_health` (50%) + `pest_break` (50%) |
| Erosion control | `erosion_protection` |
| Market preference | `market_preference_fit` |
| Forage | `forage_value` |
| Resilience | `season_fit` (50%) + `heat_drought_resilience` (50%) |

- Normalize priority weights to sum to 1. **If all priorities are 0, use equal weights** (never divide by zero).
- Apply a small **fixed safety weight** (default 10%) to `season_fit` regardless of priorities, and document why: a rotation the season cannot support should not rank well.
- **Feasibility gate:** if any crop in the sequence can complete the season in < 50% of years, cap that rotation's fit category at `weak` and add an explicit risk.

### 8.3 Scores, categories, outcome
- Internal `score` 0–100 (for ordering and charts).
- `fit_category`: `strong` (≥ 75), `moderate` (55–74), `weak` (< 55); thresholds in config.
- If two rotations differ by < 5 points, mark them `similar`; do not imply a winner.
- **Two separate confidences** (low / medium / high), each with reasons:
  - `data_confidence`: climate record completeness, missing data %, quality flags, unknown farmer inputs, proxy vs observed layers, spatial resolution.
  - `knowledge_support`: share of relevant crop traits that are verified (weighted by the farmer's priority weights).
- **`overall_outcome`**: `"clear_leader"`, `"similar_options"`, or `"no_clear_winner"`. Use `no_clear_winner` when the best rotation is `weak`, or both confidences are `low`. The message: "None of the evaluated strategies has enough supporting evidence for a confident recommendation. Additional local soil and agronomic information is needed."
- Deterministic: identical inputs must give identical outputs.

### 8.4 Explanations (`explain.py`)
Template-based; every claim cites the indicator that produced it.
- `why_suggested`: tied to the farmer's top priorities
- `evidence`: `{source: "NASA POWER" | "farmer input" | "crop knowledge base", metric, value, meaning}` — **label which source each item comes from**
- `benefits`, `information_gaps`, `risks_for_local_review`, `review_recommended_by` (e.g., agricultural extension officer)
- Optional LLM rewrite into friendlier wording **only after** everything else works; scoring stays rule-based; check the event's AI-use disclosure rules.

### 8.5 Scenarios (P1)
Perturb the daily series (scale daily rainfall by `1 + rainfall_change_pct/100`; add `temperature_change_c` to temperature), **re-run the same pipeline**, and show deltas vs baseline. Label clearly: "hypothetical sensitivity test, not a forecast." Note the limitation: this does not change rainfall timing patterns.

## 9. API contract (freeze at end of Phase 1)

- `GET /health` → `{"status":"ok"}`
- `GET /locations` → `[{id, name, lat, lon, zone}]` (demo presets: Kano, Kaduna, Jos, Makurdi, …)
- `GET /crops` → `[{id, name, family, traits_summary, verified_share}]`
- `GET /climate?lat=..&lon=..`
- `POST /recommend`

### `GET /climate` response (shape)
```json
{
  "location": {"lat": 12.0, "lon": 8.5, "label": "Kano (demo)"},
  "datasets": [{"name": "NASA POWER daily", "community": "AG", "time_standard": "UTC",
                "resolution_note": "coarse global grid, not field-level", "period": "1991-2025"}],
  "monthly": [{"month": 1, "rain_p20": 0, "rain_p50": 0, "rain_p80": 1, "tmax": 31.2, "regional_root_zone_wetness": 0.21}],
  "season": {"onset_doy_median": 150, "cessation_doy_median": 275, "length_days_median": 125,
             "length_days_p20": 98, "method": "simplified_v1", "years_ok": 29, "years_flagged": 1},
  "season_rain_total": {"median_mm": 760, "p20_mm": 610, "cv": 0.18},
  "dry_spells": {"avg_per_season": 2.1, "longest_median_days": 11},
  "heat_stress_days": {"median": 34, "threshold_c": 35},
  "trend": {"season_rain_mm_per_decade": -12, "note": "indicative only, not a forecast"},
  "bare_field_window": {"months": [12, 1, 2, 3], "basis": "proxy"},
  "data_quality": {"from_cache": false, "missing_pct": 0.4, "flags": []}
}
```

### `POST /recommend` request
```json
{
  "lat": 12.0, "lon": 8.5,
  "current_rotation": ["maize", "maize", "maize"],
  "soil": {"texture": "sandy", "drainage": "unknown", "organic_matter": "low",
           "water_source": "rain_fed", "slope": "unknown"},
  "priorities": {"water_saving": 5, "soil_health": 4, "erosion": 2,
                 "market_preference": 3, "forage": 1, "resilience": 4},
  "preferred_crops": ["maize", "groundnut"],
  "scenario": {"rainfall_change_pct": 0, "temperature_change_c": 0}
}
```

### `POST /recommend` response (shape)
```json
{
  "overall_outcome": "clear_leader",
  "outcome_message": null,
  "rotations": [
    {
      "id": "existing",
      "label": "Your current rotation: maize → maize → maize",
      "is_existing": true,
      "sequence": ["maize", "maize", "maize"],
      "score": 52,
      "fit_category": "weak",
      "rank": 3,
      "similar_to": [],
      "criteria": {"water_fit": 58, "season_fit": 80, "heat_drought_resilience": 45,
                   "soil_health": 25, "pest_break": 10, "erosion_protection": 40,
                   "market_preference_fit": 70, "forage_value": 30},
      "data_confidence": {"level": "medium", "reasons": ["slope and drainage unknown"]},
      "knowledge_support": {"level": "low", "reasons": ["most crop traits not yet verified"]},
      "why_suggested": "…",
      "evidence": [
        {"source": "NASA POWER", "metric": "crop window rainfall ≥ requirement", "value": "22 of 30 years", "meaning": "…"}
      ],
      "benefits": ["…"],
      "assumptions": ["…"],
      "information_gaps": ["…"],
      "risks_for_local_review": ["…"],
      "review_recommended_by": ["Agricultural extension officer"],
      "trace": {"algorithm_version": "0.2.0", "climate_period": "1991-2025",
                "priority_weights_applied": {}, "criteria_contributions": {}}
    }
  ],
  "disclaimer": "AgroOrbit supports decisions. It does not replace local farmer knowledge or agricultural advisers."
}
```
Rules: `rotations.length ≥ 3`; existing always present; sorted by score; plain-language text; scenario results are labelled hypothetical.

## 10. Frontend specification (teammate)

**P0 — five experiences** (mobile-first, low bandwidth, plain language):
1. **Field selection:** Leaflet map click + presets + manual lat/lon.
2. **Farm profile & priorities:** current rotation (crop dropdowns per year), soil fields (all optional, "I don't know" allowed), preferred crops, priority sliders.
3. **Rotation comparison:** 3+ cards (stack on mobile): fit category, score, rank, both confidence badges, "similar" note, criteria bar/radar chart. Show the `no_clear_winner` message when returned.
4. **NASA evidence beside each recommendation:** an expandable **Evidence** section on every card listing the actual metrics ("water requirement met in 22 of 30 years", season length, dry spells, heat days), each labelled by source (NASA / your input / crop knowledge).
5. **Climate view:** monthly rainfall bars (P20/50/80), temperature line, shaded rainy season, dry-spell/heat stats, bare-field window (labelled proxy/observed).

Always: visible disclaimer, a "waking up the server…" loading state, graceful errors, glossary tooltips for key terms.

**P1:** scenario slider. **P2:** GIBS layer toggle, NDVI timeline, Hausa labels, print summary.

**Wording rules:** say "regional soil wetness indicator" (not "soil moisture"); "market preference fit" (not income); "hypothetical scenario" (not forecast); "fit category" next to scores; never "best crop".

The frontend builds against mock JSON matching Section 9 from the first hour.

## 11. Phases (realistic time-boxes; two developers in parallel)

Total effort ≈ 30–34 working hours across the team **plus ≥ 4 h buffer**. If you fall behind, cut P1/P2, never the P0 list.

| Phase | Backend (you) | Frontend (teammate) | Done when |
|---|---|---|---|
| **0 Setup** (~1 h) | Repo, FastAPI `/health`, CORS | Scaffold, routing, mock data file | Both run locally; frontend calls `/health` |
| **1 Contract & mocks** (~2 h) | Pydantic models for Section 9; mock `/climate`, `/recommend` | Render full flow from mocks | **Contract frozen**; frontend renders mock end to end |
| **2 NASA data** (~5–7 h) | `nasa_power.py`, cache, `-999` handling, **parameter verification**, `climate.py`, tests on cached fixtures, pre-fetch demo locations | Map, forms, charts shells | `/climate` returns real indicators for 2+ Nigerian locations; season results look plausible (rainy season roughly mid-year in the north) |
| **3 Knowledge base** (~3–4 h) | `crops.json` with per-trait sources, `rotations.json`, `soil_modifiers.json`, `ASSUMPTIONS.md` | Results cards UI, evidence panels | Crop traits have sources or explicit `verified:false` flags |
| **4 Recommendation engine** (~6–8 h) | Crop-window indicators, scoring, categories, outcome, confidences, explanations, trace, candidate generator, tests | Wire climate view + cards to live endpoints | `/recommend` returns ≥ 3 distinct, deterministic rotations; ranking responds sensibly to priorities |
| **5 Integration** (~4–5 h) | Fix contract mismatches, error handling | Loading/error/cold-start states, mobile polish | Full run works on a phone-sized screen. **Feature freeze here** (except P1) |
| **6 Validate & deploy** (~3–4 h) | Edge-case tests, deploy backend, CORS, warm-up plan | Deploy frontend, test live | Works live and from cache with network off |
| **7 Submission** (reserve ≥ 4 h before the deadline) | README, technical notes, dataset list | Demo video, screenshots | Submitted **before the hackathon closes on Nov 15** |
| **P1 (optional)** | `scenarios.py` | Scenario slider | Scenario deltas display, labelled hypothetical |

## 12. Testing checklist

**Data**
- [ ] `-999` never used in calculations; missing rainfall never becomes zero
- [ ] Invalid coordinates rejected; partial/current year excluded
- [ ] Cache key includes location, parameters, dates, community, time standard
- [ ] Onset/cessation checked on at least one wet and one dry year; the mid-September-dry-spell case does **not** end the season early
- [ ] Incomplete/flagged seasons are reported, not silently used

**Engine**
- [ ] All-zero priorities → equal weights, no division by zero
- [ ] Unknown crop IDs handled gracefully; existing rotation outside the library still evaluated
- [ ] ≥ 3 distinct rotations, duplicates removed, existing always included
- [ ] Priority changes change rankings in a believable direction
- [ ] Different soil profiles change relevant criteria
- [ ] Unknown inputs lower `data_confidence` and add gaps; unverified traits lower `knowledge_support` and are listed
- [ ] Weak/low-confidence results can return `no_clear_winner`
- [ ] Identical inputs → identical outputs
- [ ] Every recommendation includes a trace from inputs to scores

**Frontend / ops**
- [ ] Works on a phone-sized screen; handles slow/failed backend gracefully
- [ ] Scenarios labelled hypothetical; disclaimer always visible
- [ ] Demo locations work offline from cache

## 13. Working with the coding agent (Antigravity)

**Standing rules to give the agent:**
- "Follow AGROORBIT_PLAN_v2.md. Work only on Phase N. Do not change the API contract in Section 9 without asking."
- "Do not invent agronomic numbers or NASA parameter names. Mark every assumption `verified: false`, add it to ASSUMPTIONS.md, and tell me."
- "Write tests with each module. Keep scoring deterministic and constants in config."
- Work in small, reviewable changes and **read every diff**, especially scoring, indicators, and data files. Separate branches for backend and frontend; merge often.

**Starter prompts:**
- **Phase 0:** "Create the repo layout from Section 5: FastAPI backend with `/health` and CORS, React frontend scaffold. No business logic."
- **Phase 1:** "Implement Pydantic models for the Section 9 contract. Make `/climate` and `/recommend` return realistic mock data with 3 rotations, including `overall_outcome`."
- **Phase 2:** "Implement the NASA POWER client (Section 6.1) with `time-standard=UTC`, -999→NaN, retries, and the cache key from Section 6.1. First, list the parameters available for the AG community at the daily level and tell me if soil wetness must be requested separately. Then implement the indicators in Section 6.2 with tests."
- **Phase 3:** "Create `crops.json` using the per-trait schema in 7.2. Use placeholder values only where unavoidable and mark them `verified: false`; list every assumption in ASSUMPTIONS.md."
- **Phase 4:** "Implement crop-window indicators, scoring (8.1–8.3), explanations (8.4), candidate generation (7.3), confidences, and the `no_clear_winner` outcome. Include the engine tests in Section 12."

## 14. Pitch & demo (≈ 2–3 min)

Tell the **science chain**, not a startup story:
**NASA observations → environmental indicators → crop constraints → rotation comparison → explainable decision support.**
1. Problem (20 s): shifting rains, short seasons, tired soils.
2. Persona (15 s): a smallholder in northern Nigeria with maize-on-maize.
3. Live flow (60–75 s): pick location → soil + priorities → 3+ rotations → open one card's **evidence** ("met in 22 of 30 years") → (P1) rainfall slider.
4. Sources (20 s): say plainly which information is **NASA**, which is **farmer input**, and which is **agronomic knowledge**.
5. Honesty (15 s): confidence, gaps, risks, no-clear-winner outcome; supports local expertise.
6. Next steps (15 s): real NDVI/SMAP, IMERG rainfall, more regions with validated crop knowledge, local languages.

## 15. Risks & fallbacks

| Risk | Fallback |
|---|---|
| NASA POWER slow/down or parameter incompatibility | Cached demo-location data; split requests; flag `from_cache` |
| Free backend cold start | Warm `/health` before demo; loading message; run locally as last resort |
| Season rules give odd results | Validate on known years; adjust with a written reason; show quality flags |
| Crop traits unverified | Flag loudly, lower knowledge_support, list in gaps; verify top traits first |
| Scope creep | Freeze features at end of Phase 5 |
| Merge conflicts | Separate folders/branches; frozen contract |
| Overconfident scores | Categories + confidences + `no_clear_winner` |

## 16. Final submission checklist
- [ ] Live frontend link works; backend warmed
- [ ] Demo video recorded and uploaded
- [ ] Project description complete (problem → NASA data → indicators → comparison → limits)
- [ ] README: run instructions, data sources, methods summary, limitations, team, license; ASSUMPTIONS.md included
- [ ] NASA datasets and what each is used for are listed
- [ ] Scope statement and "supports, not replaces" message present
- [ ] Team **Kepler's Kids**, project **AgroOrbit**, challenge **Field Shift: Adapting Farms with NASA Data** set on the submission
- [ ] AI-tool disclosure completed if the event requires it
- [ ] Submitted before the hackathon closes (Nov 15)
