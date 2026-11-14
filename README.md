# AgroOrbit

> **NASA Space Apps Challenge 2026** · *Field Shift: Adapting Farms with NASA Data*  
> **Team:** Kepler's Kids · **Local Event:** Luxembourg

AgroOrbit is a decision-support web tool that leverages NASA Earth observation data, local soil characteristics, crop constraints, and farmer priorities to evaluate and compare crop-rotation strategies.

> [!IMPORTANT]
> **Scope statement:**  
> *AgroOrbit is designed for global environmental analysis, with its initial agricultural knowledge base focused on Nigeria's northern savanna and Middle Belt. Recommendations outside that region are not validated.*
>
> AgroOrbit supports farmer judgment and agricultural extension advice; it never replaces local expertise and makes no yield or profit guarantees.

---

## Repository Structure

```text
AgroOrbit/
├── ASSUMPTIONS.md       # Assumptions log, heuristic thresholds, and trait verification audit trail
├── Docs/
│   └── AGROORBIT_PLAN.md # Implementation plan (v2) - single source of truth
├── backend/             # Python / FastAPI backend
│   ├── app/             # Application source (main, config, models, mock_data, engines)
│   ├── data/            # Knowledge base and cache fixtures
│   ├── tests/           # Pytest test suite (contract and indicator tests)
│   └── requirements.txt # Python dependencies
└── frontend/            # React client application (owned by teammate)
```

---

## Backend Getting Started

### 1. Prerequisites
- **Python 3.11+** installed (tested on Python 3.14)
- Git

### 2. Environment Setup

From the repository root (`AgroOrbit`):

#### On Windows (PowerShell):
```powershell
# Create virtual environment
python -m venv backend/.venv

# Activate virtual environment
backend\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r backend/requirements.txt
```

#### On Windows (Command Prompt):
```cmd
python -m venv backend\.venv
backend\.venv\Scripts\activate.bat
pip install -r backend\requirements.txt
```

#### On Linux / macOS:
```bash
python3 -m venv backend/.venv
source backend/.venv/bin/activate
pip install -r backend/requirements.txt
```

---

## Running the Backend Server

With the virtual environment activated:

```powershell
# Option A: From backend/ directory
cd backend
uvicorn app.main:app --reload --port 8000

# Option B: From repository root (setting PYTHONPATH)
python -m uvicorn app.main:app --app-dir backend --reload --port 8000
```

The backend will start at:
- **Base URL:** `http://localhost:8000`
- **Interactive API Docs (Swagger UI):** `http://localhost:8000/docs`
- **Alternative Docs (ReDoc):** `http://localhost:8000/redoc`

---

## Running Tests

Execute the automated test suite with `pytest`:

```powershell
# From repository root
pytest backend/tests

# Or run with verbose test output
pytest -v backend/tests
```

---

## API Contract (Section 9)

The API contract is frozen to enable parallel frontend development. CORS is enabled for local frontend development on ports `3000` and `5173`.

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Health check endpoint returning `{"status":"ok"}` |
| `GET` | `/locations` | Preset demo locations (Kano, Kaduna, Jos, Makurdi) |
| `GET` | `/crops` | Catalog of crops with traits and verification shares |
| `GET` | `/climate?lat={lat}&lon={lon}` | Multi-decadal NASA climate indicators and season statistics |
| `POST` | `/recommend` | Evaluates $\ge 3$ crop-rotation strategies against soil & priorities |

### Example `POST /recommend` Request
```json
{
  "lat": 12.0,
  "lon": 8.5,
  "current_rotation": ["maize", "maize", "maize"],
  "soil": {
    "texture": "sandy",
    "drainage": "unknown",
    "organic_matter": "low",
    "water_source": "rain_fed",
    "slope": "unknown"
  },
  "priorities": {
    "water_saving": 5,
    "soil_health": 4,
    "erosion": 2,
    "market_preference": 3,
    "forage": 1,
    "resilience": 4
  },
  "preferred_crops": ["maize", "groundnut"],
  "scenario": {
    "rainfall_change_pct": 0,
    "temperature_change_c": 0
  }
}
```

---

## Scientific Transparency & Assumptions

All scientific choices, heuristic thresholds (e.g., season onset definitions, temperature stress limits), and unverified crop traits are transparently cataloged in [ASSUMPTIONS.md](ASSUMPTIONS.md).
