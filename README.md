# QubitLens

A comprehensive web-based application for quantum circuit simulation and Bloch sphere visualization. This interactive tool provides real-time 3D visualization of quantum states, making quantum computing concepts accessible through intuitive visual representations.

## 🚀 Features

- **Interactive 3D Bloch Spheres**: Real-time visualization of quantum states with React Three Fiber
- **Quantum Circuit Simulation**: Support for OpenQASM 2.0 with multiple simulation pipelines
- **15+ Preset Circuits**: From basic superposition to advanced quantum algorithms
- **Smart Pipeline Routing**: Automatic selection of optimal simulation method
- **Educational Interface**: Clear explanations and quantum state details
- **Real-time Updates**: Live visualization of quantum state changes

## 🏗️ Architecture

- **Backend**: FastAPI + Python with Qiskit quantum simulation
- **Frontend**: React + TypeScript + Vite with Three.js 3D visualization
- **State Management**: Zustand for reactive updates
- **UI Components**: Tailwind CSS + Radix UI for modern design

## 📋 Prerequisites

### System Requirements
- **Python**: 3.11 or higher
- **Node.js**: 18 or higher
- **npm**: 8 or higher (or bun/yarn)

### Platform Support
- Linux (recommended)
- macOS
- Windows (with WSL recommended)

## 🛠️ Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/shasank0001/Quantum-State-Visualizer.git
cd Quantum_State_Visualizer
```

### 2. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/macOS:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Start the backend server
python start.py
```

The backend will be available at: **http://localhost:8000**

**API Documentation**: http://localhost:8000/docs

### 3. Frontend Setup

```bash
# Navigate to frontend directory (in a new terminal)
cd frontend

# Install Node.js dependencies
npm install
# or with bun: bun install

# Start the development server
npm run dev
# or with bun: bun run dev
```

The frontend will be available at: **http://localhost:5173**

### 4. Access the Application

Open your browser and navigate to:
- **Main App**: http://localhost:5173
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## 🎯 Quick Start Guide

### Running Your First Simulation

1. **Open the Web App** at http://localhost:5173
2. **Select a Preset Circuit** from the dropdown (try "Bell State")
3. **Click "Run Simulation"** to execute the quantum circuit
4. **Explore the 3D Bloch Spheres** showing individual qubit states
5. **View Quantum Details** in the Inspector panel

### Preset Circuits Available

#### **Basic Quantum States**
- **Superposition**: Single qubit in |+⟩ state
- **Plus-Minus States**: Demonstrates |+⟩ and |-⟩ states
- **Bloch Sphere Rotations**: Different rotation axes (RX, RY, RZ)

#### **Entanglement Examples**
- **Bell State**: Two-qubit entanglement |00⟩ + |11⟩
- **GHZ State**: Three-qubit GHZ entanglement
- **W State**: Symmetric three-qubit entanglement
- **Cat State**: Four-qubit Schrödinger cat state

#### **Quantum Algorithms**
- **Deutsch Algorithm**: Quantum speedup demonstration
- **Bernstein-Vazirani**: Secret string identification
- **Grover Search**: Database search amplification
- **Quantum Fourier Transform**: Frequency domain operations

#### **Advanced Phenomena**
- **Quantum Teleportation**: Protocol demonstration
- **Phase Kickback**: Phase manipulation effects
- **Quantum Interference**: Wave-like quantum behavior

### Understanding the Visualization

- **Bloch Sphere**: Each qubit is represented as a 3D sphere
- **State Vector**: Orange/cyan arrow showing quantum state direction
- **Zero Vector**: Center sphere for maximally mixed states (entangled qubits)
- **Purity Ring**: Indicates mixed vs. pure states
- **Coordinates**: X, Y, Z Bloch coordinates displayed below each sphere

## 🔧 Development

### Project Structure

```
Quantum_State_Visualizer/
├── backend/                 # FastAPI backend
│   ├── main.py             # Main application
│   ├── pipelines/          # Simulation engines
│   ├── utils.py            # Circuit parsing & validation
│   └── requirements.txt    # Python dependencies
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── store/          # Zustand state management
│   │   └── lib/            # API integration
│   └── package.json        # Node.js dependencies
└── tests/                  # Test suites
```

### Running Tests

```bash
# Backend tests
cd tests
python run_tests.py --backend-only --backend-url http://localhost:8000

# Full test suite (requires both servers running)
python run_tests.py
```

### API Usage

You can also use the backend API directly:

```bash
# Test a Bell state circuit
curl -X POST "http://localhost:8000/simulate" \
  -H "Content-Type: application/json" \
  -d '{
    "qasm_code": "OPENQASM 2.0;\ninclude \"qelib1.inc\";\nqreg q[2];\nh q[0];\ncx q[0], q[1];",
    "shots": 1024
  }'
```

## 🐳 Docker Deployment (Optional)

### Backend Container

```bash
cd backend
docker build -t quantum-visualizer-backend .
docker run -p 8000:8000 quantum-visualizer-backend
```

### Frontend Build

```bash
cd frontend
npm run build
# Serve the dist/ folder with your preferred web server
```

## 📚 Learning Resources

### Understanding Quantum States
- **Pure States**: Single quantum state with purity = 1.0
- **Mixed States**: Statistical mixture with purity < 1.0
- **Entangled States**: Individual qubits appear mixed (center of Bloch sphere)
- **Superposition**: Quantum states existing in multiple states simultaneously

### Bloch Sphere Coordinates
- **X-axis**: Real part of off-diagonal density matrix elements
- **Y-axis**: Imaginary part of off-diagonal elements  
- **Z-axis**: Population difference between |0⟩ and |1⟩ states
- **Center [0,0,0]**: Maximally mixed state (individual entangled qubits)

## 🛠️ Troubleshooting

### Common Issues

#### Backend Not Starting
```bash
# Check Python version
python --version  # Should be 3.11+

# Reinstall dependencies
pip install -r backend/requirements.txt

# Check port availability
lsof -i :8000
```

#### Frontend Build Issues
```bash
# Clear node modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Check Node version
node --version  # Should be 18+
```

#### API Connection Errors
- Ensure backend is running on port 8000
- Check firewall settings
- Verify CORS configuration (handled automatically)

#### Visualization Not Loading
- Ensure WebGL is supported in your browser
- Try disabling browser extensions
- Check browser console for JavaScript errors

### Performance Notes

- **Small Circuits** (≤3 qubits): Excellent performance
- **Medium Circuits** (4-8 qubits): Good performance with smooth visualization
- **Large Circuits** (9+ qubits): Functional but may need performance optimizations
- **Maximum Limits**: 24 qubits, 1000 operations per circuit

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests to ensure functionality
5. Submit a pull request

### Development Guidelines
- Follow existing code style and patterns
- Add tests for new features
- Update documentation as needed
- Ensure quantum physics correctness

## 📄 License

This project is part of a quantum computing hackathon submission. Please refer to individual component licenses for specific usage terms.

## 🎓 Educational Use

This visualizer is designed for:
- **Students**: Learning quantum computing concepts
- **Educators**: Teaching quantum mechanics and quantum computing
- **Researchers**: Exploring quantum circuit behavior
- **Developers**: Understanding quantum programming

The interactive 3D visualization makes abstract quantum concepts tangible and helps build intuition about quantum state behavior.

---

**Happy Quantum Computing! 🌟**
