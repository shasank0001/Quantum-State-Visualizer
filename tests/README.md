# Quantum State Visualizer Test Suite

This directory contains comprehensive test scripts for validating both the backend API and frontend UI components of the Quantum State Visualizer. **All test runs are automatically logged to files** in the `logs/` directory for detailed analysis and debugging.

## Directory Structure

```
tests/
├── run_tests.py              # Main test runner script with integrated logging
├── test_requirements.txt     # Test dependencies
├── test_logging.py          # Logging system test utility
├── README.md                 # This file
├── logs/                     # Auto-generated log files (created on first run)
│   └── test_run_YYYYMMDD_HHMMSS.log  # Timestamped log files
├── backend/
│   └── test_api.py           # Backend API tests
├── frontend/
│   └── test_ui.py            # Frontend UI tests (requires Selenium)
└── circuits/
    └── test_circuits.py      # Test circuit definitions
```

## Logging System

### **Automatic Logging**
Every test run automatically creates a detailed log file in `tests/logs/` with:
- **Timestamped filename**: `test_run_YYYYMMDD_HHMMSS.log`
- **Detailed execution logs**: All test steps, API calls, and results
- **Error diagnostics**: Full exception traces and debugging information
- **Performance metrics**: Timing and resource usage data

### **Log Levels**
- **DEBUG**: Detailed technical information (logged to file only by default)
- **INFO**: General test progress and results (console + file)
- **WARNING**: Non-fatal issues that should be reviewed (console + file)  
- **ERROR**: Test failures and critical issues (console + file)

### **Console vs File Logging**
- **Console**: Shows important messages (INFO, WARNING, ERROR) for quick feedback
- **File**: Contains complete details including DEBUG messages for thorough analysis
- **Verbose Mode**: Use `--verbose` flag to show DEBUG messages on console too

## Test Categories

### 1. Backend API Tests (`backend/test_api.py`)
Tests the FastAPI backend endpoints with various quantum circuits:

- **Health Check**: Validates `/health` endpoint
- **Valid Circuit Tests**: Tests simulation with various quantum circuits:
  - Bell states (entangled pairs)
  - GHZ states (multi-qubit entanglement)
  - Single qubit superpositions
  - Circuits with measurements
  - Large circuits (performance testing)
- **Invalid Circuit Tests**: Error handling validation
- **Performance Tests**: Large circuit simulation timing
- **WebSocket Tests**: WebSocket endpoint availability
- **CORS Tests**: Cross-origin resource sharing headers

### 2. Frontend UI Tests (`frontend/test_ui.py`)
Tests the React frontend using Selenium WebDriver:

- **Component Presence**: Validates all UI components load
- **Editor Integration**: Tests QASM code editor functionality
- **Simulation Workflow**: End-to-end simulation testing
- **3D Visualization**: Canvas and Bloch sphere rendering
- **Responsive Design**: Multi-device layout testing
- **API Integration**: Frontend-to-backend communication
- **Console Error Detection**: JavaScript error monitoring

### 3. Test Circuits (`circuits/test_circuits.py`)
Defines comprehensive test cases:

- **Valid Circuits**: 10+ quantum circuits with expected outcomes
- **Invalid Circuits**: Error condition testing
- **Performance Circuits**: Scalability testing

## Prerequisites

### System Dependencies
```bash
# Ubuntu/Debian
sudo apt-get install chromium-chromedriver python3-pip

# macOS
brew install chromedriver python3

# Verify installation
chromedriver --version
python3 --version
```

### Python Dependencies
```bash
# Install test requirements
pip install -r test_requirements.txt

# Core dependencies:
# - requests: HTTP client for API testing
# - selenium: Web browser automation
# - pytest: Optional advanced testing framework
```

### Service Requirements
- **Backend**: Must be running at `http://localhost:8001` (or specified URL)
- **Frontend**: Must be running at `http://localhost:5173` (or specified URL)

## Usage

### Quick Start - Run All Tests
```bash
# Run all tests with automatic logging
python3 run_tests.py

# Auto-start services and run all tests
python3 run_tests.py --auto-start

# Run with verbose console output (shows DEBUG messages)
python3 run_tests.py --verbose

# Run with visible browser (non-headless)
python3 run_tests.py --no-headless
```

### Selective Testing
```bash
# Backend tests only
python3 run_tests.py --backend-only

# Frontend tests only  
python3 run_tests.py --frontend-only

# Test specific circuit
python3 run_tests.py --backend-only --circuit bell_state

# Custom service URLs
python3 run_tests.py --backend-url http://localhost:8002 --frontend-url http://localhost:3000
```

### Log Management
```bash
# View latest log file
ls -lt tests/logs/ | head -1

# Tail live test execution
tail -f tests/logs/test_run_$(date +%Y%m%d_*)*.log

# Search logs for errors
grep -i error tests/logs/test_run_*.log

# Analyze specific test results
grep "bell_state" tests/logs/test_run_*.log
```

