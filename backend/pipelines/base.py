"""
Base simulation pipeline interface.
Defines abstract base class for all quantum simulation pipelines as specified in dev_plane.md.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import time
import logging
import numpy as np

logger = logging.getLogger(__name__)

class SimulationPipeline(ABC):
    """
    Abstract base class for quantum simulation pipelines.
    
    All pipelines must implement the run() method and return standardized results.
    This design allows easy extension with new simulation methods.
    """
    
    def __init__(self, name: str = None):
        self.name = name or self.__class__.__name__
        self.logger = logging.getLogger(f"pipeline.{self.name}")
    
    @abstractmethod
    def run(self, circuit, shots: int = 1024) -> Dict[int, Dict[str, Any]]:
        """
        Run quantum simulation on the given circuit.
        
        Args:
            circuit: Qiskit QuantumCircuit object to simulate
            shots: Number of shots for statistical simulation (ignored for exact methods)
            
        Returns:
            Dictionary mapping qubit_id -> {
                'bloch': [x, y, z],  # Bloch sphere coordinates
                'purity': float,     # State purity (0-1)
                'rho': [[complex, complex], [complex, complex]]  # 2x2 density matrix
            }
            
        The return format also includes:
            'execution_time': float  # Time taken for simulation
        """
        pass
    
    def validate_circuit(self, circuit) -> bool:
        """
        Validate circuit is suitable for this pipeline.
        Can be overridden by specific pipelines.
        
        Args:
            circuit: QuantumCircuit to validate
            
        Returns:
            True if circuit can be simulated by this pipeline
        """
        try:
            # Basic validation
            if circuit.num_qubits <= 0:
                return False
            if circuit.num_qubits > 24:  # Global limit
                return False
            if len(circuit.data) == 0:
                return False
            return True
        except Exception as e:
            self.logger.error(f"Circuit validation failed: {e}")
            return False
    
    def preprocess_circuit(self, circuit):
        """
        Preprocess circuit before simulation (e.g., transpilation, optimization).
        Can be overridden by specific pipelines.
        
        Args:
            circuit: QuantumCircuit to preprocess
            
        Returns:
            Processed circuit
        """
        # Default: return circuit as-is
        return circuit
    
    def postprocess_results(self, raw_results: Dict[int, Dict[str, Any]], 
                          execution_time: float) -> Dict[int, Dict[str, Any]]:
        """
        Post-process simulation results for consistency.
        
        Args:
            raw_results: Raw results from simulation
            execution_time: Time taken for simulation
            
        Returns:
            Processed results with execution_time added
        """
        # Add execution time to results
        processed_results = raw_results.copy()
        processed_results['execution_time'] = execution_time
        
        # Validate all qubit results
        for qubit_id, data in processed_results.items():
            if qubit_id == 'execution_time':
                continue
                
            # Ensure required fields exist
            required_fields = ['bloch', 'purity', 'rho']
            for field in required_fields:
                if field not in data:
                    self.logger.warning(f"Missing {field} for qubit {qubit_id}")
                    
            # Validate purity is in [0, 1]
            if 'purity' in data:
                data['purity'] = np.clip(data['purity'], 0.0, 1.0)
                
            # Validate Bloch vector magnitude
            if 'bloch' in data:
                x, y, z = data['bloch']
                magnitude = np.sqrt(x*x + y*y + z*z)
                if magnitude > 1.1:  # Allow small numerical errors
                    self.logger.warning(f"Bloch vector magnitude {magnitude} > 1 for qubit {qubit_id}")
                    # Normalize if too large
                    if magnitude > 1.0:
                        data['bloch'] = [x/magnitude, y/magnitude, z/magnitude]
        
        return processed_results
    
    def estimate_resources(self, circuit) -> Dict[str, Any]:
        """
        Estimate computational resources needed for simulation.
        
        Args:
            circuit: QuantumCircuit to analyze
            
        Returns:
            Dictionary with resource estimates
        """
        n_qubits = circuit.num_qubits
        n_ops = len(circuit.data)
        
        return {
            'memory_mb': self._estimate_memory(n_qubits),
            'time_seconds': self._estimate_time(n_qubits, n_ops),
            'complexity': self._classify_complexity(n_qubits, n_ops)
        }
    
    def _estimate_memory(self, n_qubits: int) -> float:
        """Estimate memory usage in MB"""
        # Override in specific pipelines
        return 0.0
    
    def _estimate_time(self, n_qubits: int, n_ops: int) -> float:
        """Estimate execution time in seconds"""
        # Override in specific pipelines
        return 0.0
    
    def _classify_complexity(self, n_qubits: int, n_ops: int) -> str:
        """Classify simulation complexity"""
        if n_qubits <= 10 and n_ops <= 50:
            return "low"
        elif n_qubits <= 20 and n_ops <= 200:
            return "medium"
        else:
            return "high"
    
    def log_simulation_start(self, circuit, shots: int):
        """Log simulation start with circuit info"""
        self.logger.info(f"Starting {self.name} simulation: {circuit.num_qubits} qubits, "
                        f"{len(circuit.data)} ops, {shots} shots")
    
    def log_simulation_end(self, execution_time: float, num_qubits: int):
        """Log simulation completion"""
        self.logger.info(f"Completed {self.name} simulation: {num_qubits} qubits "
                        f"in {execution_time:.3f}s")

class SimulationError(Exception):
    """Custom exception for simulation errors"""
    def __init__(self, message: str, pipeline: str = None, circuit_info: Dict = None):
        self.message = message
        self.pipeline = pipeline
        self.circuit_info = circuit_info or {}
        super().__init__(self.message)

class UnsupportedCircuitError(SimulationError):
    """Exception for circuits that cannot be simulated by a pipeline"""
    pass

class ResourceLimitError(SimulationError):
    """Exception for circuits that exceed resource limits"""
    pass
