import { useRef, useState, useEffect } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Text, Line } from '@react-three/drei';
import * as THREE from 'three';
import { QubitState } from '@/store/quantumStore';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Card } from '@/components/ui/card';
import { Slider } from '@/components/ui/slider';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { X, RotateCcw, Info } from 'lucide-react';

interface ExpandedQubitViewProps {
  qubit: QubitState;
  isOpen: boolean;
  onClose: () => void;
}

function VectorArrow({ start, end, color, lineWidth }: { 
  start: [number, number, number]; 
  end: [number, number, number]; 
  color: string; 
  lineWidth: number; 
}) {
  const arrowRef = useRef<THREE.Group>(null);
  
  useEffect(() => {
    if (!arrowRef.current) return;
    
    const [sx, sy, sz] = start;
    const [ex, ey, ez] = end;
    
    // Calculate direction vector
    const direction = new THREE.Vector3(ex - sx, ey - sy, ez - sz);
    const length = direction.length();
    
    if (length > 0) {
      // Create a quaternion for rotation
      const up = new THREE.Vector3(0, 1, 0); // Default cone points up
      const quaternion = new THREE.Quaternion();
      quaternion.setFromUnitVectors(up, direction.clone().normalize());
      
      // Apply rotation to the arrow
      arrowRef.current.setRotationFromQuaternion(quaternion);
      arrowRef.current.position.set(ex, ey, ez);
    }
  }, [start, end]);
  
  const [sx, sy, sz] = start;
  const [ex, ey, ez] = end;
  const direction = new THREE.Vector3(ex - sx, ey - sy, ez - sz);
  const length = direction.length();
  
  if (length === 0) return null;
  
  // Calculate where the line should end (at the base of the cone)
  const coneHeight = 0.15;
  const normalizedDir = direction.clone().normalize();
  const lineEndX = ex - normalizedDir.x * coneHeight * 0.5;
  const lineEndY = ey - normalizedDir.y * coneHeight * 0.5;
  const lineEndZ = ez - normalizedDir.z * coneHeight * 0.5;
  
  return (
    <>
      {/* Vector line - ends at cone base */}
      <Line
        points={[[sx, sy, sz], [lineEndX, lineEndY, lineEndZ]]}
        color={color}
        lineWidth={lineWidth}
        transparent
        opacity={1.0}
        renderOrder={999}
      />
      
      {/* Arrow head */}
      <group ref={arrowRef} renderOrder={1000}>
        <mesh>
          <coneGeometry args={[0.06, coneHeight, 12]} />
          <meshBasicMaterial 
            color={color}
            transparent
            opacity={1.0}
            depthTest={false}
            depthWrite={false}
          />
        </mesh>
      </group>
    </>
  );
}

interface InteractiveBlochSphereProps {
  qubit: QubitState;
  showPhase: boolean;
  showState: boolean;
}

