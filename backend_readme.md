# Quantum State Visualizer — Backend Deep Dive

This document explains the backend architecture, files, math, and code paths powering the Quantum State Visualizer. It targets engineers extending or integrating the backend.

Contents:
- Files and roles
- API endpoints and schemas
- Pipelines (unitary, exact_density, trajectory)
- Math (density matrices, partial trace, Bloch vectors, purity)
- Routing, supported gates, CORS/security
- Run, test, extend

Backend stack: FastAPI, Pydantic v2, Qiskit 1.x, Qiskit Aer.

---

## Folder structure (backend)

- `backend/main.py` — FastAPI app, routes, CORS, WebSocket, chat endpoint
- `backend/schemas.py` — Pydantic models for requests and responses
- `backend/utils.py` — Parsing, validation, routing, math helpers, QASM shim
- `backend/pipelines/base.py` — Pipeline ABC and common postprocessing
- `backend/pipelines/unitary.py` — Statevector pipeline for unitary circuits
- `backend/pipelines/exact_density.py` — Aer density-matrix pipeline (≤ 8 qubits)
- `backend/pipelines/trajectory.py` — Monte Carlo trajectories for non-unitary circuits
- `backend/start.py` — Dev runner
- `backend/requirements.txt` — Backend deps
- `backend/README.md` — Brief readme (this file is the detailed one)

Tests:
- `tests/backend/test_api.py` — API tests (health, simulate, CORS, WS)
- `tests/circuits/test_circuits.py` — Circuit samples and expectations
- `tests/run_tests.py` — Unified test runner

---

## Quick start

- Install deps (use venv recommended):

```bash
python3 -m pip install -r backend/requirements.txt
```

- Run the API:

```bash
python3 backend/start.py
# or
python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

- Health check:

```bash
curl http://localhost:8000/health
```

---

## API overview

### GET `/`
Returns basic info and available pipelines.

### GET `/health`
Returns status, timestamp, available pipelines, and whether chat is configured.

### POST `/simulate`
Routes a QASM2 circuit to the best pipeline and returns per-qubit reduced density matrices (RDM), Bloch vectors, and purity.

Request (`schemas.SimulationRequest`):
- `qasm_code: str` (OpenQASM 2.0)
- `shots: int = 1024` (trajectory only)
- `pipeline_override: Optional["unitary"|"exact_density"|"trajectory"]`
- `options: dict = {}`

Response (`schemas.SimulationResponse`):
- `qubits: List[QubitState]` — per-qubit results
- `pipeline_used: str`
- `execution_time: float` — seconds
- `shots_used: int`
- `circuit_info: dict` — summary

`QubitState` fields:
- `id: int`
- `bloch_coords: [x, y, z]`
- `purity: float` (Tr(ρ²))
- `density_matrix: 2x2` where each complex is `[re, im]`
- `label: str`

Example request:

```json
{
  "qasm_code": "OPENQASM 2.0;\ninclude \"qelib1.inc\";\nqreg q[2];\nh q[0];\ncx q[0], q[1];",
  "shots": 1024
}
```

### WebSocket `/ws/simulate`
Streaming simulation with progress; sends final results at completion. Message types are defined in `schemas.py`.

### POST `/chat/completions`
Optional Gemini-based helper; requires `GOOGLE_API_KEY` and `google-generativeai`.

---

## CORS and limits

Defined in `backend/main.py`:
- CORS is permissive (dev): `*` origin, GET/POST/OPTIONS, `Content-Type` header.
- Extra HTTP middleware adds CORS headers even when Origin is absent; handles bare OPTIONS requests.

Limits (enforced in simulate):
- Max qubits: 24 (hard cap)
- Max operations: 1000
- Max shots: 100,000
- Timeout: 300s per request

---

## Parsing, validation, routing (utils.py)

### Supported gates and non-unitary ops

```python
SUPPORTED_GATES = {
  'h','x','y','z','s','t','sdg','tdg','sx','id','rx','ry','rz','u','u1','u2','u3','p',
  'cx','cy','cz','ch','swap','ccx',
  'measure','reset'
}
NON_UNITARY_OPS = {'measure','reset'}
```

Notes:
- `barrier` treated as unitary no-op.
- A shim expands `cry(angle)` into qelib1-compatible `ry/cx/ry/cx` before parsing.

### QASM shim (expanding cry)

`cry(theta) q[a],q[b];` becomes:

```
ry(theta/2) q[b];
cx q[a], q[b];
ry(-theta/2) q[b];
cx q[a], q[b];
```

### Validation
- Syntax and header (`OPENQASM 2.0; include "qelib1.inc";`)
- Counts: qubits/ops within limits
- Gate whitelist enforced; errors collected
- Empty circuit is allowed (identity)

### Routing

`route_circuit(circuit, shots, force_pipeline)`:
- If override is provided: use it.
- Else:
  - Unitary and qubits ≤ 20 → `unitary`
  - Non-unitary and qubits ≤ 8 → `exact_density`
  - Non-unitary and 9–16 → `trajectory`
  - Non-unitary > 16 → `trajectory`

---

## Math reference

- Pure state density matrix: ρ = |ψ⟩⟨ψ|
- Purity: P = Tr(ρ²) ∈ [0, 1]
- Bloch from 2×2 ρ:
  - x = 2 Re(ρ₀₁)
  - y = −2 Im(ρ₀₁)
  - z = ρ₀₀ − ρ₁₁
- Partial trace (single-qubit A from ρ over B):

  ρᴬ[i,j] = Σ_k ρ[(i,k), (j,k)]

- Vectorized per-qubit RDM from statevector (qubit 0 is LSB):
  1) reshape |ψ⟩ to (2,)*n
  2) move target axis to front, flatten to 2×(2ⁿ⁻¹)
  3) ρ = V Vᴴ; hermitize and normalize

---

## Pipelines

All pipelines return per-qubit results with keys: `bloch`, `purity`, `rho` and aggregate `execution_time`.

Common behaviors (`pipelines/base.py`):
- Allows empty circuits
- Postprocess: clamp purity to [0,1], normalize Bloch if slightly >1 due to numeric noise

### Unitary pipeline — `pipelines/unitary.py`

- `Statevector.from_instruction(circuit)`
- Per-qubit 2×2 RDM via reshape+matmul (O(2ⁿ)):

```python
def _rdm_from_statevector(state_vector, n_qubits, target_qubit):
    if n_qubits == 1:
        v = state_vector.reshape(2,1)
        return (v @ v.conj().T)
    shape = (2,) * n_qubits
    target_axis = n_qubits - 1 - target_qubit  # little-endian mapping
    axes = (target_axis,) + tuple(i for i in range(n_qubits) if i != target_axis)
    V = state_vector.reshape(shape).transpose(axes).reshape(2, -1)
    rho = V @ V.conj().T
    rho = 0.5 * (rho + rho.conj().T)
    rho = rho / np.trace(rho).real
    return rho.astype(np.complex128)
