"""
Exact density matrix simulation pipeline.
Implementation based on dev_plane.md specifications.
"""

import numpy as np
import time
from typing import Dict, Any
from qiskit import QuantumCircuit, transpile
from qiskit.quantum_info import DensityMatrix
from qiskit_aer import AerSimulator

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
        # Density matrices scale as 4^n; cap tightened to 8 for safety/perf
        self.max_qubits = 8
    
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
            
            # Simulate full density matrix evolution using Aer density_matrix backend
            try:
                sim = AerSimulator(method='density_matrix')
                circ = processed_circuit.copy()
                # Ensure final density matrix is saved
                try:
                    circ.save_density_matrix()
                except Exception:
                    # Older Aer APIs: add via instruction import if needed
                    from qiskit.providers.aer.library import SaveDensityMatrix  # type: ignore
                    circ.append(SaveDensityMatrix(), [])
                tcirc = transpile(circ, sim)
                result = sim.run(tcirc, shots=1).result()
                data0 = result.data(0)
                dm = data0.get('density_matrix', None)
                if dm is None:
                    raise RuntimeError("No density_matrix in simulation result")
                dm_array = np.array(dm, dtype=np.complex128)
            except Exception as e:
                # Fallback: try unitary-only path for strictly unitary circuits
                try:
                    density_matrix = DensityMatrix.from_instruction(processed_circuit)
                    dm_array = density_matrix.data
                except Exception:
                    raise SimulationError(f"Density matrix simulation failed: {str(e)}", pipeline=self.name)
            
            # Compute reduced density matrices for each qubit
            results = {}
            n_qubits = processed_circuit.num_qubits
            
            # Wrap full density into Qiskit object once for partial_trace convenience
            dm_qi = DensityMatrix(dm_array)
            for qubit_id in range(n_qubits):
                try:
                    # Compute reduced density matrix using Qiskit's partial trace
                    qubits_to_trace = [j for j in range(n_qubits) if j != qubit_id]
                    
                    if qubits_to_trace:
                        # Partial trace over other qubits
                        rho_reduced = dm_qi.partial_trace(qubits_to_trace)
                        rho = rho_reduced.data
                    else:
                        # Single qubit case - use full density matrix
                        rho = dm_array
                    
                    # Ensure 2x2 matrix
                    if rho.shape != (2, 2):
                        self.logger.warning(f"Unexpected density matrix shape {rho.shape} for qubit {qubit_id}")
                        # Fallback to manual computation
                        rho = self._compute_reduced_density_matrix_manual(dm_array, n_qubits, qubit_id)
                    # Enforce Hermiticity and trace normalization defensively
                    rho = 0.5 * (rho + rho.conj().T)
                    tr = float(np.trace(rho).real)
                    if abs(tr) > 1e-15:
                        rho = rho / tr
                    
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
                        'rho': [[[0.5, 0.0], [0.0, 0.0]], [[0.0, 0.0], [0.5, 0.0]]]
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
            if n_qubits == 1:
                # Already 2x2
                rho = dm_full
            else:
                # Reshape to (2,)*n (bra) + (2,)*n (ket)
                shape = (2,) * (2 * n_qubits)
                dm_tensor = dm_full.reshape(shape)
                # Bring target bra axis first, target ket axis next block start
                perm = (target_qubit,
                        *[i for i in range(n_qubits) if i != target_qubit],
                        target_qubit + n_qubits,
                        *[i + n_qubits for i in range(n_qubits) if i != target_qubit])
                dm_perm = dm_tensor.transpose(perm)
                # Now shape is (2, 2^(n-1), 2, 2^(n-1)); trace over middle dims (diagonal)
                m = 1 << (n_qubits - 1)
                dm_shaped = dm_perm.reshape(2, m, 2, m)
                rho = np.einsum('aibi->ab', dm_shaped)
            # Defensive normalization and Hermiticity
            rho = 0.5 * (rho + rho.conj().T)
            tr = float(np.trace(rho).real)
            if abs(tr) > 1e-15:
                rho = rho / tr
            return rho.astype(np.complex128)
        except Exception as e:
            self.logger.warning(f"Manual density matrix computation failed: {e}")
            return np.array([[0.5+0j, 0.0+0j], [0.0+0j, 0.5+0j]], dtype=np.complex128)
    
    def _format_density_matrix(self, rho: np.ndarray) -> list:
        """Format density matrix for JSON serialization as [[re,im],...]."""
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
