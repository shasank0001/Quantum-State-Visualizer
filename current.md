# Quantum State Visualizer - Current Implementation

A comprehensive web-based tool for visualizing quantum circuit states through interactive Bloch sphere representations. This application demystifies quantum entanglement and mixed states by providing intuitive 3D visualizations of multi-qubit quantum circuits.

## 🌟 Project Overview

The Quantum State Visualizer is designed to help students and researchers understand quantum computing concepts by providing visual feedback on quantum states. The application accepts quantum circuits through multiple input methods, automatically routes them to the most efficient simulation pipeline, and renders each qubit's state on an interactive 3D Bloch sphere.

### 🎯 Mission Statement

To develop a web-based tool that demystifies quantum entanglement and mixed states by providing an intuitive, interactive visualization of each qubit's state on a Bloch Sphere, helping users *see* the difference between pure, mixed, and conditioned quantum states.

## ✨ Current Features

### 🔧 Circuit Input & Validation
- **Preset Circuits**: Dropdown menu with famous quantum circuits:
  - Bell State (|Φ+⟩)
  - GHZ State (3-qubit entangled state)
  - Custom preset configurations
- **Code Editor**: 
  - **Simple Editor**: Basic textarea for OpenQASM 2.0 code input
  - **Advanced Editor**: Monaco Editor with full OpenQASM syntax highlighting, themes, and autocomplete
  - **File Upload**: Support for .qasm and .txt files (max 1MB)
- **Real-time Validation**: Live syntax checking and circuit validation with detailed error reporting
- **Visual Editor**: Drag-and-drop interface for essential quantum gates
- **Smooth Transitions**: 700ms animated transitions between visual and code modes

### 🚀 Smart Simulation Backend
- **Intelligent Routing**: Automatically selects the optimal simulation pipeline based on circuit characteristics
- **Circuit Analysis**: Automatic classification of unitary vs non-unitary operations
- **Performance Optimization**: Vectorized NumPy calculations with optional Numba acceleration

#### Pipeline Implementation Details

##### 🔄 Unitary Pipeline (Pure States)
**Use Case**: Circuits with only unitary operations (no measurements/resets) ≤20 qubits
**Algorithm**: Direct statevector simulation with reduced density matrix calculation

**Implementation**:
```python
# 1. Simulate the full quantum circuit to get final statevector |ψ⟩
statevector = Statevector.from_instruction(circuit)
psi = statevector.data  # Complex amplitudes

# 2. For each qubit i, compute reduced density matrix ρᵢ
# Using vectorized partial trace over computational basis
for i in range(n_qubits):
    rho_i = np.zeros((2, 2), dtype=complex)
    # Sum over all basis states, tracing out other qubits
    for basis_state in range(2**n_qubits):
        amp = psi[basis_state]
        bit_i = (basis_state >> i) & 1  # Extract bit at position i
        rho_i[bit_i, bit_i] += abs(amp)**2
        
        # Off-diagonal elements from quantum superposition
        for other_state in range(2**n_qubits):
            if bin(basis_state ^ other_state).count('1') == 1:  # Differ by 1 bit
                diff_bit = (basis_state ^ other_state).bit_length() - 1
                if diff_bit == i:
                    bit_j = (other_state >> i) & 1
                    rho_i[bit_i, bit_j] += amp * np.conj(psi[other_state])
```

**Performance**: O(n × 2^n) complexity, fastest for pure states, scales up to ~24 qubits

##### 📊 Exact Density Matrix Pipeline (Mixed States)
**Use Case**: Circuits with measurements/resets ≤16 qubits, when exact mixed states are needed
**Algorithm**: Full density matrix simulation with partial trace operations

**Implementation**:
```python
# 1. Simulate using Qiskit's DensityMatrix backend
from qiskit.quantum_info import DensityMatrix
density_matrix = DensityMatrix.from_instruction(circuit)

# 2. Compute reduced density matrix for each qubit using partial trace
for i in range(n_qubits):
    # Trace out all qubits except qubit i
    other_qubits = [j for j in range(n_qubits) if j != i]
    rho_i = density_matrix.partial_trace(other_qubits)
    
    # Extract 2x2 density matrix
    rho_reduced = rho_i.data  # Already in proper 2x2 form
```

**Performance**: O(4^n) memory complexity, exact results for mixed states, limited to ~16 qubits

