# Sustainable Navigation Model

ML-powered route scoring for eco-conscious navigation — balancing **time, energy, and carbon** across candidate paths.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/status-early--stage-orange)

---

## 📂 Repository Structure

Sustainable-Navigation-Model/
├── backend/ # Python backend for inference / API
│ ├── main.py # Backend entry point (FastAPI/Flask)
│ ├── api/ # Routes / handlers
│ ├── model/ # Model load / predict utilities
│ └── ... # Helpers, schemas, etc.
├── symbolic_model_carbon.joblib # CO₂ / carbon predictor
├── symbolic_model_energy.joblib # Energy consumption predictor
├── updated_sustainable_navigation_model.joblib # Composite/score model
├── requirements.txt # Python dependencies
├── package.json # (Optional) Node tooling / UI
└── README.md # This file


---

## ✨ Features & Capabilities

- Predicts **energy consumption** and **CO₂ emissions** for candidate routes.  
- Combines route attributes (distance, elevation, speed, congestion, weather) into a **composite sustainability score**.  
- Backend API to accept route candidates and return scored results.  
- Extensible design: new modes, weights, or models can be added easily.  

---

## 🚀 Getting Started

### Prerequisites
- Python **3.10+**  
- (Optional) Node.js **18+** if using the UI/tooling in `package.json`  
- Works on macOS, Linux, or Windows  

### Clone & Setup
```bash
git clone https://github.com/swethamkulkarni/Sustainable-Navigation-Model.git
cd Sustainable-Navigation-Model
Python Environment
bash
Copy code
python -m venv .venv
# macOS/Linux:
source .venv/bin/activate
# Windows:
.venv\Scripts\activate

pip install --upgrade pip wheel
pip install -r requirements.txt
Environment Variables (if needed)
Create a .env file if your backend uses APIs:

ini
Copy code
MAPS_API_KEY=your_maps_api_key
WEATHER_API_KEY=your_weather_api_key
Run the Backend
bash
Copy code
# Example (FastAPI + Uvicorn)
uvicorn backend.main:app --reload --port 8000

# Or Flask-style
python backend/main.py
Backend runs by default at: http://localhost:8000

(Optional) Frontend / Tooling
bash
Copy code
npm install
npm run dev   # or npm run build / npm run start
📡 API (Template)
Healthcheck
bash
Copy code
GET /health
→ {"status":"ok"}
Score Route
bash
Copy code
POST /score
Request JSON

json
Copy code
{
  "route": {
    "polyline": "ENCODED_POLYLINE_OR_WAYPOINTS",
    "distance_km": 5.2,
    "elevation_gain_m": 80,
    "avg_speed_kph": 14.3
  },
  "weather": {
    "temperature_C": 12.5,
    "wind_speed_m_s": 3.4,
    "precipitation_mm": 0.0
  },
  "transport": {
    "mode": "walk|cycle|bus|car",
    "headway_min": 7
  }
}
Response JSON

json
Copy code
{
  "energy_kwh": 0.24,
  "carbon_g": 180.0,
  "eta_min": 28.9,
  "composite_score": 0.71,
  "details": {
    "weights": {"time":0.5,"energy":0.3,"carbon":0.2},
    "influencing_features": ["elevation_gain_m","headway_min"]
  }
}
📊 Models & Artifacts
symbolic_model_carbon.joblib → CO₂ / carbon predictor

symbolic_model_energy.joblib → energy predictor

updated_sustainable_navigation_model.joblib → composite route-scoring model

Tip: add a model_card.md documenting training data, metrics, and limitations.

📈 Benchmarks (Example)
Metric	Baseline (Shortest Path)	Sustainable Model	Δ
Avg Travel Time	34.1 min	28.9 min	–15%
CO₂ (g/journey)	620	540	–13%

Reproduce with:

bash
Copy code
python scripts/benchmark.py --city london --n 200
🛣️ Roadmap
 Add e-scooters & battery-aware cycling

 Integrate real-time transport headways

 Offline tiles + on-device inference

 Multi-objective tuning UI (weights slider + Pareto frontier)

🤝 Contributing
Fork the repo

Create a feature branch (feature/my-addition)

Add tests for new functionality

Run checks:

bash
Copy code
pytest -q
ruff check .
mypy .
Submit a PR with clear description + screenshots if applicable

🔒 Security & Privacy
Don’t commit API keys — keep them in .env

Validate input ranges/types at API boundaries

Models don’t store PII (only route features)

📄 License
MIT License © 2025 Swetha Malhar Kulkarni

🙏 Acknowledgements
OpenStreetMap contributors / routing APIs

OpenWeather (weather feeds)

Research in sustainable routing & symbolic ML
