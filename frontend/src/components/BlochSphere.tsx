import { useRef, useMemo, useEffect } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Text, Line } from '@react-three/drei';
import * as THREE from 'three';
import { QubitState } from '@/store/quantumStore';

interface BlochSphereProps {
  qubit: QubitState;
  isSelected: boolean;
  onSelect: () => void;
  size?: 'small' | 'medium' | 'large';
}

interface SphereContentProps {
  qubit: QubitState;
  isSelected: boolean;
  size: 'small' | 'medium' | 'large';
}

export const BlochSphere = ({ qubit, isSelected, onSelect, size = 'medium' }: BlochSphereProps) => {
  const canvasHeight = size === 'small' ? 150 : size === 'medium' ? 200 : 250;
  
  return (
    <div 
      className={`
        sphere-container quantum-transition cursor-pointer rounded-xl
        ${isSelected ? 'ring-2 ring-quantum-primary shadow-quantum' : 'hover:shadow-glow'}
        ${size === 'small' ? 'p-2' : 'p-4'}
      `}
      onClick={onSelect}
    >
      <div className="quantum-card rounded-lg overflow-hidden">
        <div className="p-2 bg-gradient-quantum-subtle border-b border-border">
          <div className="flex items-center justify-between">
            <span className="text-sm font-semibold text-foreground">{qubit.label}</span>
            <span className="text-xs text-muted-foreground mono-scientific">
              P = {qubit.bloch.purity.toFixed(3)}
            </span>
          </div>
        </div>
        
        <div style={{ height: canvasHeight }}>
          <Canvas
            camera={{ position: [2.5, 2.5, 2.5], fov: 50 }}
            dpr={[1, 2]}
            performance={{ min: 0.5 }}
          >
            <SphereContent qubit={qubit} isSelected={isSelected} size={size} />
            <OrbitControls 
              enableZoom={false} 
              enablePan={false}
              target={[0, 0, 0]}
            />
          </Canvas>
        </div>
        
        <div className="p-2 bg-gradient-quantum-subtle border-t border-border">
          <div className="grid grid-cols-3 gap-2 text-xs mono-scientific">
            <div className="text-center">
              <div className="text-muted-foreground">X</div>
              <div className="text-quantum-primary">{qubit.bloch.x.toFixed(3)}</div>
            </div>
            <div className="text-center">
              <div className="text-muted-foreground">Y</div>
              <div className="text-quantum-secondary">{qubit.bloch.y.toFixed(3)}</div>
            </div>
            <div className="text-center">
              <div className="text-muted-foreground">Z</div>
              <div className="text-quantum-accent">{qubit.bloch.z.toFixed(3)}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

function SphereContent({ qubit, isSelected, size }: SphereContentProps) {
  const meshRef = useRef<THREE.Group>(null);
  const vectorRef = useRef<THREE.Group>(null);
  const arrowRef = useRef<THREE.Mesh>(null);
  
  // Calculate vector length - should be the magnitude of Bloch vector (≤1 for physical states)
  const vectorLength = Math.min(1.0, Math.sqrt(
    qubit.bloch.x * qubit.bloch.x + 
    qubit.bloch.y * qubit.bloch.y + 
    qubit.bloch.z * qubit.bloch.z
  ));
  const vectorOpacity = Math.max(0.8, qubit.bloch.purity);
  
  // Update arrow rotation to point along vector direction
  useEffect(() => {
    if (!arrowRef.current) return;
    
    const direction = new THREE.Vector3(
      qubit.bloch.x,
      qubit.bloch.y,
      qubit.bloch.z
    );
    
    if (direction.length() > 0.001) {
      const up = new THREE.Vector3(0, 1, 0); // Default cone direction
      const quaternion = new THREE.Quaternion();
      quaternion.setFromUnitVectors(up, direction.normalize());
      arrowRef.current.setRotationFromQuaternion(quaternion);
    }
  }, [qubit.bloch.x, qubit.bloch.y, qubit.bloch.z]);
  
  // Axis lines data - corrected coordinate system
  const axisLines = useMemo(() => [
    { points: [[-1, 0, 0], [1, 0, 0]], color: '#ff4444' }, // X-axis (red)
    { points: [[0, 0, -1], [0, 0, 1]], color: '#44ff44' }, // Y-axis (green) 
    { points: [[0, -1, 0], [0, 1, 0]], color: '#4444ff' }, // Z-axis (blue)
  ], []);
  
  // Animate sphere rotation
  useFrame((state) => {
    if (meshRef.current) {
      meshRef.current.rotation.y = state.clock.elapsedTime * 0.1;
    }
  });
  
  return (
    <group ref={meshRef}>
      {/* Ambient lighting */}
      <ambientLight intensity={0.6} />
      <pointLight position={[5, 5, 5]} intensity={0.8} />
      <pointLight position={[-5, -5, 5]} intensity={0.4} />
      
      {/* Bloch sphere - more transparent */}
      <mesh>
        <sphereGeometry args={[1, 64, 32]} />
        <meshPhongMaterial 
          color="#2a2a3a"
          transparent 
          opacity={isSelected ? 0.15 : 0.08}
          wireframe={false}
          side={THREE.DoubleSide}
        />
      </mesh>
      
      {/* Wireframe sphere */}
      <mesh>
        <sphereGeometry args={[1.01, 24, 12]} />
        <meshBasicMaterial 
          color={isSelected ? "#00bfff" : "#666666"}
          wireframe 
          transparent 
          opacity={0.4}
        />
      </mesh>
      
      {/* Coordinate axes */}
      {axisLines.map((axis, index) => (
        <Line
          key={index}
          points={axis.points as [number, number, number][]}
          color={axis.color}
          lineWidth={2}
          transparent
          opacity={0.6}
        />
      ))}
      
      {/* Axis labels with standard Bloch sphere conventions */}
      <Text
        position={[1.3, 0, 0]}
        fontSize={0.15}
        color="#ff4444"
        anchorX="center"
        anchorY="middle"
      >
        X
      </Text>
      <Text
        position={[-1.3, 0, 0]}
        fontSize={0.15}
        color="#ff4444"
        anchorX="center"
        anchorY="middle"
      >
        -X
      </Text>
      <Text
        position={[0, 0, 1.3]}
        fontSize={0.15}
        color="#44ff44"
        anchorX="center"
        anchorY="middle"
      >
        Y
      </Text>
      <Text
        position={[0, 0, -1.3]}
        fontSize={0.15}
        color="#44ff44"
        anchorX="center"
        anchorY="middle"
      >
        -Y
      </Text>
      <Text
        position={[0, 1.3, 0]}
        fontSize={0.15}
        color="#4444ff"
        anchorX="center"
        anchorY="middle"
      >
        Z
      </Text>
      <Text
        position={[0, -1.3, 0]}
        fontSize={0.15}
        color="#4444ff"
        anchorX="center"
        anchorY="middle"
      >
        -Z
      </Text>
      
      {/* Quantum state labels on Z-axis */}
      <Text
        position={[0, 1.6, 0]}
        fontSize={0.18}
        color="#ffffff"
        anchorX="center"
        anchorY="middle"
        fontWeight="bold"
      >
        |0⟩
      </Text>
      <Text
        position={[0, -1.6, 0]}
        fontSize={0.18}
        color="#ffffff"
        anchorX="center"
        anchorY="middle"
        fontWeight="bold"
      >
        |1⟩
      </Text>
      
      {/* State vector */}
      <group ref={vectorRef}>
        {/* Vector line - make it more prominent */}
        <Line
          points={[
            [0, 0, 0],
            [qubit.bloch.x, qubit.bloch.y, qubit.bloch.z]
          ]}
          color={isSelected ? "#00ffff" : "#ff6600"}
          lineWidth={6}
          transparent
          opacity={Math.max(0.8, vectorOpacity)}
        />
        
        {/* Vector arrow head - larger and more visible */}
        <mesh 
          ref={arrowRef}
          position={[qubit.bloch.x, qubit.bloch.y, qubit.bloch.z]}
        >
          <coneGeometry args={[0.08, 0.16, 8]} />
          <meshBasicMaterial 
            color={isSelected ? "#00ffff" : "#ff6600"}
            transparent
            opacity={Math.max(0.8, vectorOpacity)}
            depthTest={false}
            side={THREE.DoubleSide}
          />
        </mesh>
        
        {/* Add a small sphere at the vector tip for better visibility */}
        <mesh 
          position={[qubit.bloch.x, qubit.bloch.y, qubit.bloch.z]}
        >
          <sphereGeometry args={[0.04, 16, 8]} />
          <meshBasicMaterial 
            color={isSelected ? "#00ffff" : "#ff6600"}
            transparent
            opacity={Math.max(0.9, vectorOpacity)}
          />
        </mesh>
      </group>
      
      {/* Purity indicator ring at equator */}
      {qubit.bloch.purity < 1 && (
        <mesh rotation={[Math.PI / 2, 0, 0]}>
          <ringGeometry args={[0.98, 1.02, 32]} />
          <meshBasicMaterial 
            color="#ff6600"
            transparent 
            opacity={0.4}
          />
        </mesh>
      )}
    </group>
  );
}