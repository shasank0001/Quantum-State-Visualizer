"""
Test circuit definitions for Quantum State Visualizer
Contains various types of quantum circuits for comprehensive testing
"""

# Test circuit definitions with expected results
TEST_CIRCUITS = {
    "bell_state": {
        "name": "Bell State (Entangled Pair)",
        "qasm": """OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
h q[0];
cx q[0], q[1];""",
        "expected_pipeline": "unitary",
        "expected_qubits": 2,
        "expected_entanglement": True,
        "expected_pure_global": True,
        "expected_mixed_individual": True,  # Individual qubits should be mixed due to entanglement
        "expected_purity_range": (0.4, 0.6),  # Should be around 0.5 for maximally mixed
        "description": "Two-qubit entangled Bell state |00⟩ + |11⟩"
    },
    
    "ghz_state": {
        "name": "GHZ State (3-qubit Entanglement)",
        "qasm": """OPENQASM 2.0;
include "qelib1.inc";
qreg q[3];
h q[0];
cx q[0], q[1];
cx q[1], q[2];""",
        "expected_pipeline": "unitary",
        "expected_qubits": 3,
        "expected_entanglement": True,
        "expected_pure_global": True,
        "expected_mixed_individual": True,
        "expected_purity_range": (0.4, 0.6),
        "description": "Three-qubit GHZ entangled state"
    },
    
    "single_qubit_superposition": {
        "name": "Single Qubit Superposition",
        "qasm": """OPENQASM 2.0;
include "qelib1.inc";
qreg q[1];
h q[0];""",
        "expected_pipeline": "unitary",
        "expected_qubits": 1,
        "expected_entanglement": False,
        "expected_pure_global": True,
        "expected_mixed_individual": False,  # Single qubit in pure superposition
        "expected_purity_range": (0.95, 1.0),
        "expected_bloch_coords": {"x": 1.0, "y": 0.0, "z": 0.0},  # |+⟩ state
        "description": "Single qubit in |+⟩ superposition state"
    },
    
    "identity_circuit": {
        "name": "Identity (Ground State)",
        "qasm": """OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];""",
        "expected_pipeline": "unitary",
        "expected_qubits": 2,
        "expected_entanglement": False,
        "expected_pure_global": True,
        "expected_mixed_individual": False,
        "expected_purity_range": (0.95, 1.0),
        "expected_bloch_coords": {"x": 0.0, "y": 0.0, "z": 1.0},  # |0⟩ state
        "description": "Two qubits in ground state |00⟩"
    },
    
    "measurement_circuit": {
        "name": "Circuit with Measurements",
        "qasm": """OPENQASM 2.0;
include "qelib1.inc";
qreg q[3];
creg c[3];
h q[0];
cx q[0], q[1];
h q[2];
measure q[2] -> c[2];
reset q[2];
h q[2];""",
    "expected_pipeline": "exact_density",
        "expected_qubits": 3,
        "expected_entanglement": True,
        "expected_pure_global": False,  # Measurements create mixed states
        "expected_mixed_individual": True,
        "expected_purity_range": (0.3, 0.8),
        "description": "Circuit with measurements and reset operations"
    },
    
    "rotation_circuit": {
        "name": "Arbitrary Rotation",
        "qasm": """OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
ry(1.57) q[0];
rx(0.78) q[1];""",
        "expected_pipeline": "unitary",
        "expected_qubits": 2,
        "expected_entanglement": False,
        "expected_pure_global": True,
        "expected_mixed_individual": False,
        "expected_purity_range": (0.95, 1.0),
        "description": "Two qubits with arbitrary rotations"
    },
    
    "large_circuit": {
        "name": "Large Circuit (5 qubits)",
        "qasm": """OPENQASM 2.0;
include "qelib1.inc";
qreg q[5];
h q[0];
cx q[0], q[1];
cx q[1], q[2];
h q[3];
cx q[3], q[4];
cx q[2], q[3];""",
        "expected_pipeline": "unitary",
        "expected_qubits": 5,
        "expected_entanglement": True,
        "expected_pure_global": True,
        "expected_mixed_individual": True,
        "expected_purity_range": (0.3, 0.7),
        "description": "Large circuit with multiple entangled qubits"
    },
    
    "complex_measurement_circuit": {
        "name": "Complex Circuit with Multiple Measurements",
        "qasm": """OPENQASM 2.0;
include "qelib1.inc";
qreg q[4];
creg c[4];
h q[0];
cx q[0], q[1];
cx q[1], q[2];
h q[3];
measure q[3] -> c[3];
ry(0.5) q[2];
cz q[0], q[3];""",
    "expected_pipeline": "exact_density",
        "expected_qubits": 4,
        "expected_entanglement": True,
        "expected_pure_global": False,
        "expected_mixed_individual": True,
        "expected_purity_range": (0.2, 0.8),
        "description": "Complex circuit with entanglement and measurements"
    },
    
    "w_state": {
        "name": "W State (Symmetric Entanglement)",
        "qasm": """OPENQASM 2.0;
include "qelib1.inc";
qreg q[3];
ry(1.23095942) q[0];
ch q[0], q[1];
x q[0];
cry(0.95531662) q[1], q[2];
x q[0];""",
        "expected_pipeline": "unitary",
        "expected_qubits": 3,
        "expected_entanglement": True,
        "expected_pure_global": True,
        "expected_mixed_individual": True,
        "expected_purity_range": (0.5, 0.8),
        "description": "Three-qubit W state with symmetric entanglement"
    },
    
    "phase_circuit": {
        "name": "Phase Gate Circuit",
        "qasm": """OPENQASM 2.0;
include "qelib1.inc";
qreg q[3];
h q[0];
h q[1];
h q[2];
s q[0];
t q[1];
z q[2];
cx q[0], q[1];
cx q[1], q[2];""",
        "expected_pipeline": "unitary",
        "expected_qubits": 3,
        "expected_entanglement": True,
        "expected_pure_global": True,
        "expected_mixed_individual": True,
        "expected_purity_range": (0.4, 0.7),
        "description": "Circuit with phase gates and entanglement"
    }
}

