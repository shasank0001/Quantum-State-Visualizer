# Quantum State Visualizer - Detailed Implementation Guide for Developers

This document provides a comprehensive implementation guide for building the Quantum State Visualizer MVP, based on the provided project plan (v3). It focuses on architectural overviews, step-by-step implementation guides, and ensures extensibility for stretch goals. The architecture is designed to be modular, with clear separation of concerns (e.g., simulation pipelines as pluggable modules, WebSocket handlers for real-time features) to facilitate easy addition of advanced features later.

The guide assumes familiarity with the tech stack (no version constraints specified). Where relevant, UML diagrams are described using Mermaid syntax for easy rendering in Markdown viewers like GitHub or VS Code.

## 1. Project Overview and Architecture

### 1.1 Mission and Scope

The Quantum State Visualizer is a web-based tool for visualizing quantum states of multi-qubit circuits on Bloch spheres. It supports input via presets, QASM code, or a graphical editor; routes circuits to efficient simulation pipelines; and provides interactive 3D visualizations. The MVP focuses on core simulation and visualization, with hooks for stretch goals like step-by-step execution and conditioned views.

### 1.2 High-Level Architecture Overview

The system follows a client-server architecture:

* **Frontend:** Handles UI, user input, state management, and rendering. Communicates with the backend via REST API for full simulations and WebSockets for real-time/step-by-step features.
* **Backend:** Parses circuits, routes to simulation pipelines, computes RDMs and Bloch vectors, and streams results.
* **Data Flow:** User inputs circuit → Validation → Routing → Simulation → Results → Visualization.

**UML Diagram: High-Level System Architecture (Mermaid Syntax)**

```
graph TD
    subgraph Frontend [Frontend - Handles UI and Visualization]
        A[React Components: EditorPanel, CanvasGrid, Inspector, ControlsBar]
        B[State Management: Zustand]
        C[API Client: TanStack Query]
        D[3D Rendering: React Three Fiber + drei]
        E[WebSocket Client]
    end

    subgraph Backend [Backend - Handles Computation and Routing]
        F[Simulation Routes: FastAPI Router (/simulate)]
        G[WebSocket Endpoint: /ws/simulate]
        H[Circuit Parser/Validator]
        I[Router Logic]
    end

    subgraph SimulationPipelines [Simulation Pipelines]
        J[UnitaryPipeline]
        K[ExactDensityPipeline]
        L[TrajectoryPipeline]
    end

    Frontend -- REST API / WebSocket --> Backend
    Backend -- Routes Circuit --> SimulationPipelines

```

This modular design allows easy extension: e.g., add new pipelines by subclassing a base `SimulationPipeline` interface, or hook WebSocket events for stretch features like conditioned states.

## 2. Technology Stack

* **Frontend:** React (Vite + TypeScript), React Three Fiber (r3f) + drei for 3D, Zustand for global state, TanStack Query for API caching, Monaco/CodeMirror for QASM editor, Tailwind CSS for styling.
* **Backend:** FastAPI (Python) + uvicorn; Qiskit for quantum logic; NumPy for computations; optional Numba for optimizations.
* **Real-Time:** WebSockets for streaming.
* **DevOps:** Docker for containerization, GitHub Actions for CI/CD, testing with pytest (backend) and Jest/Vitest (frontend).

**Assumptions:** Use latest stable versions (e.g., Qiskit 1.x, React 18+). No internet dependencies beyond local libs.

## 3. Frontend Implementation

### 3.1 Step-by-Step Guide

1. **Setup Project Skeleton:**
   * Initialize with Vite: `npm create vite@latest --template react-ts`.
   * Install dependencies: `npm i @react-three/fiber @react-three/drei zustand @tanstack/react-query monaco-editor tailwindcss postcss autoprefixer`.
   * Configure Tailwind in `tailwind.config.js` and `index.css`.
   * Set up Zustand store in `src/store.ts`.
