"""
Pydantic schemas for API requests and responses.
Defines data models for quantum circuit simulation API.
"""

from pydantic import BaseModel, Field, validator, ConfigDict
from typing import List, Dict, Optional, Union, Any, Tuple
from enum import Enum

class PipelineType(str, Enum):
    """Available simulation pipeline types"""
    UNITARY = "unitary"
    EXACT_DENSITY = "exact_density"
    TRAJECTORY = "trajectory"

class SimulationRequest(BaseModel):
    """Request model for quantum circuit simulation"""
    qasm_code: str = Field(
        ..., 
        description="OpenQASM 2.0 code for the quantum circuit",
        min_length=10,
        max_length=100000
    )
    shots: int = Field(
        default=1024,
        description="Number of shots for trajectory-based simulation",
        ge=1,
        le=100000
    )
    pipeline_override: Optional[PipelineType] = Field(
        default=None,
        description="Force specific pipeline (overrides automatic routing)"
    )
    options: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional simulation options"
    )

    @validator('qasm_code')
    def validate_qasm_code(cls, v):
        """Basic QASM code validation"""
        if not v.strip():
            raise ValueError("QASM code cannot be empty")
        
        # Check for required QASM header
        if "OPENQASM" not in v:
            raise ValueError("QASM code must include OPENQASM declaration")
        
        return v.strip()

    @validator('shots')
    def validate_shots(cls, v):
        """Validate shot count is reasonable"""
        if v <= 0:
            raise ValueError("Shot count must be positive")
        if v > 100000:
            raise ValueError("Maximum 100,000 shots allowed")
        return v

class QubitState(BaseModel):
    """Quantum state information for a single qubit"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    id: int = Field(..., description="Qubit index/identifier")
    bloch_coords: Tuple[float, float, float] = Field(
        ..., 
        description="Bloch sphere coordinates [x, y, z]"
    )
    purity: float = Field(
        ..., 
        description="State purity (1.0 = pure, <1.0 = mixed)",
        ge=0.0,
        le=1.0
    )
    density_matrix: List[List[Union[complex, float]]] = Field(
        ..., 
        description="2x2 reduced density matrix"
    )
    label: str = Field(..., description="Human-readable qubit label")

    @validator('bloch_coords')
    def validate_bloch_coords(cls, v):
        """Validate Bloch coordinates are within unit sphere"""
        x, y, z = v
        magnitude = (x**2 + y**2 + z**2)**0.5
        if magnitude > 1.1:  # Allow small numerical errors
            raise ValueError(f"Bloch vector magnitude {magnitude} exceeds unit sphere")
        return v

    @validator('density_matrix')
    def validate_density_matrix(cls, v):
        """Basic density matrix validation"""
        if len(v) != 2 or any(len(row) != 2 for row in v):
            raise ValueError("Density matrix must be 2x2")
        
        # Check if trace is approximately 1
        trace = v[0][0] + v[1][1]
        if abs(trace.real - 1.0) > 1e-6:
            raise ValueError(f"Density matrix trace {trace.real} should be 1.0")
        
        return v

class SimulationResponse(BaseModel):
    """Response model for quantum circuit simulation"""
    qubits: List[QubitState] = Field(..., description="Quantum states for each qubit")
    pipeline_used: str = Field(..., description="Simulation pipeline that was used")
    execution_time: float = Field(..., description="Simulation execution time in seconds")
    shots_used: int = Field(..., description="Number of shots used in simulation")
    circuit_info: Dict[str, Any] = Field(..., description="Information about the simulated circuit")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional simulation metadata"
    )

class ErrorResponse(BaseModel):
    """Error response model"""
    error: Dict[str, Any] = Field(..., description="Error details")
    timestamp: str = Field(..., description="Error timestamp")
    request_id: Optional[str] = Field(None, description="Request identifier for tracking")

class WebSocketMessage(BaseModel):
    """WebSocket message model"""
    type: str = Field(..., description="Message type")
    data: Optional[Dict[str, Any]] = Field(None, description="Message payload")
    timestamp: Optional[str] = Field(None, description="Message timestamp")

class CircuitValidationInfo(BaseModel):
    """Circuit validation information"""
    is_valid: bool = Field(..., description="Whether circuit is valid")
    is_unitary: bool = Field(..., description="Whether circuit contains only unitary operations")
    num_qubits: int = Field(..., description="Number of qubits in circuit")
    num_operations: int = Field(..., description="Number of operations in circuit")
    supported_gates: List[str] = Field(..., description="List of supported gates found")
    unsupported_gates: List[str] = Field(
        default_factory=list,
        description="List of unsupported gates found"
    )
    errors: List[str] = Field(
        default_factory=list,
        description="List of validation errors"
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="List of validation warnings"
    )

class SimulationProgress(BaseModel):
    """Progress update for streaming simulations"""
    progress: float = Field(..., description="Progress percentage (0-100)", ge=0, le=100)
    stage: str = Field(..., description="Current simulation stage")
    message: str = Field(..., description="Progress message")
    estimated_completion: Optional[float] = Field(
        None, 
        description="Estimated completion time in seconds"
    )

class StepSnapshot(BaseModel):
    """Snapshot of quantum state at a specific step (stretch goal)"""
    step_index: int = Field(..., description="Step number in circuit execution")
    gate_applied: Optional[str] = Field(None, description="Gate that was just applied")
    qubits: List[QubitState] = Field(..., description="Quantum states after this step")
    timestamp: str = Field(..., description="Snapshot timestamp")

# WebSocket message types for type safety
class WSMessageType:
    """WebSocket message type constants"""
    # Client to server
    START_SIMULATION = "start_simulation"
    PAUSE_SIMULATION = "pause_simulation"
    RESUME_SIMULATION = "resume_simulation" 
    STOP_SIMULATION = "stop_simulation"
    STEP_FORWARD = "step_forward"
    STEP_BACKWARD = "step_backward"
    
    # Server to client
    SIMULATION_STARTED = "simulation_started"
    SIMULATION_PAUSED = "simulation_paused"
    SIMULATION_RESUMED = "simulation_resumed"
    SIMULATION_STOPPED = "simulation_stopped"
    SIMULATION_COMPLETE = "simulation_complete"
    SIMULATION_ERROR = "simulation_error"
    PROGRESS_UPDATE = "progress"
    STEP_SNAPSHOT = "step_snapshot"
    ERROR = "error"

# Additional utility models

class GateInfo(BaseModel):
    """Information about a quantum gate"""
    name: str = Field(..., description="Gate name")
    qubits: List[int] = Field(..., description="Target qubit indices")
    parameters: List[float] = Field(
        default_factory=list,
        description="Gate parameters (angles, etc.)"
    )
    is_unitary: bool = Field(..., description="Whether gate is unitary")

class CircuitAnalysis(BaseModel):
    """Detailed circuit analysis"""
    gates: List[GateInfo] = Field(..., description="List of gates in circuit")
    depth: int = Field(..., description="Circuit depth")
    total_gates: int = Field(..., description="Total number of gates")
    entangling_gates: int = Field(..., description="Number of entangling gates")
    estimated_complexity: str = Field(..., description="Complexity estimate (low/medium/high)")
    recommended_pipeline: PipelineType = Field(..., description="Recommended simulation pipeline")