### Individual Test Modules
```bash
# Run backend tests directly
cd backend && python3 test_api.py

# Run frontend tests directly
cd frontend && python3 test_ui.py

# Test specific circuit with backend
cd backend && python3 test_api.py --circuit ghz_state
```

### Generate Test Reports
```bash
# Save detailed JSON report + automatic log file
python3 run_tests.py --report test_results.json

# View report structure
python3 -m json.tool test_results.json

# Logs are always created automatically in tests/logs/
# No additional flags needed for logging
```

## Test Circuit Examples

The test suite includes various quantum circuits:

### Bell State (Entangled Pair)
```qasm
OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
h q[0];
cx q[0], q[1];
```
Expected: 2 qubits, unitary pipeline, entangled state

### GHZ State (3-qubit Entanglement)
```qasm
OPENQASM 2.0;
include "qelib1.inc";
qreg q[3];
h q[0];
cx q[0], q[1];
cx q[1], q[2];
```
Expected: 3 qubits, unitary pipeline, multi-party entanglement

### Circuit with Measurements
```qasm
OPENQASM 2.0;
include "qelib1.inc";
qreg q[3];
creg c[3];
h q[0];
cx q[0], q[1];
measure q[2] -> c[2];
```
Expected: 3 qubits, trajectory pipeline, mixed states

## Expected Test Results

### Backend API Tests
- **Health Check**: Should pass if backend is running
- **Valid Circuits**: Should simulate successfully with correct metadata  
- **Invalid Circuits**: Should return appropriate HTTP error codes
- **Performance**: Large circuits should complete within time limits
- **Logging**: All API requests/responses logged with timing details

### Frontend UI Tests  
- **Page Load**: React app should initialize without errors
- **Components**: Editor, controls, and canvas should be present
- **Simulation**: Should handle circuit input and display results
- **Responsive**: Should work on different screen sizes
- **Logging**: All UI interactions and browser console messages logged

### Log File Analysis
Each test run generates comprehensive logs containing:
- **Test Execution Timeline**: Start/end times for each test
- **API Request/Response Details**: Full HTTP interactions
- **Browser Console Messages**: JavaScript errors and warnings
- **Performance Metrics**: Response times and resource usage
- **Error Diagnostics**: Full stack traces for failures

## Troubleshooting

### Common Issues

#### ChromeDriver Not Found
```bash
# Ubuntu/Debian
sudo apt-get install chromium-chromedriver

# Verify PATH
which chromedriver
```

#### Backend Not Starting
```bash
# Check backend logs
cd backend && python3 start.py

# Verify dependencies
cd backend && pip install -r requirements.txt
```

#### Frontend Not Starting
```bash
# Install dependencies
cd frontend && npm install
# or
cd frontend && bun install

# Start development server
cd frontend && npm run dev
# or
cd frontend && bun run dev
```

#### Selenium WebDriver Issues
```bash
# Update Chrome/Chromium
sudo apt update && sudo apt upgrade chromium-browser

# Check Chrome version compatibility
google-chrome --version
chromedriver --version
```

### Test-Specific Issues

#### API Connection Errors
- Verify backend URL and port
- Check firewall/network restrictions
- Ensure CORS headers are configured

#### UI Element Not Found
- Frontend may still be loading
- Check console for JavaScript errors
- Verify React component structure

#### Performance Test Failures
- Large circuits may require more time/memory
- Adjust timeout values in test configuration
- Monitor system resources during tests

## Configuration

### Environment Variables
```bash
# Optional: Override default URLs
export BACKEND_URL="http://localhost:8001"
export FRONTEND_URL="http://localhost:5173"

# Optional: Test timeout settings
export TEST_TIMEOUT=30
export SELENIUM_TIMEOUT=10
```

### Test Customization
Edit `circuits/test_circuits.py` to:
- Add new test circuits
- Modify expected outcomes
- Adjust performance thresholds

## Integration with CI/CD

### GitHub Actions Example
```yaml
name: Test Quantum Visualizer
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: |
          sudo apt-get update
          sudo apt-get install chromium-chromedriver
          pip install -r tests/test_requirements.txt
          pip install -r backend/requirements.txt
      - run: python3 tests/run_tests.py --auto-start --report results.json
      - uses: actions/upload-artifact@v3
        with:
          name: test-results
          path: results.json
```

## Contributing

When adding new tests:

1. **Backend Tests**: Add new circuits to `circuits/test_circuits.py`
2. **Frontend Tests**: Extend `frontend/test_ui.py` with new UI scenarios
3. **Test Validation**: Ensure tests are deterministic and reliable
4. **Documentation**: Update this README with new test descriptions

### Test Writing Guidelines

- **Isolation**: Tests should not depend on external state
- **Clarity**: Test names should clearly describe what they validate
- **Coverage**: Include both positive and negative test cases
- **Performance**: Set reasonable timeout values
- **Maintainability**: Use shared test utilities and constants

## License

This test suite is part of the Quantum State Visualizer project and follows the same licensing terms.