2. **State Management with Zustand:**
   * Create a global store for app state, simulation results, and UI settings.
   * **Example Store (`src/store.ts`):**
     ```
     import { create } from 'zustand';

     type SimulationStatus = 'idle' | 'running' | 'done' | 'error';
     type PipelineType = 'unitary' | 'exact_density' | 'trajectory';

     interface AppState {
       qasm: string;
       status: SimulationStatus;
       pipeline: PipelineType;
       results: Record<number, { bloch: [number, number, number], purity: number }>;
       setQasm: (qasm: string) => void;
       runSimulation: () => void; // Placeholder for API call logic
     }

     export const useStore = create<AppState>((set) => ({
       qasm: '// Start writing your QASM code here',
       status: 'idle',
       pipeline: 'unitary',
       results: {},
       setQasm: (qasm) => set({ qasm }),
       runSimulation: () => { /* ... */ },
     }));

     ```
   * This store is extensible for stretch goals (e.g., add `conditionedOutcome: string` for conditioned views).
3. **UI Components:**
   * **EditorPanel:** Use Monaco for QASM editing. Integrate presets dropdown (e.g., Bell State QASM strings). Validate on change via API call.
   * **CanvasGrid:** Wrap r3f `<Canvas>`. Use CSS Grid for responsive layout (e.g., 2-4 spheres per row based on screen size).
   * **BlochSphere Component (r3f):**
     * Use drei's `<Sphere>`, `<ArrowHelper>` for vector, `<OrbitControls>` for interaction.
     * Render mixedness as a scaled translucent sphere (radius = 1 - purity).
     * **Example Snippet:**
       ```
       import { Sphere, OrbitControls, ArrowHelper } from '@react-three/drei';
       import { Canvas } from '@react-three/fiber';
       import * as THREE from 'three';

       function BlochSphere({ bloch, purity }) {
         const vector = new THREE.Vector3(...bloch);
         return (
           <>
             <Sphere args={[1, 32, 32]}>
               <meshStandardMaterial wireframe color="gray" />
             </Sphere>
             <ArrowHelper args={[vector.normalize(), new THREE.Vector3(0,0,0), vector.length(), '#ff0000']} />
             {/* Translucent sphere for mixedness */}
             <Sphere args={[1 - purity, 32, 32]}>
                <meshStandardMaterial transparent opacity={0.3} color="lightblue" />
             </Sphere>
             <OrbitControls />
           </>
         );
       }

       ```
     * Sync cameras across spheres optionally via shared state.
   * **Inspector:** Display selected qubit's rho as a table, bloch coords as list.
   * **ControlsBar:** Buttons for Run/Step, sliders for speed/shots. Hook to WebSocket for step mode.
4. **API Integration:**
   * Use TanStack Query for REST: e.g., `useMutation` for `/simulate`.
   * **WebSocket Client:** Use native WebSocket API or a lib like `reconnecting-websocket`. Listen for 'progress', 'snapshot', 'done' events and update Zustand store.

**UML Diagram: Frontend Component Hierarchy (Mermaid)**

```
graph TD
    App --> EditorPanel
    App --> CanvasGrid
    App --> Inspector
    App --> ControlsBar
    CanvasGrid --> BlochSphere

```

## 4. Backend Implementation

### 4.1 Step-by-Step Guide

1. **Setup Project Skeleton:**
   * Initialize FastAPI: `pip install fastapi uvicorn qiskit numpy numba`.
   * Create `main.py` with `app = FastAPI()`.
   * Dockerize: Multi-stage Dockerfile (build + runtime).
2. **Circuit Parsing and Validation:**
   * Use Qiskit to parse QASM: `from qiskit import QuantumCircuit; circuit = QuantumCircuit.from_qasm_str(qasm)`.
   * **Validator:** Check gate whitelist (H, X, Z, S, T, CNOT, CZ, measure, reset). Count qubits/ops. Classify as unitary if no measure/reset/noise.
