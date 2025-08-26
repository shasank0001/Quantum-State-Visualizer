"""
Quantum State Visualizer Backend

FastAPI application for quantum circuit simulation and Bloch sphere visualization.
Implements the architecture specified in dev_plane.md with modular simulation pipelines.
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Union, Any
import asyncio
import json
import logging
from datetime import datetime
import os
from dotenv import load_dotenv

from schemas import (
    SimulationRequest,
    SimulationResponse,
    QubitState,
    WebSocketMessage,
    ErrorResponse
)
from utils import parse_and_validate_circuit, route_circuit
from pipelines.base import SimulationPipeline
from pipelines.unitary import UnitaryPipeline
from pipelines.exact_density import ExactDensityPipeline
from pipelines.trajectory import TrajectoryPipeline

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Quantum State Visualizer API",
    description="Backend API for quantum circuit simulation and Bloch sphere visualization",
    version="1.0.0",
)

# Add CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://localhost:8080"],  # Vite and React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize simulation pipelines
PIPELINES: Dict[str, SimulationPipeline] = {
    "unitary": UnitaryPipeline(),
    "exact_density": ExactDensityPipeline(),
    "trajectory": TrajectoryPipeline(),
}

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.simulation_tasks: Dict[str, asyncio.Task] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"Client {client_id} connected")

    def disconnect(self, websocket: WebSocket, client_id: str):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if client_id in self.simulation_tasks:
            self.simulation_tasks[client_id].cancel()
            del self.simulation_tasks[client_id]
        logger.info(f"Client {client_id} disconnected")

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        await websocket.send_json(message)

    async def broadcast_message(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                # Connection might be closed, remove it
                self.active_connections.remove(connection)

manager = ConnectionManager()

# Load .env if present
load_dotenv()

# Optional Gemini client (loaded lazily)
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
print(GOOGLE_API_KEY)
try:
    import google.generativeai as genai  # type: ignore
    _HAS_GEMINI = True
except Exception:
    _HAS_GEMINI = False

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Quantum State Visualizer API",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat(),
        "available_pipelines": list(PIPELINES.keys())
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "pipelines": {name: "available" for name in PIPELINES.keys()},
        "timestamp": datetime.utcnow().isoformat(),
        "chat": {
            "provider": "google-gemini",
            "model": GEMINI_MODEL,
            "configured": bool(GOOGLE_API_KEY) and _HAS_GEMINI,
        },
    }


class ChatRequest(BaseModel):
    messages: List[Dict[str, str]] = Field(
        description="Chat history as a list of {role, content} messages (roles: user|assistant)")
    system: Optional[str] = Field(default="You are a concise assistant for a quantum circuits visualizer app.")


class ChatResponse(BaseModel):
    reply: str
    model: str = GEMINI_MODEL


@app.post("/chat/completions", response_model=ChatResponse)
async def chat_completions(payload: ChatRequest):
    """Lightweight chat endpoint backed by Gemini 2.5 Flash.
    Requires GOOGLE_API_KEY env and google-generativeai package.
    """
    if not _HAS_GEMINI or not GOOGLE_API_KEY:
        raise HTTPException(status_code=501, detail="Chat is not configured on server")

    try:
        genai.configure(api_key=GOOGLE_API_KEY)
        model = genai.GenerativeModel(GEMINI_MODEL, system_instruction=payload.system)
        # Convert messages to the expected format
        history = []
        for m in payload.messages:
            role = m.get("role", "user")
            content = m.get("content", "")
            if role == "assistant":
                history.append({"role": "model", "parts": [content]})
            else:
                history.append({"role": "user", "parts": [content]})

        chat = model.start_chat(history=history)
        result = await asyncio.get_event_loop().run_in_executor(None, chat.send_message, payload.messages[-1]["content"] if payload.messages else "Hello")
        text = getattr(result, "text", None) or (result.candidates[0].content.parts[0].text if getattr(result, "candidates", None) else "")
        if not text:
            text = "(No response)"
        return ChatResponse(reply=text)
    except HTTPException:
        raise
    except Exception as e:
        # Map common Google API errors to HTTP responses
        try:
            from google.api_core.exceptions import ResourceExhausted, PermissionDenied, InvalidArgument  # type: ignore
            if isinstance(e, ResourceExhausted):
                raise HTTPException(status_code=429, detail="Gemini API quota/rate limit exceeded. Please wait and retry or adjust quota.")
            if isinstance(e, PermissionDenied):
                raise HTTPException(status_code=403, detail="Gemini API access denied. Check API key or project permissions.")
            if isinstance(e, InvalidArgument):
                raise HTTPException(status_code=400, detail="Invalid request to Gemini API. Check model name or payload.")
        except Exception:
            pass
        logger.exception("Chat error")
        raise HTTPException(status_code=500, detail=f"Chat backend error: {str(e)}")

@app.post("/simulate", response_model=SimulationResponse)
async def simulate_circuit(request: SimulationRequest):
    """
    Main simulation endpoint for quantum circuits.
    Parses QASM, validates, routes to appropriate pipeline, and returns results.
    """
    try:
        logger.info(f"Received simulation request with {len(request.qasm_code)} chars of QASM")
        
        # Parse and validate circuit
        circuit, validation_info = parse_and_validate_circuit(request.qasm_code)
        
        if not validation_info["is_valid"]:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid circuit: {validation_info['errors']}"
            )
        
        # Route to appropriate pipeline
        pipeline_name = route_circuit(
            circuit=circuit,
            shots=request.shots,
            force_pipeline=request.pipeline_override
        )
        
        logger.info(f"Routed to {pipeline_name} pipeline for circuit with {circuit.num_qubits} qubits, unitary={validation_info['is_unitary']}")
        
        if pipeline_name not in PIPELINES:
            raise HTTPException(
                status_code=500,
                detail=f"Pipeline {pipeline_name} not available"
            )
        
        # Run simulation
        pipeline = PIPELINES[pipeline_name]
        
        # Apply security limits
        if circuit.num_qubits > 24:
            raise HTTPException(
                status_code=400,
                detail="Maximum 24 qubits supported"
            )
        
        if len(circuit.data) > 1000:
            raise HTTPException(
                status_code=400,
                detail="Maximum 1000 operations supported"
            )
        
        if request.shots > 100000:
            raise HTTPException(
                status_code=400,
                detail="Maximum 100,000 shots supported"
            )
        
        # Run simulation with timeout
        try:
            async with asyncio.timeout(300):  # 5 minute timeout
                results = await asyncio.get_event_loop().run_in_executor(
                    None, pipeline.run, circuit, request.shots
                )
        except asyncio.TimeoutError:
            raise HTTPException(
                status_code=408,
                detail="Simulation timeout after 5 minutes"
            )
        except Exception as pipeline_error:
            # If the selected pipeline fails, try to fallback to exact_density
            if pipeline_name != 'exact_density' and 'not suitable' in str(pipeline_error).lower():
                logger.warning(f"{pipeline_name} pipeline failed: {pipeline_error}. Falling back to exact_density pipeline.")
                try:
                    fallback_pipeline = PIPELINES['exact_density']
                    results = await asyncio.get_event_loop().run_in_executor(
                        None, fallback_pipeline.run, circuit, request.shots
                    )
                    pipeline_name = 'exact_density'  # Update for response
                except Exception as fallback_error:
                    logger.error(f"Fallback pipeline also failed: {fallback_error}")
                    raise HTTPException(
                        status_code=500,
                        detail=f"Both {pipeline_name} and exact_density pipelines failed: {str(fallback_error)}"
                    )
            else:
                raise HTTPException(
                    status_code=500,
                    detail=f"Pipeline {pipeline_name} simulation failed: {str(pipeline_error)}"
                )
        
        # Format results
        qubit_states = []
        execution_time = results.get("execution_time", 0.0)
        
        for qubit_id, data in results.items():
            # Skip metadata entries
            if not isinstance(qubit_id, int) or not isinstance(data, dict):
                continue
                
            qubit_state = QubitState(
                id=qubit_id,
                bloch_coords=data["bloch"],
                purity=data["purity"],
                density_matrix=data["rho"],
                label=f"Q{qubit_id}"
            )
            qubit_states.append(qubit_state)
        
        response = SimulationResponse(
            qubits=qubit_states,
            pipeline_used=pipeline_name,
            execution_time=execution_time,
            shots_used=request.shots,
            circuit_info={
                "num_qubits": circuit.num_qubits,
                "num_operations": len(circuit.data),
                "is_unitary": validation_info["is_unitary"],
                "supported_gates": validation_info["supported_gates"]
            }
        )
        
        logger.info(f"Simulation completed successfully with {len(qubit_states)} qubits")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Simulation error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal simulation error: {str(e)}"
        )

@app.websocket("/ws/simulate")
async def websocket_simulate(websocket: WebSocket):
    """
    WebSocket endpoint for real-time simulation streaming.
    Supports step-by-step execution and progress updates.
    """
    client_id = f"client_{datetime.utcnow().timestamp()}"
    await manager.connect(websocket, client_id)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            logger.info(f"WebSocket received: {message.get('type', 'unknown')}")
            
            if message["type"] == "start_simulation":
                # Start streaming simulation
                await handle_streaming_simulation(
                    websocket=websocket,
                    client_id=client_id,
                    request_data=message["data"]
                )
            
            elif message["type"] == "pause_simulation":
                # Pause current simulation
                if client_id in manager.simulation_tasks:
                    manager.simulation_tasks[client_id].cancel()
                    await websocket.send_json({
                        "type": "simulation_paused",
                        "message": "Simulation paused by user"
                    })
            
            elif message["type"] == "resume_simulation":
                # Resume simulation (placeholder for stretch goal)
                await websocket.send_json({
                    "type": "simulation_resumed",
                    "message": "Resume functionality not yet implemented"
                })
            
            elif message["type"] == "step_forward":
                # Step-by-step execution (placeholder for stretch goal)
                await websocket.send_json({
                    "type": "step_completed",
                    "message": "Step-by-step execution not yet implemented"
                })
            
            else:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Unknown message type: {message.get('type', 'none')}"
                })
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, client_id)
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        await websocket.send_json({
            "type": "error",
            "message": f"Server error: {str(e)}"
        })
        manager.disconnect(websocket, client_id)

async def handle_streaming_simulation(websocket: WebSocket, client_id: str, request_data: dict):
    """Handle streaming simulation with progress updates"""
    try:
        # Parse request similar to REST endpoint
        qasm_code = request_data.get("qasm_code", "")
        shots = request_data.get("shots", 1024)
        
        circuit, validation_info = parse_and_validate_circuit(qasm_code)
        
        if not validation_info["is_valid"]:
            await websocket.send_json({
                "type": "error",
                "message": f"Invalid circuit: {validation_info['errors']}"
            })
            return
        
        pipeline_name = route_circuit(circuit, shots)
        pipeline = PIPELINES[pipeline_name]
        
        # Send start confirmation
        await websocket.send_json({
            "type": "simulation_started",
            "pipeline": pipeline_name,
            "circuit_info": {
                "num_qubits": circuit.num_qubits,
                "num_operations": len(circuit.data)
            }
        })
        
        # Create and store simulation task
        task = asyncio.create_task(
            run_streaming_simulation(websocket, pipeline, circuit, shots)
        )
        manager.simulation_tasks[client_id] = task
        
        # Await completion
        await task
        
    except asyncio.CancelledError:
        await websocket.send_json({
            "type": "simulation_cancelled",
            "message": "Simulation was cancelled"
        })
    except Exception as e:
        await websocket.send_json({
            "type": "error", 
            "message": f"Streaming simulation error: {str(e)}"
        })

async def run_streaming_simulation(websocket: WebSocket, pipeline: SimulationPipeline, circuit, shots: int):
    """Run simulation with progress streaming"""
    try:
        # Send progress updates
        for progress in range(0, 101, 20):
            await websocket.send_json({
                "type": "progress",
                "progress": progress,
                "message": f"Simulation {progress}% complete"
            })
            await asyncio.sleep(0.5)  # Simulate work
        
        # Run actual simulation
        results = await asyncio.get_event_loop().run_in_executor(
            None, pipeline.run, circuit, shots
        )
        
        # Send final results
        qubit_states = []
        for qubit_id, data in results.items():
            qubit_state = {
                "id": qubit_id,
                "bloch_coords": data["bloch"],
                "purity": data["purity"],
                "density_matrix": data["rho"],
                "label": f"Q{qubit_id}"
            }
            qubit_states.append(qubit_state)
        
        await websocket.send_json({
            "type": "simulation_complete",
            "qubits": qubit_states,
            "execution_time": results.get("execution_time", 0.0)
        })
        
    except asyncio.CancelledError:
        raise
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "message": f"Simulation error: {str(e)}"
        })

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler"""
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "status_code": exc.status_code,
                "detail": exc.detail,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
