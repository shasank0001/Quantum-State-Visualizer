"""
Utility functions for quantum circuit parsing, validation, and routing.
Implements the core logic specified in dev_plane.md.
"""

import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit.library import *
from qiskit import qasm2
import re
from typing import Dict, List, Tuple, Any, Optional
import time
import logging

logger = logging.getLogger(__name__)

# Supported gate whitelist for security
SUPPORTED_GATES = {
    # Single-qubit unitary gates
    'h', 'x', 'y', 'z', 's', 't', 'sdg', 'tdg',
    'sx', 'sxdg', 'id',
    'rx', 'ry', 'rz', 'u', 'u1', 'u2', 'u3', 'p',
    # Two-qubit (and controlled) unitary gates
    'cx', 'cy', 'cz', 'ch', 'swap', 'ccx', 'cswap', 'csx', 'dcx',
    'crx', 'crz', 'cp', 'cu1', 'cu2', 'cu3',
    'rxx', 'ryy', 'rzz', 'rzx', 'ecr', 'iswap',
    # Misc / compile-time ops treated as unitary no-ops
    'barrier',
    # Non-unitary operations (measurements/resets)
    'measure', 'reset'
}

# Non-unitary operations that affect routing (barrier is unitary/no-op)
NON_UNITARY_OPS = {'measure', 'reset'}