##### 🎲 Trajectory Pipeline (Monte Carlo Sampling)
**Use Case**: Large non-unitary circuits >16 qubits, statistical approximation acceptable
**Algorithm**: Monte Carlo sampling with stochastic quantum trajectories

**Implementation**:
```python
# 1. Run S independent quantum trajectories
S = max(1000, shots)  # Ensure sufficient statistics
trajectory_results = []

for trajectory in range(S):
    # Simulate single shot with random measurement outcomes
    circuit_copy = circuit.copy()
    backend = AerSimulator(method='statevector', shots=1)
    
    # Execute with stochastic collapse on measurements
    result = execute(circuit_copy, backend, shots=1).result()
    
    # Extract final statevector before any measurements
    if hasattr(result, 'get_statevector'):
        final_state = result.get_statevector()
        trajectory_results.append(final_state)

# 2. Compute ensemble average density matrices
ensemble_rho = {}
for i in range(n_qubits):
    rho_i = np.zeros((2, 2), dtype=complex)
    
    # Average over all trajectories
    for state_vec in trajectory_results:
        # Compute single-trajectory reduced density matrix
        rho_single = compute_single_qubit_rdm(state_vec, i)
        rho_i += rho_single / S
    
    ensemble_rho[i] = rho_i
```

**Performance**: O(S × simulation_time) complexity, scalable to 20+ qubits, accuracy improves with more trajectories

#### 🧠 Pipeline Selection Logic
The router intelligently selects pipelines based on circuit analysis:

```python
def route_circuit(circuit, shots=1000):
    # Analyze circuit properties
    has_measurements = any(op.name == 'measure' for op, _, _ in circuit.data)
    has_resets = any(op.name == 'reset' for op, _, _ in circuit.data)
    qubit_count = circuit.num_qubits
    gate_count = len(circuit.data)
    
    is_unitary = not (has_measurements or has_resets)
    
    # Selection criteria based on performance characteristics
    if is_unitary and qubit_count <= 20:
        return 'unitary'  # Fastest for pure states
    elif not is_unitary and qubit_count <= 16 and shots < 1000:
        return 'exact_density'  # Exact mixed states for smaller systems
    else:
        return 'trajectory'  # Statistical sampling for large systems
```

### 🎨 Interactive 3D Visualization
- **Bloch Sphere Grid**: Responsive grid layout displaying one interactive 3D Bloch sphere per qubit
- **State Vector Rendering**: Accurate representation of quantum states with vector length indicating purity
- **Mixed State Visualization**: Translucent spheres showing degree of mixedness
- **Camera Controls**: Synchronized orbit controls across all spheres
- **Real-time Updates**: Live state updates as circuits are modified

### 📊 Detailed State Inspector
- **Density Matrix Display**: Complete 2×2 reduced density matrix for each qubit
- **Bloch Coordinates**: Precise (rx, ry, rz) coordinates on the Bloch sphere
- **Purity Calculation**: Quantitative measure of state purity (Tr(ρ²))
- **Gate Count**: Live tracking of quantum operations in the circuit
- **Validation Status**: Real-time circuit validity indicators

### 🎮 Simulation Controls
- **Run Simulation**: Execute complete quantum circuits with validation
- **Pause/Resume**: Control simulation execution
- **Stop/Reset**: Clear current simulation state
- **Status Indicators**: Visual feedback on simulation progress and pipeline usage

### 💬 Built-in Chat Assistant (Optional)
- Floating chat button (bottom-right) opens a compact assistant window
- Answers questions about OpenQASM, routing, and app usage
- Backend powered by Gemini 2.5 Flash when configured
- Configure `GOOGLE_API_KEY` on backend; set `VITE_API_URL` on frontend

## 🛠️ Technology Stack

### Frontend
- **Framework**: React 18.3.1 with TypeScript
- **Build Tool**: Vite for fast development and building
- **3D Rendering**: React Three Fiber (R3F) + drei for interactive Bloch spheres
- **State Management**: Zustand for global application state
- **Code Editor**: Monaco Editor with custom OpenQASM language support
- **Styling**: Tailwind CSS with custom quantum-themed components
- **UI Components**: Radix UI for accessible, composable components
- **File Handling**: Custom drag-and-drop file upload with validation
- **Animations**: Custom CSS keyframes and transition system

