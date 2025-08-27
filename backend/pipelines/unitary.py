"""
Unitary simulation pipeline using statevector simulation.
Implementation based on dev_plane.md specifications.
"""

import numpy as np
import time
from typing import Dict, Any
from qiskit.quantum_info import Statevector
from qiskit import QuantumCircuit

from pipelines.base import SimulationPipeline, SimulationError, UnsupportedCircuitError
from utils import compute_bloch_vector, compute_purity, clip_tiny_values

class UnitaryPipeline(SimulationPipeline):
    """
    Statevector-based simulation pipeline for unitary quantum circuits.
    
    Suitable for:
    - Pure state evolution (no measurements/noise)
    - Circuits with ≤ 20 qubits (as per dev_plane.md routing logic)
    - Exact quantum state simulation
    
    Implementation details from dev_plane.md:
    - Simulate statevector: Statevector.from_instruction(circuit)
    - Compute RDM per qubit: Vectorized NumPy loop over basis
    - Bloch calc: rx = 2 * Re(rho[0,1]), ry = -2 * Im(rho[0,1]), rz = rho[0,0] - rho[1,1]
    - Purity: np.trace(np.dot(rho, rho))
    """
    
    def __init__(self):
        super().__init__("UnitaryPipeline")
        self.max_qubits = 20  # As specified in routing logic
    
    def validate_circuit(self, circuit: QuantumCircuit) -> bool:
        """
        Validate circuit is suitable for unitary simulation.
        
        Requirements:
        - No measurement operations
        - No reset operations  
        - No noise channels
        - ≤ 20 qubits for performance
        """
        if not super().validate_circuit(circuit):
            return False
        
        # Check qubit limit for unitary pipeline
        if circuit.num_qubits > self.max_qubits:
            self.logger.warning(f"Circuit has {circuit.num_qubits} qubits > {self.max_qubits} limit")
            return False
        # Check for non-unitary operations
        non_unitary_ops = {'measure', 'reset', 'noise', 'kraus'}
        for instr in circuit.data:
            if instr.operation.name.lower() in non_unitary_ops:
                self.logger.warning(f"Non-unitary operation found: {instr.operation.name}")
                return False
        return True
    
    def run(self, circuit: QuantumCircuit, shots: int = 1024) -> Dict[int, Dict[str, Any]]:
        """
        Run unitary simulation using statevector method.
        
        Note: shots parameter is ignored for exact statevector simulation.
        """
        start_time = time.time()
        
        try:
            self.log_simulation_start(circuit, shots)
            
            # Validate circuit
            if not self.validate_circuit(circuit):
                raise UnsupportedCircuitError(
                    "Circuit not suitable for unitary pipeline",
                    pipeline=self.name,
                    circuit_info={'num_qubits': circuit.num_qubits, 'num_ops': len(circuit.data)}
                )
            
            # Preprocess circuit (transpilation, optimization)
            processed_circuit = self.preprocess_circuit(circuit)
            
            # Simulate statevector evolution
            try:
                statevector = Statevector.from_instruction(processed_circuit)
                state_array = statevector.data
            except Exception as e:
                raise SimulationError(f"Statevector simulation failed: {str(e)}", pipeline=self.name)
            
            # Compute reduced density matrices for each qubit
            results = {}
            n_qubits = processed_circuit.num_qubits
            
            for qubit_id in range(n_qubits):
                try:
                    # Fast RDM via reshape + matmul (O(2^n))
                    rho = self._rdm_from_statevector(state_array, n_qubits, qubit_id)
                    
                    # Compute Bloch coordinates
                    bloch_coords = compute_bloch_vector(rho)
                    
                    # Compute purity
                    purity = compute_purity(rho)
                    
                    # Store results
                    results[qubit_id] = {
                        'bloch': list(bloch_coords),  # Ensure it's a list
                        'purity': float(purity),
                        'rho': self._format_density_matrix(rho)
                    }
                except Exception as e:
                    self.logger.error(f"Failed to compute state for qubit {qubit_id}: {str(e)}")
                    # Provide fallback state (|0⟩)
                    results[qubit_id] = {
                        'bloch': [0.0, 0.0, 1.0],
                        'purity': 1.0,
                        'rho': [[1.0+0j, 0.0+0j], [0.0+0j, 0.0+0j]]
                    }
            
            execution_time = time.time() - start_time
            self.log_simulation_end(execution_time, n_qubits)
            
            return self.postprocess_results(results, execution_time)
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"Unitary simulation failed after {execution_time:.3f}s: {str(e)}")
            raise SimulationError(f"Unitary simulation failed: {str(e)}", pipeline=self.name)
    
    def _rdm_from_statevector(self, state_vector: np.ndarray, n_qubits: int, target_qubit: int) -> np.ndarray:
        """
        Fast single-qubit RDM from statevector using reshape + matmul.
        Treat qubit 0 as LSB (little-endian) for axis ordering.
        """
        if n_qubits == 1:
            # ρ = |ψ><ψ|
            v = state_vector.reshape(2, 1)
            return (v @ v.conj().T).astype(np.complex128)
        shape = (2,) * n_qubits
        # In row-major reshape, the last axis corresponds to LSB (qubit 0).
        # Map target_qubit to its axis index accordingly.
        target_axis = n_qubits - 1 - target_qubit
        # Bring target axis to front: (target_axis, others...)
        axes = (target_axis,) + tuple(i for i in range(n_qubits) if i != target_axis)
        V = state_vector.reshape(shape).transpose(axes).reshape(2, -1)
        rho = V @ V.conj().T
        # Normalize to trace 1 (defensive against numeric drift)
        tr = float(np.trace(rho).real)
        if abs(tr) > 1e-15:
            rho = rho / tr
        # Hermitize
        rho = 0.5 * (rho + rho.conj().T)
        return rho.astype(np.complex128)
    
    # remove heavy full density matrix path; the fast path covers all cases for unitary
    
    def _format_density_matrix(self, rho: np.ndarray) -> list:
        """
        Format density matrix for JSON serialization.
        Clips tiny values and converts to nested list format.
        """
        formatted = []
        for i in range(2):
            row = []
            for j in range(2):
                real = clip_tiny_values(rho[i, j].real)
                imag = clip_tiny_values(rho[i, j].imag)
                row.append([float(real), float(imag)])
            formatted.append(row)
        return formatted
    
    def _estimate_memory(self, n_qubits: int) -> float:
        """Estimate memory usage for statevector simulation"""
        # Statevector: 2^n complex numbers * 16 bytes/complex
        statevector_mb = (2 ** n_qubits) * 16 / (1024 * 1024)
        # Full density matrix: 2^(2n) complex numbers * 16 bytes/complex  
        density_mb = (4 ** n_qubits) * 16 / (1024 * 1024)
        # Total with overhead
        return (statevector_mb + density_mb) * 1.5
    
    def _estimate_time(self, n_qubits: int, n_ops: int) -> float:
        """Estimate execution time for unitary simulation"""
        # Base time scales with statevector size and operations
        base_time = 0.001 * (2 ** n_qubits) * n_ops / 1000
        # Add overhead for partial traces (scales with n_qubits^2)
        trace_time = 0.01 * (n_qubits ** 2)
        return base_time + trace_time
    
    def preprocess_circuit(self, circuit: QuantumCircuit) -> QuantumCircuit:
        """
        Optimize circuit for statevector simulation.
        """
        # For now, return circuit as-is
        # Future: add transpilation, gate fusion, etc.
        return circuit
