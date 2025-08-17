"""
Exact density matrix simulation pipeline.
Implementation based on dev_plane.md specifications.
"""

import numpy as np
import time
from typing import Dict, Any
from qiskit.quantum_info import DensityMatrix
from qiskit import QuantumCircuit

from pipelines.base import SimulationPipeline, SimulationError, ResourceLimitError
from utils import compute_bloch_vector, compute_purity, clip_tiny_values

class ExactDensityPipeline(SimulationPipeline):
    """
    Exact density matrix simulation pipeline for quantum circuits.
    
    Suitable for:
    - Circuits with noise/measurements
    - Mixed quantum states
    - Fallback for complex circuits that don't fit other pipelines
    - Systems where exact density matrix evolution is needed
    
    Implementation details from dev_plane.md:
    - Use DensityMatrix.from_instruction(circuit)
    - Partial trace: dm.partial_trace([j for j in range(n_qubits) if j != i])
    """
    
    def __init__(self):
        super().__init__("ExactDensityPipeline")
        self.max_qubits = 16  # Density matrices scale as 4^n
    
    def validate_circuit(self, circuit: QuantumCircuit) -> bool:
        """
        Validate circuit is suitable for exact density simulation.
        
        This pipeline is more permissive than unitary pipeline:
        - Allows measurements and resets
        - Handles noise channels (if added later)
        - Limited by memory constraints (4^n scaling)
        """
        if not super().validate_circuit(circuit):
            return False
        
        # Check qubit limit for density matrix simulation
        if circuit.num_qubits > self.max_qubits:
            self.logger.warning(f"Circuit has {circuit.num_qubits} qubits > {self.max_qubits} limit")
            return False
        
        return True
    
    def run(self, circuit: QuantumCircuit, shots: int = 1024) -> Dict[int, Dict[str, Any]]:
        """
        Run exact density matrix simulation.
        
        Note: shots parameter is ignored for exact density matrix simulation.
        """
        start_time = time.time()
        
        try:
            self.log_simulation_start(circuit, shots)
            
            # Validate circuit
            if not self.validate_circuit(circuit):
                raise ResourceLimitError(
                    f"Circuit exceeds density matrix simulation limits: {circuit.num_qubits} qubits",
                    pipeline=self.name,
                    circuit_info={'num_qubits': circuit.num_qubits, 'num_ops': len(circuit.data)}
                )
            
            # Preprocess circuit
            processed_circuit = self.preprocess_circuit(circuit)
            
            # Simulate full density matrix evolution
            try:
                density_matrix = DensityMatrix.from_instruction(processed_circuit)
                dm_array = density_matrix.data
            except Exception as e:
                raise SimulationError(f"Density matrix simulation failed: {str(e)}", pipeline=self.name)
            
            # Compute reduced density matrices for each qubit
            results = {}
            n_qubits = processed_circuit.num_qubits
            
            for qubit_id in range(n_qubits):
                try:
                    # Compute reduced density matrix using Qiskit's partial trace
                    qubits_to_trace = [j for j in range(n_qubits) if j != qubit_id]
                    
                    if qubits_to_trace:
                        # Partial trace over other qubits
                        rho_reduced = density_matrix.partial_trace(qubits_to_trace)
                        rho = rho_reduced.data
                    else:
                        # Single qubit case - use full density matrix
                        rho = dm_array
                    
                    # Ensure 2x2 matrix
                    if rho.shape != (2, 2):
                        self.logger.warning(f"Unexpected density matrix shape {rho.shape} for qubit {qubit_id}")
                        # Fallback to manual computation
                        rho = self._compute_reduced_density_matrix_manual(dm_array, n_qubits, qubit_id)
                    
                    # Compute Bloch coordinates
                    bloch_coords = compute_bloch_vector(rho)
                    
                    # Compute purity
                    purity = compute_purity(rho)
                    
                    # Store results
                    results[qubit_id] = {
                        'bloch': bloch_coords,
                        'purity': purity,
                        'rho': self._format_density_matrix(rho)
                    }
                    
                except Exception as e:
                    self.logger.error(f"Failed to compute state for qubit {qubit_id}: {str(e)}")
                    # Provide fallback state (maximally mixed)
                    results[qubit_id] = {
                        'bloch': [0.0, 0.0, 0.0],
                        'purity': 0.5,
                        'rho': [[0.5+0j, 0.0+0j], [0.0+0j, 0.5+0j]]
                    }
            
            execution_time = time.time() - start_time
            self.log_simulation_end(execution_time, n_qubits)
            
            return self.postprocess_results(results, execution_time)
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"Exact density simulation failed after {execution_time:.3f}s: {str(e)}")
            raise SimulationError(f"Exact density simulation failed: {str(e)}", pipeline=self.name)
    
    def _compute_reduced_density_matrix_manual(self, dm_full: np.ndarray, n_qubits: int, 
                                             target_qubit: int) -> np.ndarray:
        """
        Manual computation of reduced density matrix when Qiskit method fails.
        """
        try:
            # Reshape density matrix to tensor form
            shape = [2] * (2 * n_qubits)
            dm_tensor = dm_full.reshape(shape)
            
            # Trace over unwanted qubits
            axes_to_trace = []
            for i in range(n_qubits):
                if i != target_qubit:
                    axes_to_trace.extend([i, i + n_qubits])
            
            # Perform traces sequentially
            dm_reduced = dm_tensor
            for _ in range(len(axes_to_trace) // 2):
                # Find next pair to trace
                ax1 = 0
                ax2 = len(dm_reduced.shape) // 2
                dm_reduced = np.trace(dm_reduced, axis1=ax1, axis2=ax2)
            
            return dm_reduced.astype(np.complex128)
            
        except Exception as e:
            self.logger.warning(f"Manual density matrix computation failed: {e}")
            # Return maximally mixed state as fallback
            return np.array([[0.5+0j, 0.0+0j], [0.0+0j, 0.5+0j]], dtype=np.complex128)
    
    def _format_density_matrix(self, rho: np.ndarray) -> list:
        """
        Format density matrix for JSON serialization.
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
        """Estimate memory usage for density matrix simulation"""
        # Full density matrix: 4^n complex numbers * 16 bytes/complex
        density_mb = (4 ** n_qubits) * 16 / (1024 * 1024)
        # Additional workspace for operations
        workspace_mb = density_mb * 2
        # Total with overhead
        return (density_mb + workspace_mb) * 1.5
    
    def _estimate_time(self, n_qubits: int, n_ops: int) -> float:
        """Estimate execution time for density matrix simulation"""
        # Base time scales with density matrix size and operations
        base_time = 0.01 * (4 ** n_qubits) * n_ops / 1000
        # Add overhead for partial traces (scales with n_qubits^3)
        trace_time = 0.1 * (n_qubits ** 3)
        return base_time + trace_time
    
    def preprocess_circuit(self, circuit: QuantumCircuit) -> QuantumCircuit:
        """
        Optimize circuit for density matrix simulation.
        """
        # For now, return circuit as-is
        # Future optimizations:
        # - Remove redundant operations
        # - Combine adjacent single-qubit gates
        # - Optimize measurement handling
        return circuit
    
    def supports_measurements(self) -> bool:
        """This pipeline supports measurements"""
        return True
    
    def supports_noise(self) -> bool:
        """This pipeline can support noise (when implemented)"""
        return True
    
    def get_max_qubits(self) -> int:
        """Return maximum number of qubits this pipeline can handle"""
        return self.max_qubits
