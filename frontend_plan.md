# Quantum State Visualizer — Frontend Implementation Guide

This document provides a detailed guide for implementing the frontend of the Quantum State Visualizer MVP. It builds on the overall project architecture, incorporating all design decisions from the project plans (v3 and v4), the detailed implementation overview, identified issues, and optimizations. The focus is on architectural overviews, step-by-step guides, UI/UX considerations, performance strategies, and extensibility for stretch goals. No code snippets are included; instead, descriptions emphasize design rationale and how to address potential issues.

The frontend is built with React (using Vite and TypeScript), ensuring a responsive, interactive experience for visualizing quantum states. Key design decisions prioritize modularity, performance for large qubit counts (up to n=24), and user intuition for quantum concepts like mixed states and entanglement.

## 1. Frontend Overview and Architecture

### 1.1 High-Level Goals

The frontend handles user input for quantum circuits, displays validation feedback, triggers simulations via API/WebSockets, and renders interactive Bloch spheres for each qubit's state. It emphasizes intuitive visualization: spheres show Bloch vectors with length indicating purity, and an inspector provides detailed data.

Design Decisions:

- Use a single-page application (SPA) structure for seamless interactions, avoiding page reloads during simulations.
- Responsive design with Tailwind CSS to adapt to desktop, tablet, and mobile screens, ensuring usability for students and researchers.
- Global state management to synchronize UI components efficiently, reducing prop drilling.

### 1.2 Component Hierarchy and Data Flow

The app is composed of top-level components wrapped in providers for state and API querying. Data flows from user input (EditorPanel) to backend triggers (ControlsBar), then to visualization (CanvasGrid and Inspector).

Main Components:

- **App**: Root component that sets up providers (Zustand for state, TanStack Query for API caching) and routes. It includes a top bar for navigation and a settings modal.
- **EditorPanel**: Handles circuit input via presets dropdown, QASM text area (upgraded to a full-featured editor like Monaco or CodeMirror with syntax highlighting), and basic drag-and-drop for gates.
- **CanvasGrid**: Renders the grid of Bloch spheres, optimized for performance.
- **Inspector**: Side panel for detailed qubit data, selectable via click on spheres.
- **ControlsBar**: Bottom controls for simulation actions (Run, Step, Pause), sliders (speed, shots), and toggles (endianness, accuracy mode).

Design Decisions:

- Separate concerns: Input/validation in EditorPanel, visualization in CanvasGrid, controls in ControlsBar, to allow independent testing and extension.
- Use Zustand for lightweight global state (over Redux) due to its simplicity and low boilerplate, suitable for this mid-sized app.
- TanStack Query for API interactions to handle caching, retries, and optimistic updates, addressing potential network issues.

#### UML Diagram Description (Mermaid-Compatible Text Representation)

The component hierarchy can be visualized as:

- App as the root.
- App contains EditorPanel, CanvasGrid, Inspector, and ControlsBar.
- CanvasGrid contains multiple BlochSphere instances.
- Zustand store is injected via providers at the App level.

This hierarchy ensures scalability: For stretch goals like shareable links, parse URL params in App on mount.

## 2. UI Features and Design

### 2.1 Input and Validation

- Preset dropdown offers famous circuits (e.g., Bell, GHZ) for quick demos.
- QASM editor supports OpenQASM 2.0 pasting/validation, with real-time feedback (e.g., qubit count, op count, unitary/non-unitary classification).
- Graphical editor: Basic drag-and-drop for essential gates, with validation to prevent invalid circuits.

Design Decisions:

- Default to "Averaged" ensemble view, with a toggle for advanced "Conditioned" states (stretch goal placeholder).
- Prominent qubit mapping banner (e.g., "Top wire = Q0") with endianness toggle to avoid misinterpretation.
- Validation panel shows warnings for non-unitary ops or unsupported gates, addressing security and usability issues by sanitizing inputs before backend calls.

### 2.2 Visualization

- **Bloch Sphere Design**: Each sphere uses React Three Fiber (r3f) + drei for 3D rendering. Displays a vector arrow (direction: Bloch coordinates rx, ry, rz; length: sqrt(2*purity - 1)), axis gridlines, purity ring/label, and a translucent shell for mixedness (when purity < 1).
- Grid layout: Responsive CSS Grid (e.g., 2-4 columns based on screen width) for spheres.
- Inspector: Shows selected qubit's 2x2 reduced density matrix (as a table), Bloch coordinates, purity (to 3 decimals), and copy buttons.

Design Decisions:

