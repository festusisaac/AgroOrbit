# AgroOrbit

> **NASA Space Apps Challenge 2026** · *Field Shift: Adapting Farms with NASA Data*  
> **Team:** Kepler's Kids · **Local Event:** Luxembourg  
> **Live Backend API:** [https://agroorbit-backend.onrender.com](https://agroorbit-backend.onrender.com)  
> **Interactive Swagger Docs:** [https://agroorbit-backend.onrender.com/docs](https://agroorbit-backend.onrender.com/docs)

AgroOrbit is an open-source, decision-support web application that harnesses 35+ years of continuous NASA Earth observation satellite data, agronomic phenology rules, and farmer priorities to evaluate, compare, and recommend resilient 3-year crop rotation strategies.

```
       [ 35+ Years of NASA POWER Satellites ]
      (Precipitation, Temp, Humidity, Soil Wetness)
                         │
                         ▼
           [ Crop Phenology Simulation ]
        (Can Complete, Dry Spells, Heat Days)
                         │
                         ▼
        [ Feasibility Gate & Scoring Engine ]
   (Safety Weight, Legume Nitrogen, Farmer Priorities)
                         │
                         ▼
          [ Transparent Explainability ]
     (Auditable Frequencies, Gaps, Local Risks)
                         │
                         ▼
        [ Interactive AgroOrbit Dashboard ]
```

> [!IMPORTANT]
> **Agronomic Scope Statement:**  
> *AgroOrbit retrieves real NASA daily satellite observations worldwide (including Nigeria, Ghana, Kenya, India, Brazil, and the United States). Its calibrated agricultural trait knowledge base is centered on West African savanna agroecological zones (Sudan Savanna, Northern & Southern Guinea Savanna, Jos Plateau). Queries for other global regions retrieve real NASA climate records and highlight uncalibrated regional boundaries with an explicit local extension advisory warning.*  
>
> AgroOrbit supports farmer judgment and extension agent advice; it never replaces local expertise and makes no financial guarantees.

---

## Key Features

### 🛰️ 1. Multi-Decadal NASA Earth Observation Engine
* Connects directly to the **NASA POWER API** (Prediction Of Worldwide Energy Resources) daily point meteorology.
* Analyzes **35 years (1991–2025)** of daily satellite measurements:
  * `PRECTOTCORR`: Precipitation corrected ($mm/day$)
  * `T2M_MAX` / `T2M_MIN` / `T2M`: Daily maximum, minimum, and mean temperatures ($^\circ C$)
  * `RH2M`: Relative humidity at 2 meters ($\%$)
  * `ALLSKY_SFC_SW_DWN`: Solar insolation ($MJ/m^2/day$)
  * `GWETROOT` / `GWETTOP`: Root-zone and surface soil wetness ($0.0 - 1.0$)
* Computes robust growing-season indicators using a two-tier rainfall window method:
  * **Rainy Season Onset Date:** First 3-day rainfall $\ge 20\text{ mm}$ with no subsequent dry spell $>7$ days in the following 30 days.
  * **Season Cessation Date:** Last 5-day window receiving $\ge 15\text{ mm}$ of rain before the dry season.
  * **Growing Season Length:** Median and 20th percentile (dry year) duration in days.
  * **Dry Spell Frequency:** Runs of $>7$ consecutive rainless days ($<1\text{ mm}$) during the active crop flowering window.
  * **Thermal Stress:** Days exceeding crop-specific critical temperature thresholds ($>35^\circ C$).

### 🌱 2. Agronomic Crop Simulation & Feasibility Gate
* Models 9 regional staple crops: **Maize, Sorghum, Pearl Millet, Cowpea, Groundnut, Soybean, Cassava, Rice, and Yam**.
* Evaluates crop water requirements, season maturity days, root depth, erosion protection factor, and nitrogen fixation capacity.
* **The Safety-First Feasibility Gate:** If a crop fails to reach maturity before season cessation in $\ge 50\%$ of historical years, the entire rotation sequence is capped at **"Weak"**, ensuring high-risk monocropping or late-maturing varieties are never recommended as safe options.

### ⚖️ 3. Multi-Objective Deterministic Scoring
* 100% deterministic, rule-based scoring engine with zero hallucination.
* Evaluates 8 distinct criteria:
  1. `season_fit`: Growing season length vs. crop maturity (includes a mandatory 10% safety weight).
  2. `water_fit`: Crop-window rainfall vs. total water requirement.
  3. `soil_health`: Legume rotation benefits, nitrogen fixation, organic matter preservation, and pest break intervals.
  4. `erosion_risk`: Ground canopy cover during early erosive storm periods.
  5. `market_preference`: Farmer cash-crop demand and local staple preference.
  6. `forage_value`: Crop residue, stover, and livestock fodder value.
  7. `heat_drought_resilience`: Tolerance to high heat days and mid-season dry spells.
  8. `break_benefit`: Pest and disease interruption between cereal cycles.

### 🔍 4. Transparent Explainability & Auditable Evidence
* Every recommendation includes plain-language justifications:
  * **Why Suggested:** Specific agronomic rationale (e.g. *"Cowpea fixes nitrogen into the soil, reducing synthetic fertilizer costs for the next season's maize"*).
  * **NASA Evidence with Real Empirical Frequencies:** (e.g. *"Completed growth cycle before season end in 29 of 35 years"*).
  * **Information Gaps:** Honest accounting of unverified traits or unknown soil characteristics.
  * **Risks for Local Review:** Flags localized concerns like certified seed availability, heat-tolerant cultivars, and soil inoculants.

### 🌡️ 5. Climate Sensitivity Stress-Testing
* Built-in scenario modeler allows testing "what-if" climate disruptions:
  * Rainfall perturbations ($-30\%$ to $+30\%$).
  * Temperature shifts ($0^\circ C$ to $+3.0^\circ C$).
* Reruns the entire 35-year daily sequence under perturbed conditions and labels outputs as hypothetical sensitivity tests.

### 🎨 6. Accessible, Responsive Frontend
* **Auto-Loading on Launch:** Automatically runs the comparison on startup for instant feedback.
* **Interactive Onboarding Modal:** New visitors are greeted with pre-filled, editable farm setup options (country, region, current crops, soil, and priorities).
* **Worldwide Map & Coordinate Picker:** Select any farm worldwide via interactive satellite maps or GPS geolocation.
* **100% Semantic Iconography:** Zero emoji dependencies; powered by clean, uniform Lucide SVG icons.

---

## Repository Structure

```text
AgroOrbit/
├── ASSUMPTIONS.md         # Heuristic thresholds, algorithm rules, and trait audit trail
├── README.md              # Project documentation and quickstart
├── render.yaml            # Render Blueprint for unified fullstack deployment
├── Docs/
│   └── AGROORBIT_PLAN.md  # Architectural implementation plan (v2)
├── backend/               # Python / FastAPI backend service
│   ├── app/
│   │   ├── main.py        # FastAPI application and CORS entrypoint
│   │   ├── config.py      # Climate thresholds, regions, and environment settings
│   │   ├── models.py      # Frozen Pydantic v2 API schemas
│   │   ├── climate.py     # 35-year NASA POWER climate indicator calculations
│   │   ├── scoring.py     # Multi-criteria scoring engine & feasibility gate
│   │   ├── candidates.py  # 3-year rotation generator and sequence library
│   │   ├── explain.py     # Trace, why-suggested, and evidence generator
│   │   ├── quality.py     # Data completeness and coverage checks
│   │   └── nasa_power.py  # Asynchronous HTTP client with disk caching
│   ├── data/
│   │   ├── crops.json     # 9 verified crops catalog
│   │   ├── locations.json # Demo benchmark locations
│   │   └── cache/         # Multi-decadal NASA POWER daily cached datasets
│   ├── tests/             # 70 automated pytest unit and integration tests
│   └── requirements.txt   # Backend dependencies
└── frontend/              # React 18 + Vite client application
    ├── public/            # Static assets
    ├── src/
    │   ├── api/           # API client with automatic live backend connectivity
    │   ├── components/    # UI components (OnboardingModal, SetupPanel, ResultsView, etc.)
    │   ├── data/          # Regional benchmarks and definitions
    │   └── styles/        # CSS design system
    ├── package.json       # Frontend dependencies
    └── vite.config.js     # Vite configuration
```

---

## Live API Endpoints

The backend is live on Render at **`https://agroorbit-backend.onrender.com`**:

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Service health check (`{"status": "ok"}`) |
| `GET` | `/locations` | Catalog of preset agroecological benchmark locations |
| `GET` | `/crops` | Catalog of crops with physiological traits and verification shares |
| `GET` | `/climate?lat={lat}&lon={lon}` | Multi-decadal NASA climate indicators, onset/cessation, and season statistics |
| `POST` | `/recommend` | Evaluates $\ge 3$ rotation strategies against climate, soil, and priorities |

### Example `POST /recommend` Request
```json
{
  "lat": 12.0022,
  "lon": 8.5919,
  "current_rotation": ["maize", "maize", "maize"],
  "soil": {
    "texture": "sandy",
    "drainage": "moderate",
    "organic_matter": "low",
    "water_source": "rain_fed",
    "slope": "flat"
  },
  "priorities": {
    "water_saving": 5,
    "soil_health": 4,
    "erosion": 2,
    "market_preference": 4,
    "forage": 1,
    "resilience": 4
  },
  "preferred_crops": ["maize", "cowpea", "sorghum"],
  "scenario": {
    "rainfall_change_pct": 0,
    "temperature_change_c": 0
  }
}
```

---

## Local Development Setup

### Prerequisites
* **Python 3.11+**
* **Node.js 18+** and **npm**
* Git

---

### Backend Setup

```bash
# 1. Navigate to backend
cd backend

# 2. Create and activate a virtual environment
# Windows:
python -m venv .venv
.venv\Scripts\activate
# Linux / macOS:
python3 -m venv .venv
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start backend server
uvicorn app.main:app --reload --port 8000
```

The backend will be running at `http://localhost:8000` with Swagger documentation at `http://localhost:8000/docs`.

#### Running Backend Tests
Execute the complete test suite (70 tests):
```bash
pytest backend/tests
```

---

### Frontend Setup

```bash
# 1. Navigate to frontend
cd frontend

# 2. Install dependencies
npm install

# 3. Start local development server
npm run dev
```

The frontend will start at `http://localhost:5173`. It is configured to automatically communicate with the live backend (`https://agroorbit-backend.onrender.com`), or you can override it locally by creating `frontend/.env`:
```env
VITE_API_BASE_URL=http://localhost:8000
```

#### Building Frontend for Production
```bash
npm run build
```

---

## Deployment Guide

### Deploy on Render (Recommended)

AgroOrbit includes an Infrastructure-as-Code [render.yaml](render.yaml) blueprint at the repository root defining both services:

1. Log in to [Render Dashboard](https://dashboard.render.com).
2. Click **New +** $\rightarrow$ **Blueprint**.
3. Connect your repository.
4. Render will automatically detect `render.yaml` and configure:
   * **Backend Web Service:** `agroorbit-backend` (Python 3.11, `rootDir: backend`, `uvicorn app.main:app`).
   * **Frontend Static Site:** `agroorbit-frontend` (Static runtime, `rootDir: frontend`, `buildCommand: npm install && npm run build`, `staticPublishPath: dist`).
5. Click **Apply**. Both services will build and deploy with continuous integration from `main`.

---

## Scientific Transparency & Auditability

Every constant, threshold, heuristic formula, and assumption used in AgroOrbit is rigorously documented in:
* **[ASSUMPTIONS.md](ASSUMPTIONS.md):** Complete audit trail of season definitions, critical windows, heat thresholds, soil modifiers, and crop trait verification statuses.
* **[Docs/AGROORBIT_PLAN.md](Docs/AGROORBIT_PLAN.md):** Architectural blueprints, scoring criteria weights, and API schemas.

---

## Team & Acknowledgements

* **Challenge:** NASA Space Apps Challenge 2026 (*Field Shift: Adapting Farms with NASA Data*)
* **Team:** Kepler's Kids (Luxembourg)
* **Data Sources:** NASA POWER Project (NASA Langley Research Center), MERRA-2, GEOS-5, CERES, and FAO Crop Water & Management Standards.
* **License:** Open Source under the MIT License.