def parse_and_validate_circuit(qasm_code: str) -> Tuple[QuantumCircuit, Dict[str, Any]]:
    """
    Parse QASM code and validate the quantum circuit.
    
    Args:
        qasm_code: OpenQASM 2.0 code string
        
    Returns:
        Tuple of (parsed_circuit, validation_info)
        
    Raises:
        ValueError: If circuit cannot be parsed or is invalid
    """
    validation_info = {
        "is_valid": False,
        "is_unitary": True,
        "num_qubits": 0,
        "num_operations": 0,
        "supported_gates": [],
        "unsupported_gates": [],
        "errors": [],
        "warnings": []
    }
    
    try:
        # Clean and validate QASM string
        qasm_code = qasm_code.strip()
        
        if not qasm_code:
            validation_info["errors"].append("Empty QASM code")
            return None, validation_info
        
        if "OPENQASM" not in qasm_code:
            validation_info["errors"].append("Missing OPENQASM version declaration")
            return None, validation_info
        
        # QASM shims: expand a few non-qelib instructions into qelib1-compatible sequences
        def _expand_qasm_aliases(qasm: str) -> str:
            # 1) CRY(theta) decomposition (control=c, target=t)
            cry_pat = re.compile(r"^\s*cry\(([^)]+)\)\s+q\[(\d+)\],\s*q\[(\d+)\];\s*$", re.IGNORECASE | re.MULTILINE)
            def cry_repl(m):
                angle, c, t = m.group(1), m.group(2), m.group(3)
                return (f"ry({angle}/2) q[{t}];\n"
                        f"cx q[{c}], q[{t}];\n"
                        f"ry(-{angle}/2) q[{t}];\n"
                        f"cx q[{c}], q[{t}];")
            qasm = re.sub(cry_pat, cry_repl, qasm)

            # 2) CP(theta) alias to CU1(theta)
            cp_pat = re.compile(r"^\s*cp\(([^)]+)\)\s+q\[(\d+)\],\s*q\[(\d+)\];\s*$", re.IGNORECASE | re.MULTILINE)
            def cp_repl(m):
                angle, c, t = m.group(1), m.group(2), m.group(3)
                return f"cu1({angle}) q[{c}], q[{t}];"
            qasm = re.sub(cp_pat, cp_repl, qasm)

            # 3) DCX(a,b) ≡ CX(a,b); CX(b,a)
            dcx_pat = re.compile(r"^\s*dcx\s+q\[(\d+)\],\s*q\[(\d+)\];\s*$", re.IGNORECASE | re.MULTILINE)
            def dcx_repl(m):
                a, b = m.group(1), m.group(2)
                return f"cx q[{a}], q[{b}];\ncx q[{b}], q[{a}];"
            qasm = re.sub(dcx_pat, dcx_repl, qasm)

            # 4) RZZ(theta) decomposition via CX-RZ-CX (control=a, target=b)
            rzz_pat = re.compile(r"^\s*rzz\(([^)]+)\)\s+q\[(\d+)\],\s*q\[(\d+)\];\s*$", re.IGNORECASE | re.MULTILINE)
            def rzz_repl(m):
                angle, a, b = m.group(1), m.group(2), m.group(3)
                return f"cx q[{a}], q[{b}];\nrz({angle}) q[{b}];\ncx q[{a}], q[{b}];"
            qasm = re.sub(rzz_pat, rzz_repl, qasm)

            return qasm

        qasm_code = _expand_qasm_aliases(qasm_code)

        # Parse circuit using Qiskit
        try:
            circuit = qasm2.loads(qasm_code)
        except Exception as parse_error:
            validation_info["errors"].append(f"QASM parsing error: {str(parse_error)}")
            return None, validation_info
        
        # Basic circuit info
        validation_info["num_qubits"] = circuit.num_qubits
        validation_info["num_operations"] = len(circuit.data)
        
        if circuit.num_qubits == 0:
            validation_info["errors"].append("Circuit has no qubits")
            return None, validation_info
            
        if circuit.num_qubits > 24:
            validation_info["errors"].append(f"Too many qubits: {circuit.num_qubits} (max 24)")
            return None, validation_info
        
        if len(circuit.data) > 1000:
            validation_info["errors"].append(f"Too many operations: {len(circuit.data)} (max 1000)")
            return None, validation_info
        
        # Validate gates
        supported_gates = []
        unsupported_gates = []
        is_unitary = True
        
        for instruction in circuit.data:
            gate_name = instruction.operation.name.lower()
            
            if gate_name in SUPPORTED_GATES:
                if gate_name not in supported_gates:
                    supported_gates.append(gate_name)
                    
                # Check if operation is non-unitary
                if gate_name in NON_UNITARY_OPS:
                    is_unitary = False
            else:
                if gate_name not in unsupported_gates:
                    unsupported_gates.append(gate_name)
                    validation_info["errors"].append(f"Unsupported gate: {gate_name}")
        
        validation_info["supported_gates"] = supported_gates
        validation_info["unsupported_gates"] = unsupported_gates
        validation_info["is_unitary"] = is_unitary
        
        # Add warnings for potentially problematic circuits
        if len(circuit.data) > 100:
            validation_info["warnings"].append("Large circuit may take time to simulate")
            
        if circuit.num_qubits > 16:
            validation_info["warnings"].append("High qubit count may require trajectory simulation")
        
        # Circuit is valid if no errors and no unsupported gates
        validation_info["is_valid"] = len(validation_info["errors"]) == 0
        
        logger.info(f"Parsed circuit: {circuit.num_qubits} qubits, {len(circuit.data)} ops, unitary={is_unitary}")
        
        return circuit, validation_info
        
    except Exception as e:
        validation_info["errors"].append(f"Unexpected validation error: {str(e)}")
        logger.error(f"Circuit validation failed: {str(e)}")
        return None, validation_info

