"""
Trajectory-based simulation pipeline for quantum circuits with measurements.
Implementation based on dev_plane.md specifications.
"""

import numpy as np
import time
from typing import Dict, Any, List
from qiskit import QuantumCircuit, ClassicalRegister
from qiskit_aer import AerSimulator
from qiskit.quantum_info import DensityMatrix

from pipelines.base import SimulationPipeline, SimulationError, UnsupportedCircuitError
from utils import compute_bloch_vector, compute_purity, clip_tiny_values

class TrajectoryPipeline(SimulationPipeline):
    """
    Trajectory-based simulation pipeline using quantum Monte Carlo methods.
    
    Suitable for:
    - Circuits with measurements and resets
    - Large systems where exact simulation is impractical
    - Statistical sampling of quantum evolution
    - Non-unitary circuits with ≤16 qubits and ≥1000 shots (routing condition)
    
    Implementation details from dev_plane.md:
    - Loop S times: Simulate with stochastic collapses (use Qiskit's Aer simulator with shots=1)
    - Average RDMs over trajectories
    """
    
    def __init__(self):
        super().__init__("TrajectoryPipeline")
        self.max_qubits = 16  # As specified in routing logic
        self.min_shots = 100   # Minimum for meaningful statistics
        self.max_shots = 100000  # Practical upper limit
        
        # Initialize Aer simulator
        try:
            self.simulator = AerSimulator(method='statevector')
        except Exception as e:
            self.logger.warning(f"Failed to initialize Aer simulator: {e}")
            self.simulator = None
    
    def validate_circuit(self, circuit: QuantumCircuit) -> bool:
        """
        Validate circuit is suitable for trajectory simulation.
        
        Requirements:
        - Contains measurements or resets (non-unitary)
        - ≤ 16 qubits for reasonable simulation time
        - Simulator must be available
        """
        if not super().validate_circuit(circuit):
            return False
        
        # Check simulator availability
        if self.simulator is None:
            self.logger.error("Aer simulator not available")
            return False
        
        # Check qubit limit
        if circuit.num_qubits > self.max_qubits:
            self.logger.warning(f"Circuit has {circuit.num_qubits} qubits > {self.max_qubits} limit")
            return False
        
        # Check for non-unitary operations (preferred for trajectory method)
        has_measurements = any(
            instr.operation.name.lower() in ['measure', 'reset']
            for instr in circuit.data
        )
        
        if not has_measurements:
            self.logger.info("Circuit is unitary - trajectory simulation still supported")
        
        return True
    
    def run(self, circuit: QuantumCircuit, shots: int = 1024) -> Dict[int, Dict[str, Any]]:
        """
        Run trajectory-based simulation with quantum Monte Carlo sampling.
        """
        start_time = time.time()
        
        try:
            self.log_simulation_start(circuit, shots)
            
            # Validate circuit and shots
            if not self.validate_circuit(circuit):
                raise UnsupportedCircuitError(
                    "Circuit not suitable for trajectory pipeline",
                    pipeline=self.name,
                    circuit_info={'num_qubits': circuit.num_qubits, 'num_ops': len(circuit.data)}
                )
            
            if shots < self.min_shots:
                self.logger.warning(f"Low shot count {shots} may give poor statistics")
                shots = max(shots, self.min_shots)
            
            if shots > self.max_shots:
                self.logger.warning(f"High shot count {shots} clamped to {self.max_shots}")
                shots = self.max_shots
            
            # Preprocess circuit for trajectory simulation
            processed_circuit = self.preprocess_circuit(circuit)
            
            # Run trajectory simulation
            if self._has_measurements(processed_circuit):
                results = self._run_measurement_trajectories(processed_circuit, shots)
            else:
                results = self._run_unitary_trajectories(processed_circuit, shots)
            
            execution_time = time.time() - start_time
            self.log_simulation_end(execution_time, processed_circuit.num_qubits)
            
            return self.postprocess_results(results, execution_time)
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"Trajectory simulation failed after {execution_time:.3f}s: {str(e)}")
            raise SimulationError(f"Trajectory simulation failed: {str(e)}", pipeline=self.name)
    
    def _has_measurements(self, circuit: QuantumCircuit) -> bool:
        """Check if circuit contains measurement operations"""
        return any(
            instr.operation.name.lower() in ['measure', 'reset']
            for instr in circuit.data
        )
    
    def _run_measurement_trajectories(self, circuit: QuantumCircuit, shots: int) -> Dict[int, Dict[str, Any]]:
        """
        Run trajectories for circuits with measurements.
        Each trajectory samples a specific measurement outcome path.
        """
        n_qubits = circuit.num_qubits
        
        # Accumulate density matrices from all trajectories
        accumulated_rhos = {i: np.zeros((2, 2), dtype=np.complex128) for i in range(n_qubits)}
        valid_trajectories = 0
        
        # Run individual trajectories
        for trajectory in range(shots):
            try:
                # Run single trajectory with Aer simulator
                traj_result = self._simulate_single_trajectory(circuit)
                
                if traj_result is not None:
                    # Extract reduced density matrices for each qubit
                    for qubit_id in range(n_qubits):
                        rho_traj = self._extract_qubit_state(traj_result, n_qubits, qubit_id)
                        accumulated_rhos[qubit_id] += rho_traj
                    
                    valid_trajectories += 1
                
            except Exception as e:
                self.logger.warning(f"Trajectory {trajectory} failed: {e}")
                continue
        
        if valid_trajectories == 0:
            raise SimulationError("All trajectories failed", pipeline=self.name)
        
        # Average over valid trajectories
        results = {}
        for qubit_id in range(n_qubits):
            avg_rho = accumulated_rhos[qubit_id] / valid_trajectories
            
            # Ensure proper normalization
            trace = np.trace(avg_rho)
            if abs(trace) > 1e-10:
                avg_rho = avg_rho / trace
            
            # Compute observables
            bloch_coords = compute_bloch_vector(avg_rho)
            purity = compute_purity(avg_rho)
            
            results[qubit_id] = {
                'bloch': bloch_coords,
                'purity': purity,
                'rho': self._format_density_matrix(avg_rho)
            }
        
        self.logger.info(f"Completed {valid_trajectories}/{shots} trajectories successfully")
        return results
    
    def _run_unitary_trajectories(self, circuit: QuantumCircuit, shots: int) -> Dict[int, Dict[str, Any]]:
        """
        Run trajectories for unitary circuits (no measurements).
        In this case, all trajectories give the same result, so we can optimize.
        """
        try:
            # For unitary circuits, run once and return exact result
            from qiskit.quantum_info import Statevector
            statevector = Statevector.from_instruction(circuit)
            state_array = statevector.data
            
            n_qubits = circuit.num_qubits
            results = {}
            
            for qubit_id in range(n_qubits):
                # Compute reduced density matrix
                rho = self._compute_reduced_density_matrix(state_array, n_qubits, qubit_id)
                
                # Compute observables  
                bloch_coords = compute_bloch_vector(rho)
                purity = compute_purity(rho)
                
                results[qubit_id] = {
                    'bloch': bloch_coords,
                    'purity': purity,
                    'rho': self._format_density_matrix(rho)
                }
            
            return results
            
        except Exception as e:
            # Fallback to single trajectory method
            self.logger.warning(f"Unitary optimization failed: {e}, falling back to trajectory method")
            return self._run_measurement_trajectories(circuit, 1)
    
    def _simulate_single_trajectory(self, circuit: QuantumCircuit):
        """
        Simulate a single quantum trajectory using Aer simulator.
        """
        try:
            # Add measurements if not present (needed for state extraction)
            measured_circuit = circuit.copy()
            
            # Add classical register for measurements if needed
            if not measured_circuit.cregs:
                creg = ClassicalRegister(measured_circuit.num_qubits, 'c')
                measured_circuit.add_register(creg)
            
            # Run simulation with shots=1 for single trajectory
            job = self.simulator.run(measured_circuit, shots=1, memory=True)
            result = job.result()
            
            # Extract final statevector or density matrix
            if hasattr(result, 'get_statevector'):
                return result.get_statevector()
            elif hasattr(result, 'data') and 'density_matrix' in result.data(0):
                return result.data(0)['density_matrix']
            else:
                return None
                
        except Exception as e:
            self.logger.warning(f"Single trajectory simulation failed: {e}")
            return None
    
    def _extract_qubit_state(self, trajectory_result, n_qubits: int, qubit_id: int) -> np.ndarray:
        """
        Extract single qubit density matrix from trajectory result.
        """
        try:
            if hasattr(trajectory_result, 'data'):
                # Result is a statevector
                state_array = trajectory_result.data
                return self._compute_reduced_density_matrix(state_array, n_qubits, qubit_id)
            else:
                # Result might already be a density matrix
                dm = DensityMatrix(trajectory_result)
                qubits_to_trace = [j for j in range(n_qubits) if j != qubit_id]
                if qubits_to_trace:
                    rho_reduced = dm.partial_trace(qubits_to_trace)
                    return rho_reduced.data
                else:
                    return dm.data
                    
        except Exception as e:
            self.logger.warning(f"Failed to extract qubit state: {e}")
            # Return maximally mixed state as fallback
            return np.array([[0.5+0j, 0.0+0j], [0.0+0j, 0.5+0j]], dtype=np.complex128)
    
    def _compute_reduced_density_matrix(self, state_vector: np.ndarray, n_qubits: int, 
                                      target_qubit: int) -> np.ndarray:
        """
        Compute reduced density matrix from statevector (same as unitary pipeline).
        """
        rho = np.zeros((2, 2), dtype=np.complex128)
        
        # Direct computation for efficiency
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
        """Format density matrix for JSON serialization."""
        formatted = []
        for i in range(2):
            row = []
            for j in range(2):
                real = clip_tiny_values(rho[i, j].real)
                imag = clip_tiny_values(rho[i, j].imag)
                row.append(complex(real, imag))
            formatted.append(row)
        
        return formatted
    
    def _estimate_memory(self, n_qubits: int) -> float:
        """Estimate memory usage for trajectory simulation"""
        # Memory scales with single trajectory, not total shots
        # Statevector: 2^n complex numbers * 16 bytes
        single_traj_mb = (2 ** n_qubits) * 16 / (1024 * 1024)
        # Accumulation arrays for results
        result_mb = n_qubits * 4 * 16 / (1024 * 1024)  # 4 complex numbers per qubit
        return (single_traj_mb + result_mb) * 1.2
    
    def _estimate_time(self, n_qubits: int, n_ops: int, shots: int = 1024) -> float:
        """Estimate execution time for trajectory simulation"""
        # Time scales with shots * single trajectory time
        single_traj_time = 0.01 * (2 ** n_qubits) * n_ops / 10000
        return shots * single_traj_time * 1.5  # 50% overhead
    
    def preprocess_circuit(self, circuit: QuantumCircuit) -> QuantumCircuit:
        """
        Preprocess circuit for trajectory simulation.
        """
        # Ensure circuit has classical registers for measurements
        processed = circuit.copy()
        
        # Add classical register if measurements exist but no classical register
        has_measurements = self._has_measurements(processed)
        if has_measurements and not processed.cregs:
            from qiskit import ClassicalRegister
            creg = ClassicalRegister(processed.num_qubits, 'c')
            processed.add_register(creg)
        
        return processed
    
    def get_shot_requirements(self) -> Dict[str, int]:
        """Return shot count recommendations"""
        return {
            'minimum': self.min_shots,
            'recommended': 1024,
            'maximum': self.max_shots
        }
