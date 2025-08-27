# Optimization Overview

This document explains the current simulation optimization strategy for the Quantum State Visualizer, why we chose it, and the trade-offs involved.

## Goals

- Keep simulations fast and memory-safe on typical developer machines.
- Preserve exactness where practical (unitary and small mixed-state circuits).
- Provide scalable approximations when exact methods become impractical.

## Routing Policy (Current)

- Unitary circuits: up to 20 qubits → Unitary (statevector) pipeline.
- Non-unitary circuits (measure/reset/noise):
  - 1–8 qubits → Exact Density pipeline (exact mixed-state evolution).
  - 9–16 qubits → Trajectory pipeline (Monte Carlo sampling).
  - >16 qubits → Trajectory (may exceed resource limits depending on circuit).

Why: density matrices scale as 4^n in memory/time. At 9+ qubits, exact density grows prohibitively large for typical environments.

## Unitary Pipeline (Fast Exact)

Technique:
- Simulate the full statevector exactly.
- Compute each qubit’s reduced density matrix (RDM) from |ψ⟩ using a fast reshape + matrix multiply instead of nested 4^n loops:
  - Reshape |ψ⟩ to isolate the target qubit axis, then compute ρ = Ψ · Ψᴴ (2×M by its conjugate transpose), which is O(2^n).
- Derive Bloch vector and purity from the 2×2 RDM.

Benefits:
- Exact results for unitary circuits.
- Avoids constructing a 2^n × 2^n full density matrix.
- Scales to the global cap (24 qubits) on capable machines.

Downsides:
- Still exponential in 2^n; very large n can hit memory/time limits.
- Careful axis permutations and reshapes are required to avoid overhead.

### Detailed optimization design

Goal:
- Input: statevector ψ ∈ C^{2^n} (complex128), n = number of qubits.
- Output per qubit i:
  - ρ_i ∈ C^{2×2}, Bloch r_i = (x,y,z), purity p_i = Tr(ρ_i^2).

Core idea (reshape + GEMM):
- View ψ as a 2×(2^{n−1}) matrix where rows correspond to the target qubit’s basis and columns to the rest.
- Then ρ_i = Ψ_i · Ψ_i^†, a 2×2 Hermitian matrix from a single small matrix multiply.

Algorithm for qubit i (0-based, little-endian):
1) Let shape = (2,)*n. Form a view V with the target axis first:
  - V = ψ.reshape(shape).transpose((i,) + tuple(j for j in range(n) if j != i))
  - V2 = V.reshape(2, -1)  # shape (2, 2^{n−1})
2) Compute reduced density: ρ = V2 @ V2.conj().T  # (2×M)·(M×2) → 2×2
3) Bloch vector from ρ:
  - rx = 2·Re(ρ01), ry = −2·Im(ρ01), rz = Re(ρ00 − ρ11)
4) Purity: p = Tr(ρ·ρ)

Complexity:
- Time: O(n · 2^n) total across all qubits (each qubit does a 2×(2^{n−1})×2 GEMM and a transpose/view).
- Memory: O(2^n) for state + small temporaries; avoids any 4^n allocations.

Implementation notes:
- Prefer views over copies. NumPy’s transpose returns a view; reshape may copy if non-contiguous. If copying happens frequently, consider np.ascontiguousarray(V) once per qubit.
- Use complex128 throughout to minimize numerical drift; clip tiny values (|val| ≤ 1e−12 → 0) when serializing.
- Preallocate 2×2 arrays for ρ to reduce allocator churn, or reuse buffers.
- BLAS backend (MKL/OpenBLAS) will multi-thread the GEMMs; avoid over-parallelizing at Python level unless measured.
- Endianness: current code treats qubit 0 as LSB in basis index (consistent with bit-shift usage elsewhere). Keep consistent across pipelines and UI.

Optional enhancements:
- Parallelize per-qubit RDM computation for n ≥ 12 using a thread pool; tune workers to avoid fighting BLAS threads.
- Skip ρ and compute Bloch directly via V2 row inner-products (equivalent numerically), reconstruct ρ from r if only needed for UI: ρ = (I + r·σ)/2.
- Light transpilation before simulation (remove barriers, fuse adjacent single-qubit gates) to reduce ops in state evolution.

Edge cases:
- n = 1: V2 is already 2×1; algorithm reduces to trivial ρ.
- Nearly pure numerical noise: enforce Hermiticity with (ρ+ρ^†)/2 and renormalize trace to 1 within tolerance.
- Very large n (≥23): statevector memory (2^n · 16 bytes) becomes the limiting factor irrespective of the RDM method.

## Exact Density Pipeline (Exact Mixed States)

Technique:
- Build the full density matrix exactly and compute single-qubit RDMs via partial trace.

Benefits:
- Exact treatment of measurements, resets, and noise.
- Deterministic results; no sampling error.

Why the 8-qubit cap:
- Density matrix memory grows as 4^n; at 9 qubits, it is 512×512 complex (~4 MB) per array but operations and intermediates quickly multiply usage; real circuits trigger multiple such operations. The 8-qubit cap is a practical safety margin to stay fast and stable across environments.

Downsides:
- 4^n scaling becomes prohibitive beyond 8–9 qubits for many users.

## Trajectory Pipeline (Monte Carlo Approximation)

Technique:
- Run many 1-shot stochastic trajectories with explicit projective collapses on measurement.
- Average single-qubit RDMs across trajectories to estimate the ensemble state.

Benefits:
- Scales much better for larger non-unitary circuits than exact density.
- Naturally models conditional logic from measurements.

Downsides:
- Statistical error: accuracy depends on number of shots.
- Non-deterministic results; repeated runs vary slightly.
- Rare branches may need many shots to converge.
- Runtime scales with shots × circuit cost.

Recommended usage:
- Start with 1k–4k shots; increase shots for tighter error bars.

## Why This Mix Works

- Exact where it is cheap and impactful (unitary; small mixed states).
- Approximate where exactness is too expensive (larger mixed states).
- Clean routing thresholds keep UX predictable while protecting performance.

## Potential Improvements

- Unitary
  - Use reshape + einsum/GEMM for all RDMs (avoid any 4^n intermediates).
  - Light transpilation: remove barriers, fuse adjacent 1-qubit gates.
  - Optional Numba JIT for hot loops; thread pool for per-qubit RDMs at large n.

- Trajectory
  - Batch multiple trajectories per worker; parallelize across cores.
  - Precompute bit masks/index tables for faster measurement collapse.
  - Adaptive shots: stop early when confidence intervals are tight enough.

- Exact Density
  - Early gate simplifications and measurement commuting to reduce work.
  - Switch to trajectory automatically when projected memory/time exceeds a budget.

## Trade-offs Summary

- Exact Density (≤8 qubits): exact but steep 4^n growth; safest for correctness.
- Trajectory (≥9 non-unitary): scalable but introduces sampling error and variance.
- Unitary (≤20): exact, efficient with fast RDM, but still exponential in 2^n.

## Configurability (Future)

- Expose thresholds (unitary_qubit_cap, exact_density_qubit_cap) via env or settings.
- Allow users to force pipelines via API override when they know their hardware limits.

## Validation

- Golden tests on Bell, GHZ, and known single-qubit states.
- Property tests: trace(ρ)=1, Hermitian, positive semidefinite.
- Compare trajectory averages vs exact density on small circuits to calibrate default shots.