# Invalid circuits for error testing
INVALID_CIRCUITS = {
    "empty_circuit": {
        "name": "Empty Circuit",
        "qasm": "",
        "expected_error": "Empty QASM code"
    },
    
    "no_qasm_header": {
        "name": "Missing QASM Header",
        "qasm": """include "qelib1.inc";
qreg q[1];
h q[0];""",
        "expected_error": "Missing OPENQASM version declaration"
    },
    
    "unsupported_gate": {
        "name": "Unsupported Gate",
        "qasm": """OPENQASM 2.0;
include "qelib1.inc";
qreg q[1];
unsupported_gate q[0];""",
        "expected_error": "Unsupported gate"
    },
    
    "too_many_qubits": {
        "name": "Too Many Qubits",
        "qasm": """OPENQASM 2.0;
include "qelib1.inc";
qreg q[30];""",
        "expected_error": "Too many qubits"
    },
    
    "syntax_error": {
        "name": "Syntax Error",
        "qasm": """OPENQASM 2.0;
include "qelib1.inc";
qreg q[1];
h q[0]""",  # Missing semicolon
        "expected_error": "QASM parsing error"
    }
}

# Performance test circuits
PERFORMANCE_CIRCUITS = {
    "small_performance": {
        "name": "Small Performance Test",
        "qubits": 8,
        "operations": 50,
        "expected_time_limit": 1.0  # seconds
    },
    
    "medium_performance": {
        "name": "Medium Performance Test", 
        "qubits": 12,
        "operations": 100,
        "expected_time_limit": 5.0  # seconds
    },
    
    "large_performance": {
        "name": "Large Performance Test",
        "qubits": 16,
        "operations": 200,
        "expected_time_limit": 30.0  # seconds
    }
}

def generate_performance_circuit(qubits: int, operations: int) -> str:
    """Generate a random circuit for performance testing"""
    import random
    
    qasm = f"""OPENQASM 2.0;
include "qelib1.inc";
qreg q[{qubits}];
"""
    
    gates = ['h', 'x', 'y', 'z', 's', 't']
    two_qubit_gates = ['cx', 'cz']
    
    for _ in range(operations):
        if random.random() < 0.7:  # 70% single-qubit gates
            gate = random.choice(gates)
            qubit = random.randint(0, qubits - 1)
            qasm += f"{gate} q[{qubit}];\n"
        else:  # 30% two-qubit gates
            gate = random.choice(two_qubit_gates)
            q1, q2 = random.sample(range(qubits), 2)
            qasm += f"{gate} q[{q1}], q[{q2}];\n"
    
    return qasm