- Hover tooltips on spheres for quick rho and coordinates, enhancing interactivity.
- Numerical stability: Clip tiny negatives in display (e.g., ≤1e-12 shown as 0) to match backend and avoid confusing users.
- For large n (>8), auto-switch to compact mode: Smaller spheres, static views (no per-sphere controls), or tabbed groups to prevent crowding.

### 2.3 Controls and Settings

- Simulation buttons: Run for full sim, Step/Previous for gate-by-gate (via WebSockets, stretch goal).
- Sliders/toggles: Speed for animations, shots for trajectory mode, accuracy vs. speed presets.
- Settings modal: Endianness, precision, WebSocket endpoints, compact view toggle.

Design Decisions:

- Pipeline badges (e.g., "Exact" or "Estimated (S=500)") and uncertainty indicators (e.g., error ~1/sqrt(S)) in the UI to communicate simulation mode and reliability.
- Progress indicators (spinners on spheres) during runs, with estimated times based on n and pipeline.

## 3. Performance Optimizations and Issue Resolutions

Several potential frontend issues were identified (e.g., rendering lag, crowding for large n, WebSocket errors, display precision). These are addressed through targeted design decisions.

### 3.1 Bloch Sphere Rendering for Large n (>8)

- **Crowding Mitigation**: Use a scrollable, virtualized grid (via react-window) to render only visible spheres, allowing users to scroll through all without overwhelming the screen. For n>8, enable subset selection (multi-select dropdown) to filter displayed qubits, and group into tabs (e.g., Q0-7, Q8-15) for progressive disclosure.
- **Performance Boost**: Consolidate all spheres into a single Canvas element (one WebGL context) to share resources and reduce overhead. Position spheres in a 2D grid within the 3D scene. Use instancing for shared geometries (e.g., batch spheres and arrows into few draw calls) to handle n=24 efficiently.
- **Dynamic Adjustments**: Integrate performance monitoring to auto-degrade quality (e.g., lower polygon count, disable antialiasing) on low FPS. Set frameloop to "demand" for updates only on changes. For extreme cases (n>16), offer a 2D fallback toggle (SVG-based vectors) that's lighter and less cluttered.
- Design Rationale: These ensure >30 FPS on mid-range devices, tested via monitoring tools. Addresses lag from multiple Canvases and clutter by focusing on overview-first UX.

### 3.2 Other Frontend Issues Addressed

- **WebSocket Handling**: Use a reconnecting WebSocket client to manage disconnections during long simulations. Include error handling (e.g., UI alerts for failures) and progress events to update state in real-time, preventing silent failures.
- **Inspector Display**: Format numerical values with consistent precision (e.g., 3 decimals for purity, clipped negatives) to avoid visual inconsistencies and user confusion.
- **API Integration Issues**: TanStack Query handles caching for repeated sims and retries for flaky networks, reducing unnecessary backend load.
- **General React Optimizations**: Memoize components to prevent unnecessary re-renders, especially in CanvasGrid. Avoid inline functions in renders to maintain performance.

These resolutions make the frontend robust, with built-in fallbacks for edge cases.

## 4. State Management

Zustand store manages:

- Qubit states (array of objects with index, bloch coords, rho, purity).
- Simulation metadata (status: idle/running/paused/done; pipeline type).
- UI settings (endianness, accuracy mode, shots, selected qubits for filtering).

Design Decisions:

- Actions for updating qubits, status, etc., ensure reactive updates.
- Extensible for stretch goals (e.g., add fields for conditioned outcomes or step snapshots).

## 5. Testing and DevOps Integration

- Unit tests for components (e.g., render BlochSphere with known states).
- Integration tests for data flows (input to visualization).
- Performance monitoring in dev mode (FPS, memory) to validate optimizations.
- CI with GitHub Actions for linting (ESLint/Prettier) and tests.

## 6. Stretch Goals and Placeholders

The architecture supports easy additions:

- **Step-by-Step Execution**: WebSocket listeners in ControlsBar update state on 'snapshot' events; add incremental rendering in CanvasGrid.
- **Shareable Links**: Parse serialized circuit from URL in App; store current view options.
- **Conditioned View**: Toggle in ControlsBar sends 'condition' messages via WebSocket; filter/update qubit states accordingly.
- **Enhanced Editor**: Modular EditorPanel allows swapping to advanced editors without affecting other components.

Placeholders include optional flags in store/UI (e.g., 'stepMode: boolean') and extensible API hooks.

This guide ensures a performant, user-friendly frontend aligned with the project's quantum visualization goals. Implement in phases: Skeleton (D1), Core UI (D2), Optimizations (D3), Testing (D4+).
