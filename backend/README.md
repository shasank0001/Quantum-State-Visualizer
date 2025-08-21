# Quantum State Visualizer Backend

FastAPI-based backend for quantum circuit simulation and Bloch sphere visualization. This implementation follows the architecture specified in `dev_plane.md` with modular simulation pipelines.

## Architecture Overview

The backend implements a client-server architecture with:

- **FastAPI Application**: RESTful API and WebSocket endpoints
- **Modular Simulation Pipelines**: Pluggable simulation backends
- **Circuit Routing**: Automatic selection of optimal simulation method
- **Security**: Input validation, resource limits, and timeouts

## Features

### Core Functionality

- ✅ OpenQASM 2.0 circuit parsing and validation
- ✅ Automatic routing to optimal simulation pipeline
- ✅ Bloch sphere coordinate calculation
- ✅ Reduced density matrix computation
- ✅ WebSocket support for real-time streaming
- ✅ Comprehensive error handling and logging

### Simulation Pipelines

- **UnitaryPipeline**: Statevector simulation for pure states (≤20 qubits)
- **ExactDensityPipeline**: Full density matrix evolution (≤16 qubits)
- **TrajectoryPipeline**: Monte Carlo sampling for measurements (≤16 qubits)

### Security & Limits

- Circuit validation with gate whitelisting
- Resource limits: 24 qubits max, 1000 operations max
- Simulation timeouts (5 minutes)
- Input sanitization and validation

## Installation

### Prerequisites

- Python 3.11+
- Poetry or pip for dependency management

### Local Development Setup

1. **Install dependencies:**

```bash
pip install -r requirements.txt
```

2. **Run the server:**

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

3. **Access the API:**

- API Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

### Docker Setup

1. **Build the image:**

```bash
docker build -t quantum-visualizer-backend .
```

2. **Run the container:**

```bash
docker run -p 8000:8000 quantum-visualizer-backend
```

## API Reference

### REST Endpoints

#### `POST /simulate`

Simulate a quantum circuit and return Bloch sphere visualization data.

**Request Body:**

```json
{
  "qasm_code": "OPENQASM 2.0;\\ninclude \"qelib1.inc\";\\nqreg q[2];\\nh q[0];\\ncx q[0], q[1];",
  "shots": 1024,
  "pipeline_override": null,
  "options": {}
}
```

**Response:**

```json
{
  "qubits": [
    {
      "id": 0,
      "bloch_coords": [0.0, 0.0, 0.0],
      "purity": 0.5,
      "density_matrix": [[0.5, 0.0], [0.0, 0.5]],
      "label": "Q0"
    }
  ],
  "pipeline_used": "exact_density",
  "execution_time": 0.123,
  "shots_used": 1024,
  "circuit_info": {
    "num_qubits": 2,
    "num_operations": 2,
    "is_unitary": true
  }
}
```

#### `GET /health`

Health check endpoint returning system status.

### WebSocket Endpoints

#### `WS /ws/simulate`

Real-time simulation streaming with progress updates.

**Client Messages:**

```json
{
  "type": "start_simulation",
  "data": {
    "qasm_code": "...",
    "shots": 1024
  }
}
```

**Server Messages:**

```json
{
  "type": "progress",
  "progress": 50,
  "message": "Simulation 50% complete"
}
```

## Simulation Pipelines

### Routing Logic

Circuits are automatically routed based on characteristics:

1. **Unitary circuits** (≤20 qubits) → `UnitaryPipeline`
2. **Non-unitary circuits** (≤16 qubits, ≥1000 shots) → `TrajectoryPipeline`
3. **All other circuits** → `ExactDensityPipeline`

### Pipeline Details

#### UnitaryPipeline

- **Method**: Statevector simulation
- **Best for**: Pure quantum states, unitary evolution
- **Limits**: 20 qubits maximum
- **Memory**: O(2^n) scaling
- **Accuracy**: Exact (numerical precision)

#### ExactDensityPipeline

- **Method**: Full density matrix evolution
- **Best for**: Mixed states, fallback cases
- **Limits**: 16 qubits maximum
- **Memory**: O(4^n) scaling
- **Accuracy**: Exact (numerical precision)

#### TrajectoryPipeline

- **Method**: Quantum Monte Carlo sampling
- **Best for**: Circuits with measurements, large systems
- **Limits**: 16 qubits maximum
- **Memory**: O(2^n) per trajectory
- **Accuracy**: Statistical (improves with shots)

## Configuration

### Environment Variables

- `PYTHONPATH`: Set to `/app` for proper imports
- `LOG_LEVEL`: Logging level (default: INFO)
- `MAX_WORKERS`: Number of worker processes (default: 1)

### Security Settings

```python
# Resource limits (configurable in utils.py)
MAX_QUBITS = 24
MAX_OPERATIONS = 1000  
MAX_SHOTS = 100000
SIMULATION_TIMEOUT = 300  # seconds
```

## Development

### Project Structure

```
backend/
├── main.py              # FastAPI application
├── schemas.py           # Pydantic models  
├── utils.py             # Circuit parsing & validation
├── pipelines/           # Simulation backends
│   ├── __init__.py
│   ├── base.py         # Abstract base class
│   ├── unitary.py      # Statevector simulation
│   ├── exact_density.py # Density matrix simulation  
│   └── trajectory.py   # Monte Carlo simulation
├── requirements.txt     # Dependencies
├── Dockerfile          # Container configuration
└── README.md           # This file
```

### Adding New Pipelines

1. **Subclass `SimulationPipeline`:**

```python
from pipelines.base import SimulationPipeline

class CustomPipeline(SimulationPipeline):
    def run(self, circuit, shots=1024):
        # Implementation here
        return results
```

2. **Register in `pipelines/__init__.py`:**

```python
AVAILABLE_PIPELINES['custom'] = CustomPipeline
```

3. **Update routing logic in `utils.py`** if needed.

### Testing

```bash
# Unit tests
python -m pytest tests/

# Integration tests  
python -m pytest tests/integration/

# Load testing
python -m pytest tests/performance/
```

### Logging

The backend uses structured logging:

```python
import logging
logger = logging.getLogger(__name__)

logger.info("Circuit parsed successfully", extra={
    "num_qubits": circuit.num_qubits,
    "num_operations": len(circuit.data)
})
```

## Deployment

### Production Considerations

1. **Resource Management**: Monitor memory usage for large circuits
2. **Scaling**: Use multiple workers for concurrent requests
3. **Monitoring**: Set up health checks and metrics collection
4. **Security**: Run with non-root user, validate all inputs

### Docker Compose Example

```yaml
version: '3.8'
services:
  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - LOG_LEVEL=INFO
    healthcheck:
      test: ["CMD", "python", "-c", "import requests; requests.get('http://localhost:8000/health')"]
      interval: 30s
      timeout: 10s
      retries: 3
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all dependencies are installed
2. **Memory Issues**: Reduce qubit count or use trajectory simulation
3. **Timeout Errors**: Increase `SIMULATION_TIMEOUT` for complex circuits
4. **WebSocket Disconnections**: Check network stability and implement reconnection logic

### Performance Optimization

- Use `numba` for numerical computations
- Enable circuit optimization in preprocessing
- Consider caching for repeated simulations
- Monitor memory usage and implement cleanup

## Contributing

1. Follow the modular architecture from `dev_plane.md`
2. Add comprehensive tests for new features
3. Update documentation and type hints
4. Ensure security validation for user inputs

## License

This project is part of the Quantum State Visualizer hackathon submission.