### Backend
- **Framework**: FastAPI with Python for high-performance async API
- **Quantum Computing**: Qiskit for circuit parsing, validation, and simulation
- **Scientific Computing**: NumPy for vectorized mathematical operations
- **Performance**: Optional Numba JIT compilation for critical calculations
- **Validation**: Comprehensive gate whitelisting and circuit analysis
- **API Design**: RESTful endpoints with detailed error handling

### Development & DevOps
- **Containerization**: Docker with multi-stage builds
- **Package Management**: 
  - Frontend: npm/bun with lockfile management
  - Backend: pip with requirements.txt
- **Testing**: Comprehensive test suites for both frontend and backend
- **Code Quality**: ESLint, TypeScript strict mode, Python type hints

## 📁 Project Structure

```
Quantum_State_Visualizer/
├── frontend/                 # React TypeScript application
│   ├── src/
│   │   ├── components/      # UI components
│   │   │   ├── BlochSphere.tsx
│   │   │   ├── CanvasGrid.tsx
│   │   │   ├── EditorPanel.tsx
│   │   │   ├── Inspector.tsx
│   │   │   └── editor/      # Editor-specific components
│   │   │       ├── MonacoQasmEditor.tsx
│   │   │       ├── CodePreview.tsx
│   │   │       ├── QasmFileUploader.tsx
│   │   │       └── VisualEditor.tsx
│   │   ├── store/           # State management
│   │   │   └── quantumStore.ts
│   │   ├── lib/             # Utilities and API client
│   │   │   ├── api.ts
│   │   │   ├── utils.ts
│   │   │   └── qasmValidator.ts
│   │   └── pages/           # Page components
│   ├── package.json
│   └── vite.config.ts
├── backend/                 # FastAPI Python application
│   ├── main.py             # API endpoints and routing
│   ├── utils.py            # Core quantum logic
│   ├── schemas.py          # Pydantic models
│   ├── pipelines/          # Simulation pipelines
│   │   ├── base.py
│   │   ├── unitary.py
│   │   ├── exact_density.py
│   │   └── trajectory.py
│   ├── requirements.txt
│   └── Dockerfile
└── tests/                  # Comprehensive test suite
    ├── backend/
    ├── frontend/
    └── circuits/
```

## 🧮 Quantum Computing Features

### Supported Gates
- **Single-Qubit Gates**: H, X, Y, Z, S, T, Rx, Ry, Rz
- **Multi-Qubit Gates**: CNOT, CZ, SWAP, Toffoli
- **Measurements**: Computational basis measurements
- **Advanced**: Parameterized rotations, custom gate definitions

### Simulation Capabilities
- **State Vector Simulation**: Up to ~24 qubits for unitary circuits
- **Density Matrix Simulation**: Exact mixed state handling for smaller systems
- **Trajectory Sampling**: Monte Carlo methods for larger non-unitary circuits
- **Partial Trace Operations**: Automatic reduced density matrix calculation
- **Purity Analysis**: Quantitative measure of quantum state mixedness

### Validation & Security
- **Gate Whitelisting**: Security through supported operation restrictions
- **Circuit Limits**: Configurable limits on qubits, operations, and execution time
- **Input Sanitization**: Comprehensive validation of user inputs
- **Error Handling**: Detailed error reporting and graceful degradation

## 🚀 Getting Started

### Prerequisites
- Node.js 18+ (for frontend)
- Python 3.8+ (for backend)
- Docker (optional, for containerized deployment)

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### Backend Setup
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --reload
```

### Docker Deployment
```bash
# Build containers
docker-compose up --build

