"""
Quantum State Visualizer Backend

FastAPI-based backend for quantum circuit simulation and Bloch sphere visualization.
Implements the architecture specified in dev_plane.md with modular simulation pipelines.
"""

__version__ = "1.0.0"
__author__ = "Quantum State Visualizer Team"

from .main import app
from . import schemas, utils, pipelines

__all__ = [
    'app',
    'schemas', 
    'utils',
    'pipelines'
]
