"""
Simulation pipelines package for Quantum State Visualizer.

This package implements the modular simulation architecture specified in dev_plane.md:
- Base pipeline interface for extensibility
- UnitaryPipeline: Statevector simulation for pure states  
- ExactDensityPipeline: Full density matrix evolution
- TrajectoryPipeline: Monte Carlo sampling for measurements

All pipelines follow the same interface and return standardized results.
"""

from .base import SimulationPipeline, SimulationError, UnsupportedCircuitError, ResourceLimitError
from .unitary import UnitaryPipeline
from .exact_density import ExactDensityPipeline
from .trajectory import TrajectoryPipeline

__all__ = [
    'SimulationPipeline',
    'SimulationError', 
    'UnsupportedCircuitError',
    'ResourceLimitError',
    'UnitaryPipeline',
    'ExactDensityPipeline', 
    'TrajectoryPipeline'
]

# Pipeline registry for dynamic loading
AVAILABLE_PIPELINES = {
    'unitary': UnitaryPipeline,
    'exact_density': ExactDensityPipeline,
    'trajectory': TrajectoryPipeline
}

def create_pipeline(pipeline_name: str) -> SimulationPipeline:
    """
    Factory function to create pipeline instances.
    
    Args:
        pipeline_name: Name of pipeline to create
        
    Returns:
        Initialized pipeline instance
        
    Raises:
        ValueError: If pipeline name is not recognized
    """
    if pipeline_name not in AVAILABLE_PIPELINES:
        raise ValueError(f"Unknown pipeline: {pipeline_name}. Available: {list(AVAILABLE_PIPELINES.keys())}")
    
    pipeline_class = AVAILABLE_PIPELINES[pipeline_name]
    return pipeline_class()

def list_available_pipelines() -> list:
    """Return list of available pipeline names"""
    return list(AVAILABLE_PIPELINES.keys())

def get_pipeline_info() -> dict:
    """
    Get information about all available pipelines.
    
    Returns:
        Dictionary with pipeline capabilities and limits
    """
    info = {}
    
    for name, pipeline_class in AVAILABLE_PIPELINES.items():
        try:
            pipeline = pipeline_class()
            info[name] = {
                'name': pipeline.name,
                'max_qubits': getattr(pipeline, 'max_qubits', None),
                'supports_measurements': getattr(pipeline, 'supports_measurements', lambda: False)(),
                'supports_noise': getattr(pipeline, 'supports_noise', lambda: False)(),
                'description': pipeline.__class__.__doc__.split('\n')[1].strip() if pipeline.__class__.__doc__ else ""
            }
        except Exception as e:
            info[name] = {'error': str(e)}
    
    return info
