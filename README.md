# Quantum State Visualizer

MVP scaffolding with a FastAPI backend exposing `/simulate` for quantum circuit state visualization, and a planned React frontend per `frontend_plan.md`.

## Structure

- `backend/` FastAPI app, requirements, and docs
- `dev_plane.md`, `frontend_plan.md`, `Project_Plan_Quantum_State_Visualizer.md`

## Quick start (backend)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload --port 8000
```

Then POST to `http://localhost:8000/simulate` with JSON: `{ "preset": "bell" }`.

## Next

- Initialize the React + TS frontend (Vite)
- Wire TanStack Query to call `/simulate`
- Implement Bloch sphere grid using React Three Fiber
