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
        non_unitary_ops = {'measure', 'reset', 'noise', 'kraus', 'barrier'}
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
                    # Compute reduced density matrix using utility function
                    from utils import partial_trace_qubit
                    rho = partial_trace_qubit(state_array, n_qubits, qubit_id)
                    
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
    
    def _compute_reduced_density_matrix(self, state_vector: np.ndarray, n_qubits: int, 
                                      target_qubit: int) -> np.ndarray:
        """
        Compute reduced density matrix for target qubit using partial trace.
        
        This is a vectorized implementation for efficiency with larger systems.
        """
        # Convert statevector to full density matrix
        rho_full = np.outer(state_vector.conj(), state_vector)
        
        # Reshape to tensor form for partial trace
        dim = 2 ** n_qubits
        rho_tensor = rho_full.reshape([2] * (2 * n_qubits))
        
        # Perform partial trace over all qubits except target
        # This traces out qubits in order, keeping target_qubit
        axes_to_trace = []
        for i in range(n_qubits):
            if i != target_qubit:
                # Each qubit appears twice in tensor (bra and ket)
                axes_to_trace.extend([i, i + n_qubits])
        
        # Sort axes in descending order for sequential tracing
        axes_to_trace.sort(reverse=True)
        
        # Trace over unwanted qubits
        rho_reduced = rho_tensor
        traced_axes = 0
        for axis in axes_to_trace:
            adjusted_axis = axis - traced_axes
            # Find the corresponding axis pair
            if adjusted_axis >= len(rho_reduced.shape) // 2:
                bra_axis = adjusted_axis
                ket_axis = adjusted_axis - len(rho_reduced.shape) // 2
            else:
                bra_axis = adjusted_axis + len(rho_reduced.shape) // 2
                ket_axis = adjusted_axis
            
            # Adjust for previous traces
            if bra_axis > ket_axis:
                bra_axis -= traced_axes // 2
                ket_axis -= traced_axes // 2
            else:
                ket_axis -= traced_axes // 2
                bra_axis -= traced_axes // 2
            
            rho_reduced = np.trace(rho_reduced, axis1=min(bra_axis, ket_axis), 
                                 axis2=max(bra_axis, ket_axis))
            traced_axes += 2
        
        # Ensure final result is 2x2
        if rho_reduced.shape != (2, 2):
            # Alternative method: direct computation
            return self._compute_rdm_direct(state_vector, n_qubits, target_qubit)
        
        return rho_reduced.astype(np.complex128)
    
    def _compute_rdm_direct(self, state_vector: np.ndarray, n_qubits: int, 
                           target_qubit: int) -> np.ndarray:
        """
        Direct computation of reduced density matrix using basis projection.
        Fallback method when tensor tracing fails.
        """
        rho = np.zeros((2, 2), dtype=np.complex128)
        
        # Iterate over all computational basis states
        for i in range(2**n_qubits):
            for j in range(2**n_qubits):
                # Extract target qubit states
                target_i = (i >> target_qubit) & 1
                target_j = (j >> target_qubit) & 1
                
                # Check if other qubits match
                mask = ~(1 << target_qubit) & ((1 << n_qubits) - 1)
                if (i & mask) == (j & mask):
                    rho[target_i, target_j] += state_vector[i].conj() * state_vector[j]
        
        return rho
    
    def _format_density_matrix(self, rho: np.ndarray) -> list:
        """
        Format density matrix for JSON serialization.
        Clips tiny values and converts to nested list format.
        """
        formatted = []
        for i in range(2):
            row = []
            for j in range(2):
                # Clip tiny values
                real = clip_tiny_values(rho[i, j].real)
                imag = clip_tiny_values(rho[i, j].imag)
                row.append(complex(real, imag))
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