3. **Router Implementation:**
   * Implement as a function (see plan's pseudocode).
   * **Example:**
     ```
     from qiskit import QuantumCircuit

     def route_circuit(circuit: QuantumCircuit, shots: int) -> str:
         is_unitary = all(op.name not in ['measure', 'reset'] for op, _, _ in circuit.data)
         op_count = len(circuit.data)
         qubit_count = circuit.num_qubits

         if is_unitary and qubit_count <= 20:
             return 'unitary'
         elif not is_unitary and qubit_count <= 16 and shots > 1000:
             return 'trajectory'
         else:
             return 'exact_density'

     ```
4. **Simulation Pipelines:**
   * **Base Interface:** Define an abstract class for pipelines to ensure extensibility.
     ```
     from abc import ABC, abstractmethod

     class SimulationPipeline(ABC):
         @abstractmethod
         def run(self, circuit, shots):
             pass

     ```
   * **Unitary Pipeline:**
     * Simulate statevector: `from qiskit.quantum_info import Statevector; sv = Statevector.from_instruction(circuit)`.
     * Compute RDM per qubit: Vectorized NumPy loop over basis.
     * Bloch calc: `rx = 2 * np.real(rho[0,1])`, `ry = -2 * np.imag(rho[0,1])`, `rz = rho[0,0] - rho[1,1]`.
     * Purity: `np.trace(np.dot(rho, rho))`.
   * **Exact Density Pipeline:**
     * Use `from qiskit.quantum_info import DensityMatrix; dm = DensityMatrix.from_instruction(circuit)`.
     * Partial trace: `dm.partial_trace([j for j in range(n_qubits) if j != i])`.
   * **Trajectory Pipeline:**
     * Loop `S` times: Simulate with stochastic collapses (use Qiskit's Aer simulator with `shots=1` per trajectory).
     * Average RDMs.
5. **API and WebSocket:**
   * **REST:** `@app.post("/simulate")` - Parse request, route, return JSON.
   * **WebSocket:** `@app.websocket("/ws/simulate")` - Accept connection, handle 'start', stream snapshots via `ws.send_json({"type": "snapshot", ...})`.
   * **Security:** Limit qubits/ops/shots, timeout with `asyncio.timeout`.

**UML Diagram: Backend Pipelines (Mermaid)**

```
graph TD
    Router -- Selects and Runs --> SimulationPipeline
    SimulationPipeline <|-- UnitaryPipeline
    SimulationPipeline <|-- ExactDensityPipeline
    SimulationPipeline <|-- TrajectoryPipeline

```

## 5. Testing Strategy

* **Unit Tests:** Golden tests for known circuits (e.g., Bell: assert bloch vectors match [0,0,1] for pure states).
* **Property Tests:** Use Hypothesis to generate random circuits, assert `Tr(rho)==1`, eigenvalues `>= 0`.
* **Integration:** Test full API flows, WebSocket streaming.
* **Performance:** Benchmark with `timeit` for n=16/20/24.

## 6. Stretch Goals and Placeholders

To ensure easy addition, the architecture includes hooks:

* **Trajectory Sampling:** Already in MVP; extend with user-configurable `S`.
* **Step-by-Step Execution:** WebSocket has 'snapshot' events - add gate-by-gate simulation in pipelines (e.g., apply gates incrementally, compute RDM after each).
  * **Placeholder:** In pipelines, add `step_run(self, circuit, step_index)` method.
* **Shareable Links:** Use URL params for serialized QASM (base64 encode).
  * **Placeholder:** In frontend, add `useEffect` to parse URL on load.
* **Conditioned State View:** Add toggle in UI/store; on WebSocket, send 'condition' message. Backend: Simulate conditioned branches in trajectory pipeline.
  * **Placeholder:** Extend router to accept `'conditioned_outcome'` option; pipelines check and collapse accordingly.
* **Enhanced QASM Editor:** Swap Monaco for CodeMirror if needed - already modular in `EditorPanel`.

If a feature is hard to add retroactively (e.g., WebSockets for streaming), it's baked into MVP with optional flags.

## 7. Deployment and Notes

* **Docker:**
  * Build image: `docker build -t qsv .`
  * Run: `docker run -p 8000:8000 qsv`
* **Correctness:** Always clip negatives, use default endianness with toggle.
* **Extensibility:** All components are modular; add new pipelines/UI views without refactoring core.