export const ExpandedQubitView = ({ qubit, isOpen, onClose }: ExpandedQubitViewProps) => {
  const [animationSpeed, setAnimationSpeed] = useState(1);
  const [showPhaseAngle, setShowPhaseAngle] = useState(true);
  const [showState, setShowState] = useState(true);
  const [precision, setPrecision] = useState(4);

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl w-full h-[90vh] p-0 bg-background border border-border">
        <DialogHeader className="p-6 border-b border-border bg-gradient-quantum-subtle">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <DialogTitle className="text-2xl font-bold text-foreground">
                Q-sphere: {qubit.label}
              </DialogTitle>
              <Badge variant="outline" className="border-quantum-primary text-quantum-primary">
                P = {qubit.bloch.purity.toFixed(precision)}
              </Badge>
              <Badge variant="outline" className="border-quantum-secondary text-quantum-secondary">
                Interactive
              </Badge>
            </div>
            <Button variant="ghost" size="sm" onClick={onClose}>
              <X className="w-4 h-4" />
            </Button>
          </div>
        </DialogHeader>

        <div className="flex flex-1 h-full">
          {/* Main 3D View */}
          <div className="flex-1 relative">
            <div className="absolute inset-0">
              <Canvas
                camera={{ position: [4, 4, 4], fov: 45 }}
                dpr={[1, 2]}
                performance={{ min: 0.5 }}
              >
                <InteractiveBlochSphere 
                  qubit={qubit} 
                  showPhase={showPhaseAngle}
                  showState={showState}
                />
                <OrbitControls 
                  enableZoom={true} 
                  enablePan={true}
                  enableRotate={true}
                  minDistance={2}
                  maxDistance={8}
                />
              </Canvas>
            </div>

            {/* Overlay Controls */}
            <div className="absolute top-4 left-4 flex flex-col gap-2">
              <Card className="p-2 bg-background/80 backdrop-blur-sm">
                <div className="flex items-center gap-2 text-sm">
                  <RotateCcw className="w-4 h-4" />
                  <span>Drag to rotate • Scroll to zoom</span>
                </div>
              </Card>
            </div>

            {/* State Coordinates Display */}
            <div className="absolute bottom-4 left-4">
              <Card className="p-4 bg-background/90 backdrop-blur-sm">
                <div className="text-sm font-semibold text-foreground mb-2">State Vector</div>
                <div className="grid grid-cols-3 gap-4 mono-scientific">
                  <div className="text-center">
                    <div className="text-xs text-muted-foreground mb-1">X</div>
                    <div className="text-lg font-bold text-quantum-primary">
                      {qubit.bloch.x.toFixed(precision)}
                    </div>
                  </div>
                  <div className="text-center">
                    <div className="text-xs text-muted-foreground mb-1">Y</div>
                    <div className="text-lg font-bold text-quantum-secondary">
                      {qubit.bloch.y.toFixed(precision)}
                    </div>
                  </div>
                  <div className="text-center">
                    <div className="text-xs text-muted-foreground mb-1">Z</div>
                    <div className="text-lg font-bold text-quantum-accent">
                      {qubit.bloch.z.toFixed(precision)}
                    </div>
                  </div>
                </div>
              </Card>
            </div>
          </div>

          {/* Side Panel */}
          <div className="w-80 bg-gradient-quantum-subtle border-l border-border p-6 overflow-y-auto">
            {/* Speed Control */}
            <Card className="p-4 mb-6">
              <div className="flex items-center justify-between mb-3">
                <Label className="text-sm font-semibold">Speed</Label>
                <Badge variant="outline">{animationSpeed.toFixed(1)}x</Badge>
              </div>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-muted-foreground">Animation:</span>
                  <span className="text-xs font-medium">{animationSpeed.toFixed(1)}x</span>
                </div>
                <Slider
                  value={[animationSpeed]}
                  onValueChange={([value]) => setAnimationSpeed(value)}
                  min={0}
                  max={3}
                  step={0.1}
                  className="w-full"
                />
              </div>
            </Card>

            {/* Precision Control */}
            <Card className="p-4 mb-6">
              <div className="flex items-center justify-between mb-3">
                <Label className="text-sm font-semibold">Precision</Label>
                <Badge variant="outline">High</Badge>
              </div>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-muted-foreground">Accuracy:</span>
                  <span className="text-xs font-medium">±1e-{precision}</span>
                </div>
                <Slider
                  value={[precision]}
                  onValueChange={([value]) => setPrecision(value)}
                  min={2}
                  max={8}
                  step={1}
                  className="w-full"
                />
              </div>
            </Card>

            {/* Display Options */}
            <Card className="p-4 mb-6">
              <div className="flex items-center gap-2 mb-4">
                <Info className="w-4 h-4" />
                <Label className="text-sm font-semibold">Display</Label>
              </div>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <Label htmlFor="show-phase" className="text-sm">Phase angle</Label>
                  <Switch
                    id="show-phase"
                    checked={showPhaseAngle}
                    onCheckedChange={setShowPhaseAngle}
                  />
                </div>
                <div className="flex items-center justify-between">
                  <Label htmlFor="show-state" className="text-sm">State</Label>
                  <Switch
                    id="show-state"
                    checked={showState}
                    onCheckedChange={setShowState}
                  />
                </div>
              </div>
            </Card>

            {/* System Info */}
            <Card className="p-4 mb-6">
              <div className="flex items-center gap-2 mb-4">
                <Label className="text-sm font-semibold">System</Label>
              </div>
              <div className="space-y-3 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Status:</span>
                  <Badge variant="outline" className="text-quantum-success border-quantum-success">
                    COMPLETED
                  </Badge>
                </div>
                <Separator />
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Memory:</span>
                  <span className="font-medium">8 states</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Accuracy:</span>
                  <span className="font-medium">±1e-{precision}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Qubits:</span>
                  <span className="font-medium">3</span>
                </div>
              </div>
            </Card>

            {/* Density Matrix */}
            <Card className="p-4">
              <Label className="text-sm font-semibold mb-3 block">Density Matrix</Label>
              <div className="mono-scientific text-xs space-y-2">
                <div className="grid grid-cols-2 gap-2">
                  <div className="p-2 bg-background rounded border">
                    {formatComplex(qubit.rho[0][0])}
                  </div>
                  <div className="p-2 bg-background rounded border">
                    {formatComplex(qubit.rho[0][1])}
                  </div>
                  <div className="p-2 bg-background rounded border">
                    {formatComplex(qubit.rho[1][0])}
                  </div>
                  <div className="p-2 bg-background rounded border">
                    {formatComplex(qubit.rho[1][1])}
                  </div>
                </div>
              </div>
            </Card>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

function InteractiveBlochSphere({ qubit, showPhase, showState }: InteractiveBlochSphereProps) {
  const meshRef = useRef<THREE.Group>(null);
  const vectorRef = useRef<THREE.Group>(null);
  
  // Calculate vector length as magnitude of Bloch vector
  const vectorLength = Math.min(1.0, Math.sqrt(
    qubit.bloch.x * qubit.bloch.x + 
    qubit.bloch.y * qubit.bloch.y + 
    qubit.bloch.z * qubit.bloch.z
  ));
  const vectorOpacity = Math.max(0.8, qubit.bloch.purity);
  
  // Animate sphere rotation
  useFrame((state) => {
    if (meshRef.current) {
      meshRef.current.rotation.y = state.clock.elapsedTime * 0.05;
    }
  });
  
  return (
    <group ref={meshRef}>
      {/* Enhanced lighting */}
      <ambientLight intensity={0.6} />
      <pointLight position={[10, 10, 10]} intensity={1.2} />
      <pointLight position={[-5, -5, -5]} intensity={0.3} color="#4444ff" />
      
      {/* Main Bloch sphere */}
      <mesh>
        <sphereGeometry args={[1, 64, 32]} />
        <meshPhongMaterial 
          color="#0a0a1a"
          transparent 
          opacity={0.08}
          wireframe={false}
          depthWrite={false}
        />
      </mesh>
      
      {/* Enhanced wireframe sphere */}
      <mesh>
        <sphereGeometry args={[1.005, 32, 16]} />
        <meshBasicMaterial 
          color="#00bfff"
          wireframe 
          transparent 
          opacity={0.3}
          depthWrite={false}
        />
      </mesh>
      
      {/* Equatorial circles */}
      {Array.from({ length: 8 }, (_, i) => {
        const angle = (i / 8) * Math.PI;
        return (
          <group key={i} rotation={[0, 0, angle]} renderOrder={-1}>
            <mesh rotation={[Math.PI / 2, 0, 0]}>
              <ringGeometry args={[0.98, 1.02, 32]} />
              <meshBasicMaterial 
                color="#334466"
                transparent 
                opacity={0.15}
                depthWrite={false}
              />
            </mesh>
          </group>
        );
      })}
      
      {/* Coordinate axes with enhanced styling - corrected orientation */}
      <Line
        points={[[-1.2, 0, 0], [1.2, 0, 0]] as [number, number, number][]}
        color="#ff6666"
        lineWidth={4}
        transparent
        opacity={0.9}
        renderOrder={500}
      />
      <Line
        points={[[0, 0, -1.2], [0, 0, 1.2]] as [number, number, number][]}
        color="#66ff66"
        lineWidth={4}
        transparent
        opacity={0.9}
        renderOrder={500}
      />
      <Line
        points={[[0, -1.2, 0], [0, 1.2, 0]] as [number, number, number][]}
        color="#6666ff"
        lineWidth={4}
        transparent
        opacity={0.9}
        renderOrder={500}
      />
      
      {/* Standard Bloch sphere axis labels */}
      <Text
        position={[1.4, 0, 0]}
        fontSize={0.25}
        color="#ff6666"
        anchorX="center"
        anchorY="middle"
        fontWeight="bold"
        renderOrder={1001}
      >
        X
      </Text>
      <Text
        position={[-1.4, 0, 0]}
        fontSize={0.25}
        color="#ff6666"
        anchorX="center"
        anchorY="middle"
        fontWeight="bold"
        renderOrder={1001}
      >
        -X
      </Text>
      <Text
        position={[0, 0, 1.4]}
        fontSize={0.25}
        color="#66ff66"
        anchorX="center"
        anchorY="middle"
        fontWeight="bold"
        renderOrder={1001}
      >
        Y
      </Text>
      <Text
        position={[0, 0, -1.4]}
        fontSize={0.25}
        color="#66ff66"
        anchorX="center"
        anchorY="middle"
        fontWeight="bold"
        renderOrder={1001}
      >
        -Y
      </Text>
      <Text
        position={[0, 1.4, 0]}
        fontSize={0.25}
        color="#6666ff"
        anchorX="center"
        anchorY="middle"
        fontWeight="bold"
        renderOrder={1001}
      >
        Z
      </Text>
      <Text
        position={[0, -1.4, 0]}
        fontSize={0.25}
        color="#6666ff"
        anchorX="center"
        anchorY="middle"
        fontWeight="bold"
        renderOrder={1001}
      >
        -Z
      </Text>
      
      {/* State vector (main arrow) - use actual Bloch coordinates, more prominent */}
      <group ref={vectorRef}>
        <VectorArrow
          start={[0, 0, 0]}
          end={[qubit.bloch.x, qubit.bloch.y, qubit.bloch.z]}
          color="#00ffff"
          lineWidth={10}
        />
        {/* Add a small sphere at the tip for visibility */}
        <mesh position={[qubit.bloch.x, qubit.bloch.y, qubit.bloch.z]} renderOrder={1002}>
          <sphereGeometry args={[0.06, 16, 8]} />
          <meshBasicMaterial 
            color="#00ffff"
            transparent
            opacity={0.95}
          />
        </mesh>
      </group>
      
      {/* State labels - positioned on Z-axis (Y in Three.js coordinates) */}
      {showState && (
        <>
          <Text
            position={[0, 1.6, 0]}
            fontSize={0.2}
            color="#ffffff"
            anchorX="center"
            anchorY="middle"
            fontWeight="bold"
            renderOrder={1001}
          >
            |0⟩
          </Text>
          <Text
            position={[0, -1.6, 0]}
            fontSize={0.2}
            color="#ffffff"
            anchorX="center"
            anchorY="middle"
            fontWeight="bold"
            renderOrder={1001}
          >
            |1⟩
          </Text>
        </>
      )}
      
      {/* Phase angle indicator */}
      {showPhase && qubit.bloch.y !== 0 && (
        <mesh rotation={[Math.PI / 2, 0, 0]}>
          <ringGeometry args={[0.3, 0.35, 32, 1, 0, Math.atan2(qubit.bloch.y, qubit.bloch.x)]} />
          <meshBasicMaterial 
            color="#ffaa00"
            transparent 
            opacity={0.6}
          />
        </mesh>
      )}
      
      {/* Purity indicator */}
      {qubit.bloch.purity < 1 && (
        <mesh>
          <sphereGeometry args={[qubit.bloch.purity, 16, 8]} />
          <meshBasicMaterial 
            color="#ff6600"
            transparent 
            opacity={0.1}
            wireframe
          />
        </mesh>
      )}
    </group>
  );
}

function formatComplex(value: number | [number, number]): string {
  if (typeof value === 'number') {
    return value.toFixed(3);
  }
  
  // Handle complex number array format
  if (Array.isArray(value) && value.length === 2) {
    const [real, imag] = value;
    if (Math.abs(imag) < 1e-10) return real.toFixed(3);
    if (Math.abs(real) < 1e-10) return `${imag.toFixed(3)}i`;
    const imagPart = imag >= 0 ? `+${imag.toFixed(3)}i` : `${imag.toFixed(3)}i`;
    return `${real.toFixed(3)}${imagPart}`;
  }
  
  return value.toString();
}
