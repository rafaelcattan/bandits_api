# Multi-Armed Bandit Optimization API

A RESTful API that receives temporal data from Multi‑Armed Bandit experiments, processes it using SQL, and returns the optimal traffic allocation percentages for control and variant(s) for the following day. The API implements Thompson Sampling for dynamic allocation.

## Features
- **FastAPI** – modern, fast web framework with automatic OpenAPI documentation.
- **SQLite** – lightweight, file‑based SQL database.
- **Thompson Sampling** – Bayesian bandit algorithm for adaptive traffic allocation.
- **RESTful Endpoints** – ingest daily metrics and retrieve allocation recommendations.
- **Unit Tests** – comprehensive test suite with pytest.

## Quick Start
### Prerequisites
- Python 3.9 or higher
- pip (Python package manager)

### Installation
1. Clone the repository (or download the source).
2. Create a virtual environment:
   ```bash
   python -m venv venv
   ```
3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Unix/macOS: `source venv/bin/activate`
4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
5. Run the application:
   ```bash
   uvicorn app.main:app --reload
   ```
6. Open your browser to `http://localhost:8000/docs` to see the interactive API documentation.

## API Usage
### Submit Daily Metrics
`POST /data`
```bash
curl -X POST "http://localhost:8000/data" \
  -H "Content-Type: application/json" \
  -d '{
    "experiment_id": "ctr_test",
    "date": "2025-12-22",
    "variants": [
      {"variant_id": "control", "impressions": 1000, "clicks": 50},
      {"variant_id": "variant", "impressions": 1000, "clicks": 70}
    ]
  }'
```

### Get Allocation for Next Day
`GET /allocation?experiment_id=ctr_test`
```bash
curl "http://localhost:8000/allocation?experiment_id=ctr_test"
```
Response:
```json
{
  "experiment_id": "ctr_test",
  "date": "2025-12-23",
  "allocations": [
    {"variant_id": "control", "percentage": 45.2},
    {"variant_id": "variant", "percentage": 54.8}
  ]
}
```

## Project Structure
```
bandit-api/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app & routes
│   ├── database.py          # DB connection & setup
│   ├── models.py            # SQLAlchemy models
│   ├── schemas.py           # Pydantic models
│   ├── algorithms.py        # Thompson Sampling
│   └── crud.py              # Database operations
├── tests/
│   ├── test_api.py
│   ├── test_algorithm.py
│   └── test_database.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml (optional)
└── README.md
```

## Algorithm Details
The system uses **Thompson Sampling**:
- Each variant is modeled as a Bernoulli process with unknown success probability `p`.
- Prior: `Beta(α=1, β=1)` (uniform).
- Posterior: `Beta(α = 1 + total_clicks, β = 1 + total_impressions - total_clicks)`.
- Allocation percentages are computed via Monte Carlo simulation (10,000 samples) of the posterior distributions.

## Development
### Running Tests
```bash
pytest
```

### Code Style
This project follows [PEP 8](https://www.python.org/dev/peps/pep-0008/). Format with `black` and `isort` if desired.

### Database Migrations
The current version uses SQLAlchemy ORM with auto‑created tables. For production, consider using Alembic for schema migrations.

## License
MIT