def route_circuit(circuit: QuantumCircuit, shots: int = 1024, force_pipeline: Optional[str] = None) -> str:
    """
    Route quantum circuit to appropriate simulation pipeline.
    
    Routing logic:
    - Unitary circuits with ≤20 qubits → unitary pipeline
    - Non-unitary circuits:
        * ≤8 qubits → exact_density pipeline (exact mixed-state evolution)
        * 9–16 qubits → trajectory pipeline (Monte Carlo sampling)
        * >16 qubits → trajectory by default (may still exceed limits)
    
    Args:
        circuit: Parsed quantum circuit
        shots: Number of shots for simulation
        force_pipeline: Override automatic routing with specific pipeline
        
    Returns:
        Pipeline name ('unitary', 'exact_density', or 'trajectory')
    """
    if force_pipeline:
        if force_pipeline in ['unitary', 'exact_density', 'trajectory']:
            logger.info(f"Forced routing to {force_pipeline} pipeline")
            return force_pipeline
        else:
            logger.warning(f"Invalid force_pipeline {force_pipeline}, using automatic routing")
    
    # Check if circuit is unitary (no measurements/resets)
    is_unitary = all(
        instr.operation.name.lower() not in NON_UNITARY_OPS 
        for instr in circuit.data
    )
    
    # Debug: Log the operations found
    ops_found = [instr.operation.name.lower() for instr in circuit.data]
    non_unitary_found = [op for op in ops_found if op in NON_UNITARY_OPS]
    logger.info(f"Circuit operations: {ops_found}")
    logger.info(f"Non-unitary operations found: {non_unitary_found}")
    
    qubit_count = circuit.num_qubits
    op_count = len(circuit.data)
    
    # Routing logic aligned with new exact_density limit (8)
    if is_unitary and qubit_count <= 20:
        pipeline = 'unitary'
        reason = f"Unitary circuit with {qubit_count} qubits (≤20)"
    elif not is_unitary:
        if qubit_count <= 8:
            pipeline = 'exact_density'
            reason = f"Non-unitary circuit with {qubit_count} qubits (≤8) → exact density"
        elif qubit_count <= 16:
            pipeline = 'trajectory'
            reason = f"Non-unitary circuit with {qubit_count} qubits (9–16) → trajectory"
        else:
            pipeline = 'trajectory'
            reason = f"Non-unitary circuit with {qubit_count} qubits (>16) → trajectory (may exceed limits)"
    else:
        # Unitary circuits with >20 qubits fall back to exact_density which will likely fail by its own cap
        pipeline = 'exact_density'
        reason = f"Fallback: unitary={is_unitary}, qubits={qubit_count}"
    
    logger.info(f"Routed to {pipeline} pipeline: {reason}")
    return pipeline

def compute_bloch_vector(rho: np.ndarray) -> Tuple[float, float, float]:
    """
    Compute Bloch sphere coordinates from 2x2 density matrix.
    
    Implementation from dev_plane.md:
    rx = 2 * Re(rho[0,1])
    ry = -2 * Im(rho[0,1]) 
    rz = rho[0,0] - rho[1,1]
    
    Args:
        rho: 2x2 density matrix as numpy array
        
    Returns:
        Tuple of (x, y, z) Bloch coordinates
    """
    if rho.shape != (2, 2):
        raise ValueError(f"Expected 2x2 density matrix, got {rho.shape}")
    
    # Bloch vector calculation
    rx = 2.0 * np.real(rho[0, 1])
    ry = -2.0 * np.imag(rho[0, 1])
    rz = np.real(rho[0, 0] - rho[1, 1])
    
    # Clip tiny numerical errors
    rx = clip_tiny_values(rx)
    ry = clip_tiny_values(ry)
    rz = clip_tiny_values(rz)
    
    return (float(rx), float(ry), float(rz))

def compute_purity(rho: np.ndarray) -> float:
    """
    Compute purity of quantum state from density matrix.
    
    Purity = Tr(rho^2)
    Pure states have purity = 1, mixed states < 1
    
    Args:
        rho: Density matrix as numpy array
        
    Returns:
        Purity value between 0 and 1
    """
    if rho.shape != (2, 2):
        raise ValueError(f"Expected 2x2 density matrix, got {rho.shape}")
    
    purity = np.real(np.trace(np.dot(rho, rho)))
    
    # Ensure purity is in valid range
    purity = np.clip(purity, 0.0, 1.0)
    
    return float(purity)

def partial_trace_qubit(state_vector: np.ndarray, total_qubits: int, target_qubit: int) -> np.ndarray:
    """
    Compute partial trace for a single qubit from full state vector.
    
    Args:
        state_vector: Full quantum state vector
        total_qubits: Total number of qubits in system
        target_qubit: Index of qubit to compute reduced density matrix for
        
    Returns:
        2x2 reduced density matrix for target qubit
    """
    # Initialize the reduced density matrix
    rho = np.zeros((2, 2), dtype=complex)
    
    # Sum over all computational basis states
    total_states = 2 ** total_qubits
    
    for i in range(total_states):
        for j in range(total_states):
            # Extract the target qubit state for both i and j
            target_i = (i >> target_qubit) & 1
            target_j = (j >> target_qubit) & 1
            
            # Check if all other qubits are the same between i and j
            # (this is the condition for the partial trace)
            mask = ~(1 << target_qubit) & ((1 << total_qubits) - 1)
            if (i & mask) == (j & mask):
                # Add the contribution to the reduced density matrix
                rho[target_i, target_j] += state_vector[i].conj() * state_vector[j]
    
    return rho

