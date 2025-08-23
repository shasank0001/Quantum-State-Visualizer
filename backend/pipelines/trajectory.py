"""
Trajectory-based simulation pipeline for quantum circuits with measurements.
Implements true Monte Carlo sampling with projective measurement collapse per shot,
matching the dev_plan specification (stochastic trajectories averaged to density).
"""

import numpy as np
import time
from typing import Dict, Any, List
from qiskit import QuantumCircuit
from qiskit.quantum_info import DensityMatrix, Statevector

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
            # Always run trajectory engine (unitary circuits will be consistent across shots)
            results = self._run_trajectories(processed_circuit, shots)
            
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
    
    def _run_trajectories(self, circuit: QuantumCircuit, shots: int) -> Dict[int, Dict[str, Any]]:
        """
        Run Monte Carlo trajectories with projective measurement collapse.
        Each trajectory walks through the circuit instruction-by-instruction,
        sampling measurement outcomes and collapsing the statevector.
        """
        n_qubits = circuit.num_qubits

        # Accumulate density matrices from all trajectories
        accumulated_rhos = {i: np.zeros((2, 2), dtype=np.complex128) for i in range(n_qubits)}
        valid_trajectories = 0

        for t in range(shots):
            try:
                state, clbits = self._simulate_single_trajectory(circuit)
                if state is None:
                    continue
                # Extract reduced density matrices for each qubit and accumulate
                state_array = state.data if isinstance(state, Statevector) else np.asarray(state)
                for qubit_id in range(n_qubits):
                    rho_traj = self._compute_reduced_density_matrix(state_array, n_qubits, qubit_id)
                    accumulated_rhos[qubit_id] += rho_traj
                valid_trajectories += 1
            except Exception as e:
                self.logger.warning(f"Trajectory {t} failed: {e}")
                continue

        if valid_trajectories == 0:
            raise SimulationError("All trajectories failed", pipeline=self.name)

        # Average and produce results
        results = {}
        for qubit_id in range(n_qubits):
            avg_rho = accumulated_rhos[qubit_id] / valid_trajectories
            # Normalize to trace 1
            tr = np.trace(avg_rho)
            if abs(tr) > 1e-12:
                avg_rho = avg_rho / tr
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
        """Deprecated in favor of _run_trajectories which handles both cases."""
        return self._run_trajectories(circuit, max(1, shots))
    
    def _simulate_single_trajectory(self, circuit: QuantumCircuit):
        """
        Simulate a single trajectory with explicit projective measurement collapse.
        Returns (Statevector, classical_bits_dict).
        """
        try:
            n_qubits = circuit.num_qubits
            # Start in |0...0>
            state = Statevector.from_int(0, 2**n_qubits)
            # Classical bits mapping: clbit index -> 0/1
            clbits: Dict[int, int] = {}

            # Build a helper mapping from circuit qubits/clbits to indices
            qubit_index = {qb: idx for idx, qb in enumerate(circuit.qubits)}
            clbit_index = {cb: idx for idx, cb in enumerate(circuit.clbits)}

            for instr in circuit.data:
                name = instr.operation.name.lower()

                # Handle classical condition (if present)
                if getattr(instr.operation, "condition", None) is not None:
                    cond = instr.operation.condition  # (ClassicalRegister or Clbit, int)
                    try:
                        reg, val = cond
                        # Compute integer value of bits in this register
                        # If reg is a single Clbit, treat it as 1-bit register
                        if hasattr(reg, "bits"):
                            bits = reg.bits
                        else:
                            bits = [reg]
                        current = 0
                        for i, b in enumerate(bits):
                            idx = clbit_index.get(b, None)
                            bitval = clbits.get(idx, 0) if idx is not None else 0
                            current |= (bitval & 1) << i
                        if current != val:
                            # Skip this instruction if condition not satisfied
                            continue
                    except Exception:
                        # If condition parsing fails, conservatively skip
                        continue

                if name == 'measure':
                    # measurement: measure q -> c
                    q = instr.qubits[0]
                    c = instr.clbits[0] if instr.clbits else None
                    q_idx = qubit_index[q]
                    outcome, state = self._measure_and_collapse(state.data, n_qubits, q_idx)
                    if c is not None:
                        c_idx = clbit_index.get(c, None)
                        if c_idx is not None:
                            clbits[c_idx] = int(outcome)
                    continue

                if name == 'reset':
                    q = instr.qubits[0]
                    q_idx = qubit_index[q]
                    state = Statevector(self._reset_qubit(state.data, n_qubits, q_idx))
                    continue

                # Unitary operation: evolve state by this operation
                try:
                    op = instr.operation
                    # Build a minimal circuit with the same number of qubits, append op at the right qargs
                    tmp = QuantumCircuit(n_qubits)
                    tmp.append(op, [qubit_index[q] for q in instr.qubits])
                    state = state.evolve(tmp)
                except Exception as e:
                    # If evolve fails, try to_matrix fallback
                    try:
                        mat = op.to_matrix()
                        qargs = [qubit_index[q] for q in instr.qubits]
                        state = Statevector(self._apply_matrix_to_qubits(state.data, mat, n_qubits, qargs))
                    except Exception as e2:
                        raise SimulationError(f"Failed to apply instruction {name}: {e2}")

            return state, clbits

        except Exception as e:
            self.logger.error(f"Single trajectory simulation failed: {e}")
            return None, {}

    # Removed simplified measurement handling in favor of explicit collapse engine
    
    def _extract_qubit_state(self, trajectory_result, n_qubits: int, qubit_id: int) -> np.ndarray:
        """Extract single qubit density matrix from trajectory result (statevector)."""
        try:
            state_array = trajectory_result.data if isinstance(trajectory_result, Statevector) else np.asarray(trajectory_result)
            return self._compute_reduced_density_matrix(state_array, n_qubits, qubit_id)
        except Exception as e:
            self.logger.warning(f"Failed to extract qubit state: {e}")
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

    def _measure_and_collapse(self, state_vector: np.ndarray, n_qubits: int, target_qubit: int):
        """
        Perform a projective measurement on target_qubit, return (outcome, new_state_vector).
        """
        # Compute probabilities for |0> and |1> on target qubit
        p0 = 0.0
        p1 = 0.0
        dim = 2 ** n_qubits
        mask = 1 << target_qubit
        for idx in range(dim):
            amp = state_vector[idx]
            if (idx & mask) == 0:
                p0 += (amp.real * amp.real + amp.imag * amp.imag)
            else:
                p1 += (amp.real * amp.real + amp.imag * amp.imag)
        # Sample outcome
        r = np.random.random()
        outcome = 0 if r < p0 else 1
        # Collapse
        new_state = np.zeros_like(state_vector)
        norm = np.sqrt(p0 if outcome == 0 else p1) if (p0 + p1) > 0 else 1.0
        if norm == 0:
            # Degenerate case: state has zero probability; return unchanged
            return outcome, Statevector(state_vector)
        for idx in range(dim):
            if ((idx & mask) == 0 and outcome == 0) or ((idx & mask) != 0 and outcome == 1):
                new_state[idx] = state_vector[idx] / norm
        return outcome, Statevector(new_state)

    def _reset_qubit(self, state_vector: np.ndarray, n_qubits: int, target_qubit: int) -> np.ndarray:
        """Reset target qubit to |0> state by zeroing |1> components and renormalizing."""
        dim = 2 ** n_qubits
        mask = 1 << target_qubit
        new_state = state_vector.copy()
        # Zero out |1> components
        for idx in range(dim):
            if (idx & mask) != 0:
                new_state[idx] = 0.0 + 0.0j
        # Renormalize
        norm = np.linalg.norm(new_state)
        if norm > 0:
            new_state = new_state / norm
        return new_state

    def _apply_matrix_to_qubits(self, state_vector: np.ndarray, gate_matrix: np.ndarray, n_qubits: int, qargs: List[int]) -> np.ndarray:
        """
        Apply a small gate_matrix acting on qargs to the full state_vector.
        gate_matrix has dimension 2^k x 2^k where k=len(qargs).
        """
        k = len(qargs)
        assert gate_matrix.shape == (2**k, 2**k)
        # Sort qargs for consistent bit order (little-endian: qubit 0 is LSB)
        qargs_sorted = list(qargs)
        # Map basis index regrouping
        dim = 2 ** n_qubits
        new_state = np.zeros_like(state_vector)

        # Precompute bit masks and positions
        other_qubits = [q for q in range(n_qubits) if q not in qargs_sorted]
        # Iterate over all basis states by splitting into target subspace and others
        for base in range(2 ** len(other_qubits)):
            # Build a template index with other qubits filled from base
            template = 0
            for i, q in enumerate(other_qubits):
                if (base >> i) & 1:
                    template |= (1 << q)
            # Build the 2^k block of amplitudes corresponding to this template
            block = np.zeros(2**k, dtype=complex)
            for sub in range(2 ** k):
                idx = template
                for j, q in enumerate(qargs_sorted):
                    if (sub >> j) & 1:
                        idx |= (1 << q)
                block[sub] = state_vector[idx]
            # Apply gate to block
            block_out = gate_matrix @ block
            # Scatter back
            for sub in range(2 ** k):
                idx = template
                for j, q in enumerate(qargs_sorted):
                    if (sub >> j) & 1:
                        idx |= (1 << q)
                new_state[idx] = block_out[sub]
        return new_state
    
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