# Run in production
docker-compose -f docker-compose.prod.yml up
```

## 🎯 Usage Examples

### Creating a Bell State
```qasm
OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
h q[0];
cx q[0],q[1];
```

### GHZ State (3-qubit entanglement)
```qasm
OPENQASM 2.0;
include "qelib1.inc";
qreg q[3];
h q[0];
cx q[0],q[1];
cx q[1],q[2];
```

### Mixed State with Measurement
```qasm
OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
creg c[2];
h q[0];
cx q[0],q[1];
measure q[0] -> c[0];
```

## 🔬 Advanced Features

### Monaco Editor Integration
- **Syntax Highlighting**: Custom OpenQASM 2.0 language definition
- **Error Reporting**: Real-time syntax and semantic error detection
- **Autocomplete**: Intelligent code completion for quantum gates
- **Themes**: Multiple editor themes (VS Dark, Light, High Contrast)
- **File Operations**: Load, save, and export quantum circuits

### State Analysis
- **Bloch Vector Calculation**: 
  - rx = 2 × Re(ρ₀₁)
  - ry = -2 × Im(ρ₀₁)  
  - rz = ρ₀₀ - ρ₁₁
- **Purity Measurement**: Tr(ρ²) for quantifying quantum coherence
- **Entanglement Detection**: Analysis of multi-qubit correlations

### Performance Optimizations
- **Vectorized Calculations**: NumPy-based linear algebra operations
- **Pipeline Selection**: Automatic routing to optimal simulation method
- **Caching**: Intelligent result caching for repeated simulations
- **Memory Management**: Efficient handling of large quantum state spaces

## 🧪 Testing

### Test Categories
- **Unit Tests**: Individual component and function testing
- **Integration Tests**: End-to-end API and UI testing  
- **Golden Tests**: Verification against known quantum states
- **Property Tests**: Validation of quantum mechanical properties
- **Performance Tests**: Benchmarking simulation pipelines

### Running Tests
```bash
# Frontend tests
cd frontend && npm test

# Backend tests  
cd backend && python -m pytest

# Full test suite
npm run test:all
```

## 📈 Performance Characteristics

### Simulation Limits
- **Unitary Pipeline**: Up to 20 qubits (pure states)
- **Exact Density**: Up to 16 qubits (mixed states)
- **Trajectory Pipeline**: 16+ qubits with statistical sampling
- **File Upload**: Maximum 1MB per file
- **Circuit Complexity**: Up to 1000 quantum operations

### Optimization Features
- **Smart Routing**: Automatic selection of fastest simulation method
- **Vectorized Math**: NumPy optimizations for linear algebra
- **Memory Efficiency**: Reduced density matrix calculations
- **JIT Compilation**: Optional Numba acceleration for critical loops

## 🎨 UI/UX Features

### Interactive Elements
- **Responsive Design**: Adaptive layout for all screen sizes
- **Smooth Animations**: 700ms transitions between interface modes
- **Real-time Feedback**: Live validation and error reporting
- **Intuitive Controls**: Drag-and-drop, click-to-edit interfaces
- **Accessibility**: ARIA labels, keyboard navigation support

### Visualization Enhancements
- **3D Bloch Spheres**: Interactive quantum state visualization
- **State Vector Display**: Accurate representation with purity indication
- **Color Coding**: Visual distinction between pure and mixed states
- **Grid Layout**: Responsive arrangement of multiple qubits
- **Camera Synchronization**: Coordinated viewing across spheres

## 🔮 Future Roadmap

### Planned Enhancements
- **Step-by-Step Execution**: Gate-by-gate animation of quantum evolution
- **WebSocket Streaming**: Real-time simulation progress updates
- **Conditioned States**: Visualization of post-measurement quantum states
- **Circuit Optimization**: Automatic gate sequence optimization
- **Export Capabilities**: SVG, PNG, and data export functionality
- **Collaborative Features**: Share and collaborate on quantum circuits

### Performance Improvements
- **GPU Acceleration**: CUDA/OpenCL support for large simulations
- **Distributed Computing**: Multi-node simulation clustering
- **Advanced Algorithms**: Tensor network and matrix product state methods
- **Caching Strategies**: Intelligent memoization of simulation results

## 🤝 Contributing

### Development Workflow
1. Fork the repository
2. Create a feature branch
3. Implement changes with tests
4. Submit pull request with detailed description
5. Code review and integration

### Code Standards
- **TypeScript**: Strict type checking enabled
- **Python**: Type hints and docstring documentation
- **Testing**: Minimum 80% code coverage requirement
- **Documentation**: Inline comments and API documentation

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **Qiskit Team**: For the excellent quantum computing framework
- **React Three Fiber**: For enabling beautiful 3D quantum visualizations  
- **FastAPI**: For the high-performance async backend framework
- **Monaco Editor**: For providing professional code editing capabilities
- **Quantum Computing Community**: For inspiration and theoretical foundations

---

**Built with ❤️ for the quantum computing community**

*Visualizing the quantum world, one qubit at a time.*