def clip_tiny_values(value: float, threshold: float = 1e-12) -> float:
    """
    Clip tiny values to zero to avoid numerical precision issues.
    
    Implementation from frontend_plan.md: "clip tiny negatives in display (e.g., ≤1e-12 shown as 0)"
    
    Args:
        value: Value to clip
        threshold: Values with absolute value below this are set to 0
        
    Returns:
        Clipped value
    """
    return 0.0 if abs(value) < threshold else value

def format_complex_number(z: complex, precision: int = 4) -> str:
    """
    Format complex number for display with proper precision.
    
    Args:
        z: Complex number to format
        precision: Number of decimal places
        
    Returns:
        Formatted string representation
    """
    real = clip_tiny_values(z.real)
    imag = clip_tiny_values(z.imag)
    
    if imag == 0:
        return f"{real:.{precision}f}"
    elif real == 0:
        return f"{imag:.{precision}f}j"
    else:
        sign = "+" if imag >= 0 else "-"
        return f"{real:.{precision}f}{sign}{abs(imag):.{precision}f}j"

def estimate_simulation_time(circuit: QuantumCircuit, pipeline: str, shots: int = 1024) -> float:
    """
    Estimate simulation execution time based on circuit complexity.
    
    Args:
        circuit: Quantum circuit to simulate
        pipeline: Pipeline to use for simulation
        shots: Number of shots for trajectory simulation
        
    Returns:
        Estimated time in seconds
    """
    n_qubits = circuit.num_qubits
    n_ops = len(circuit.data)
    
    if pipeline == "unitary":
        # Statevector simulation scales as O(2^n * n_ops)
        base_time = 0.001 * (2 ** n_qubits) * n_ops / 1000
    elif pipeline == "trajectory":
        # Trajectory simulation scales as O(shots * n_ops)
        base_time = 0.01 * shots * n_ops / 1000
    else:  # exact_density
        # Density matrix simulation scales as O(4^n * n_ops)
        base_time = 0.01 * (4 ** n_qubits) * n_ops / 1000
    
    # Add overhead and minimum time
    estimated_time = max(0.1, base_time * 1.2)  # 20% overhead, min 0.1s
    
    return estimated_time

def validate_density_matrix(rho: np.ndarray, tolerance: float = 1e-6) -> bool:
    """
    Validate that matrix is a proper density matrix.
    
    Args:
        rho: Matrix to validate
        tolerance: Numerical tolerance for validation
        
    Returns:
        True if valid density matrix, False otherwise
    """
    try:
        # Check shape
        if rho.shape != (2, 2):
            return False
        
        # Check trace = 1
        trace = np.trace(rho)
        if abs(trace - 1.0) > tolerance:
            return False
        
        # Check Hermitian
        if not np.allclose(rho, rho.conj().T, atol=tolerance):
            return False
        
        # Check positive semidefinite (eigenvalues >= 0)
        eigenvals = np.linalg.eigvals(rho)
        if np.any(eigenvals < -tolerance):
            return False
        
        return True
        
    except Exception:
        return False

# Preset quantum circuits for testing
PRESET_CIRCUITS = {
    "bell": """OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
h q[0];
cx q[0], q[1];""",
    
    "ghz": """OPENQASM 2.0;
include "qelib1.inc";
qreg q[3];
h q[0];
cx q[0], q[1];
cx q[1], q[2];""",
    
    "superposition": """OPENQASM 2.0;
include "qelib1.inc";
qreg q[1];
h q[0];""",
    
    "random_unitary": """OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
ry(pi/2) q[0];
rx(pi/4) q[1];
cx q[0], q[1];
rz(pi/6) q[0];""",

    "w_state": """OPENQASM 2.0;
include "qelib1.inc";
qreg q[3];
ry(1.910633236) q[0];
ch q[0], q[1];
ccx q[0], q[1], q[2];
cx q[0], q[1];"""
}
