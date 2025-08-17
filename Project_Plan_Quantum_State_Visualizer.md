# Project Plan: Quantum State Visualizer (v4)(final)

## 1. Project Title

**Working Title:** Quantum State Visualizer

**Alternative Names:** Q-Sphere Explorer, EntangleView, The Bloch Party

## 2. Mission Statement / The Elevator Pitch

To develop a web-based tool that demystifies quantum entanglement and mixed states. The application will accept multi-qubit quantum circuits, intelligently route them through the most efficient simulation pipeline, and provide an intuitive, interactive visualization of each qubit's state on a Bloch Sphere. This helps users *see* the difference between pure, mixed, and conditioned quantum states.

## 3. Target Audience

* **Primary:** Students learning Quantum Computing who need to build intuition about quantum states and entanglement.
* **Secondary:** Quantum Researchers/Developers who need a quick tool to debug or visualize the state of individual qubits within a larger circuit.

## 4. Core Features (Minimum Viable Product for 10-Day Sprint)

These are the essential features for the initial successful launch.

### Circuit Input & Validation:

* **Preset Circuits:** A dropdown menu with famous circuits (e.g., Bell State, GHZ State) to provide instant, interesting visualizations.
* **Code Input:** A simple `<textarea>` where a user can paste OpenQASM 2.0 code.
* **Graphical Editor:** A basic drag-and-drop UI for essential gates (H, X, Z, S, T, CNOT, CZ).
* **Validation:** The backend will validate all circuits, count qubits and operations, and classify them as either *unitary-only* or *non-unitary* (containing measurements, resets, etc.).

### Simulation Backend & Routing:

* **Smart Routing:** The backend will automatically route circuits to the correct simulation pipeline based on its properties.
* **Unitary Pipeline (Fast Path):** For circuits with no non-unitary operations, this pipeline calculates the final statevector |ψ⟩ and computes each qubit's RDM directly for maximum speed and scalability (up to ~24 qubits). This avoids building the full, slow 4^n density matrix.
* **Exact Density Matrix Pipeline:** For circuits *with* non-unitary operations and a small number of qubits (e.g., n ≤ 9), this pipeline uses Qiskit's DensityMatrix simulator to compute the exact, correct mixed-state results.

### Core Visualization & UI:

* **Bloch Sphere Canvas:** A responsive grid displaying one interactive 3D Bloch Sphere for each qubit, rendered using **React Three Fiber (R3F)** and drei.
* **State Vector Display:** Each sphere will draw the state vector. The vector's length will accurately represent the state's purity (norm = sqrt(2*Tr(ρ²) - 1)).
* **Data Display Inspector:** A panel to show detailed data for a selected qubit, including its 2x2  **reduced density matrix (ρ)** , the  **Bloch vector coordinates (rx, ry, rz)** , and the calculated **Purity** value.
* **Default View:** The UI will default to showing the  **"Averaged" ensemble state** , which represents the average outcome of many circuit executions.

## 5. Advanced Features (High-Priority Stretch Goals)

These features will be prioritized immediately after the MVP is complete and stable.

* **Trajectory Sampling Pipeline:** A Monte-Carlo based engine for simulating non-unitary circuits with too many qubits for the exact density method. This is the highest priority stretch goal.
* **Step-by-Step Execution:** Add "Next" and "Previous" buttons to apply gates one at a time, with state updates streamed to the frontend via **WebSockets** for a live, animated view of the state evolution.
* **Shareable Links:** Implement a feature to generate a URL that serializes the current circuit, allowing users to share their work easily.
* **Conditioned State View:** An advanced toggle allowing users to select a specific measurement outcome (e.g., "010") and see the resulting collapsed ("conditioned") state on the Bloch spheres.
* **Enhanced QASM Editor:** Upgrade the basic `<textarea>` to a full-featured code editor like **Monaco** or  **CodeMirror 6** , with syntax highlighting and validation.

## 6. Technology Stack

* **Frontend:** React (built with Vite), TypeScript, React Three Fiber (R3F) + drei, Zustand (for global state), TanStack Query (for server state/caching), and Tailwind CSS for styling.
* **Backend:** Python with the **FastAPI** framework and uvicorn server.
* **Quantum Logic:** **Qiskit** (for parsing, circuit building, and simulators), **NumPy** (for vectorized calculations), and optional **Numba** for micro-optimizations on the direct RDM calculation loops.
* **Real-time Communication:** **WebSockets** for step-by-step execution streaming and progress updates.
* **DevOps & Infrastructure:** **Docker** for containerization and consistent development environments, with **GitHub Actions** for Continuous Integration (CI) and automated testing.

## 7. API & WebSocket Contract

* **REST API (POST /simulate):** A primary endpoint for running a full circuit simulation and returning the final state of all qubits. The response will indicate which simulation pipeline was used (unitary, exact_density, etc.) and include the Bloch data and density matrix for each qubit.
* **WebSocket API (/ws/simulate):** A persistent connection for step-by-step execution. The client sends a start message, and the server pushes back progress, snapshot, and done events, allowing for a real-time view of the simulation.

## 8. Testing Strategy

* **Golden Unit Tests:** Test key circuits (e.g., |0⟩, |+⟩, Bell, GHZ states) and assert that the calculated RDM and Bloch vectors match their known theoretical values.
* **Property Tests:** Use libraries like Hypothesis to test fundamental physical laws, such as Tr(ρ) = 1 and that ρ is positive semidefinite, across a wide range of random circuits.
* **Integration Tests:** Write tests to ensure the full request/response cycle for both the REST and WebSocket APIs works as expected.
* **Performance Tests:** Benchmark the performance and memory usage of the different simulation pipelines to validate scalability claims.