```

- Bloch/purity from `utils.py`
- Routed for unitary circuits with ≤ 20 qubits

Contract
- Inputs: `QuantumCircuit` that contains no non-unitary ops (`measure`/`reset`), `shots` ignored.
- Output: dict of per-qubit 2×2 RDMs, Bloch vectors, purities, and total execution time.
- Limits: routed when qubits ≤ 20; complexity O(2ⁿ) memory/time.
- Failure modes: circuit includes non-unitary ops; exceeds global limits; numerical instability on very large n.

Algorithm details
- Statevector construction: `Statevector.from_instruction(circuit)`.
- Endianness: little-endian with qubit 0 as least-significant bit; target axis index is `n_qubits - 1 - target_qubit`.
- RDM per qubit: reshape → transpose → flatten to 2×(2ⁿ⁻¹) then `rho = V @ Vᴴ`; hermitize and normalize to trace 1.
- Metrics: Bloch and purity via helpers, then postprocess clamps/normalizes for numerical hygiene.

Edge cases
- Empty circuit → |0…0⟩; RDM = |0⟩⟨0| per qubit; purity=1; Bloch=[0,0,1].
- Barrier ops are allowed and ignored for state evolution.
- Very deep circuits may trigger Qiskit transpiler overhead; statevector path bypasses transpile for most ops.

Complexity
- Time: O(2ⁿ) for state, O(n·2ⁿ) to compute all per-qubit RDMs.
- Memory: O(2ⁿ) complex amplitudes.

### Exact density pipeline — `pipelines/exact_density.py`

- For non-unitary circuits ≤ 8 qubits, uses Qiskit Aer density-matrix backend:

```python
sim = AerSimulator(method='density_matrix')
circ = circuit.copy(); circ.save_density_matrix()
tcirc = transpile(circ, sim)
result = sim.run(tcirc, shots=1).result()
dm_array = np.array(result.data(0)['density_matrix'], dtype=np.complex128)
```

- Partial trace per qubit via Qiskit:

```python
dm_qi = DensityMatrix(dm_array)
qubits_to_trace = [j for j in range(n_qubits) if j != i]
rho = dm_qi.partial_trace(qubits_to_trace).data if qubits_to_trace else dm_array
```

- Manual einsum fallback available
- Hermitize and normalize ρ
- Hard cap: 8 qubits

Contract
- Inputs: `QuantumCircuit` with unitary and/or non-unitary ops; `shots` ignored.
- Output: per-qubit 2×2 RDMs, Bloch, purities, and timing.
- Limits: ≤ 8 qubits (density matrix is 2ⁿ×2ⁿ); memory/time O(4ⁿ).
- Failure modes: Aer not installed/available; circuit or backend error; exceeding cap.

Algorithm details
- Uses Aer density-matrix method and `save_density_matrix()` to capture final global ρ.
- Transpiles to the Aer backend and runs with `shots=1` (shots irrelevant for density outcomes).
- Per-qubit RDMs via `DensityMatrix.partial_trace` (Qiskit) for robust indexing and correctness.
- Manual fallback computes partial trace via einsum when Qiskit path is unavailable.
- Enforces Hermiticity and unit trace post-extraction.

Edge cases
- Mixed states from measurement/reset are exactly represented.
- Single-qubit circuits skip trace-out and reuse the global ρ directly.
- Rounding: small imaginary parts on diagonals and sub-1 traces are corrected via hermitize+normalize.

Complexity
- Time and memory dominated by 4ⁿ scaling; practical n≤8 on typical dev machines.

### Trajectory pipeline — `pipelines/trajectory.py`

- Monte Carlo trajectories simulate non-unitary behavior:
  - Apply unitaries
  - Measurement: sample outcome probabilities and collapse
  - Reset: project to |0⟩ and renormalize
- Per-trajectory per-qubit RDM computed as in unitary; averaged across shots
- Shots clamped to [100, 100000]
- Recommended when non-unitary > 8 and ≤ 16 qubits

Contract
- Inputs: `QuantumCircuit` (may include `measure`/`reset`), `shots` for number of trajectories.
- Output: averaged per-qubit RDMs, Bloch, purities, timing, `shots_used` may be clamped.
- Limits: typically ≤ 16 qubits; accuracy improves with shots.
- Failure modes: insufficient shots cause noisy estimates; unsupported custom ops.

Algorithm details
- Evolves a pure state per trajectory; applies each instruction sequentially.
- Measurement: compute marginal p(|0⟩), p(|1⟩), sample an outcome, collapse amplitudes, renormalize.
- Reset: project target qubit to |0⟩ by zeroing |1⟩ amplitudes and renormalize.
- Per-trajectory per-qubit RDM via the same vectorized method as in unitary; averages across all shots.
- Optional random seed can stabilize results across runs (if exposed in options).

Edge cases
- Purely unitary circuits will work but routing avoids this pipeline unless forced.
- Conditional/classical ops are applied if representable; classical memory register values aren’t returned in response.
- Shots below the clamp may be auto-increased to ensure basic stability.

Complexity
- Time: O(shots · 2ⁿ) plus per-qubit RDM extraction per shot.
- Memory: O(2ⁿ) for current state; low overhead for accumulators.

### Routing

All pipelines return per-qubit results with keys: `bloch`, `purity`, `rho` and aggregate `execution_time`.

Common behaviors (`pipelines/base.py`):
- Allows empty circuits
- Postprocess: clamp purity to [0,1], normalize Bloch if slightly >1 due to numeric noise

Routing details
- Unitary detection: no instruction belongs to `NON_UNITARY_OPS = {'measure','reset'}`.
- Gate whitelist: names must be in `SUPPORTED_GATES`; others produce validation errors.
- Override: `pipeline_override` forces selection (subject to global caps and availability).
- Shots usage: ignored by unitary/exact_density; applied (clamped) by trajectory.

Examples
- 6-qubit circuit with mid-circuit measurement → exact_density.
- 12-qubit circuit with several resets → trajectory (shots averaged).
- 18-qubit purely unitary circuit → unitary (≤20 threshold).
- 21-qubit unitary → rejected by limits (reduce size or partition the problem).

---

## Math reference

- Pure state density matrix: ρ = |ψ⟩⟨ψ|
- Purity: P = Tr(ρ²) ∈ [0, 1]
- Bloch from 2×2 ρ:
  - x = 2 Re(ρ₀₁)
  - y = −2 Im(ρ₀₁)
  - z = ρ₀₀ − ρ₁₁
- Partial trace (single-qubit A from ρ over B):

  ρᴬ[i,j] = Σ_k ρ[(i,k), (j,k)]

- Vectorized per-qubit RDM from statevector (qubit 0 is LSB):
  1) reshape |ψ⟩ to (2,)*n
  2) move target axis to front, flatten to 2×(2ⁿ⁻¹)
  3) ρ = V Vᴴ; hermitize and normalize

---

## Utilities (`utils.py`)

- `parse_and_validate_circuit(qasm_code)` — parse with `qasm2.loads`, apply CRY shim, validate, return circuit and metadata
- `route_circuit(circuit, shots, force_pipeline)` — routing policy
- `compute_bloch_vector(rho)` — x,y,z per formulas above
- `compute_purity(rho)` — real trace of ρ²
- `partial_trace_qubit(...)` — bitmask-based fallback partial trace from statevector
- `clip_tiny_values(...)` — numeric hygiene when formatting
- `PRESET_CIRCUITS` — sample QASM strings

---

## Schemas (`schemas.py`)

- `SimulationRequest` — QASM presence, shot bounds
- `QubitState` — 2×2 density matrix as `[[re,im], ...]`, validates shape and unit trace
- `SimulationResponse` — qubits, pipeline_used, timings, circuit_info
- Streaming and chat message models

Density matrix JSON example (2×2 identity/2):

```json
[[[0.5,0.0],[0.0,0.0]], [[0.0,0.0],[0.5,0.0]]]
```

---

## Endpoints (`main.py`)

- `/health` — simple diagnostics
- `/simulate` — parse → route → limit checks → run pipeline (timeout 300s) → format response
- `/ws/simulate` — accepts start message with QASM + shots; streams progress and final
- `/chat/completions` — optional, calls Gemini if configured

Error handling:
- Uses HTTPException with consistent JSON error payloads

CORS:
- `CORSMiddleware` + extra middleware to always set headers and handle OPTIONS

---

## Performance and precision

- Complexity:
  - Statevector: O(2ⁿ)
  - Density matrix: O(4ⁿ)
- Routing caps tuned for practicality: unitary ≤ 20, exact_density ≤ 8, trajectory up to ~16
- Numeric hygiene:
  - Hermitize ρ: ½(ρ + ρᴴ)
  - Normalize to unit trace
  - Clip tiny values when serializing
  - Clamp/normalize Bloch vector in postprocess

---

## Testing

Run backend tests:

```bash
python3 tests/run_tests.py --backend-only --backend-url http://localhost:8000 --auto-start -v
```

Covers:
- Health, simulate happy paths (Bell/GHZ/rotations/identity)
- Invalid circuits (syntax, unsupported gates, limits)
- Non-unitary circuits routed to exact_density (≤ 8 qubits)
- Performance scenarios
- WebSocket probe
- CORS headers on OPTIONS and normal responses

Frontend UI tests require Chrome/ChromeDriver; see `tests/test_requirements.txt`.

---

## Extending

- New gate: add to `SUPPORTED_GATES`; if QASM parser lacks it, add a shim (see CRY)
- Adjust routing: edit `route_circuit` thresholds and per-pipeline caps
- New pipeline: implement `SimulationPipeline` in `backend/pipelines/`, register in `main.py`, add tests
- Keep density matrices JSON-safe as `[re, im]`; update schemas if structure changes

---

## Appendix — Key symbols by file

- `backend/main.py`
  - `app: FastAPI`
  - Endpoints: `/`, `/health`, `/simulate`, `/chat/completions`, `/ws/simulate`
  - `PIPELINES = {"unitary": UnitaryPipeline(), "exact_density": ExactDensityPipeline(), "trajectory": TrajectoryPipeline()}`
  - CORS + extra headers middleware

- `backend/schemas.py`
  - `SimulationRequest`, `SimulationResponse`, `QubitState`
  - Validators for density matrix shape and trace

- `backend/utils.py`
  - `parse_and_validate_circuit`, `route_circuit`
  - `SUPPORTED_GATES`, `NON_UNITARY_OPS`
  - `compute_bloch_vector`, `compute_purity`, `partial_trace_qubit`, `clip_tiny_values`
  - CRY shim implementation

- `backend/pipelines/base.py`
  - `SimulationPipeline` ABC; `validate_circuit`, `postprocess_results`

- `backend/pipelines/unitary.py`
  - Statevector simulation; vectorized per-qubit RDM

- `backend/pipelines/exact_density.py`
  - Aer density matrix simulation; per-qubit partial trace

- `backend/pipelines/trajectory.py`
  - Monte Carlo simulation; measurement collapse and reset

- `backend/start.py`
  - Dev launcher (uvicorn with reload)

- `backend/requirements.txt`
  - FastAPI, Qiskit, Qiskit Aer, Numpy, Pydantic, Uvicorn, etc.
