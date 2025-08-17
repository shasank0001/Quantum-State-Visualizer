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
            camera={{ position: [3, 3, 3], fov: 50 }}
            dpr={[1, 2]}
            performance={{ min: 0.5 }}
          >
            <SphereContent qubit={qubit} isSelected={isSelected} size={size} />
            <OrbitControls enableZoom={false} enablePan={false} />
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
  
  // Calculate vector length based on purity
  const vectorLength = Math.sqrt(2 * qubit.bloch.purity - 1);
  const vectorOpacity = Math.max(0.3, qubit.bloch.purity);
  
  // Update arrow rotation to point along vector direction
  useEffect(() => {
    if (!arrowRef.current) return;
    
    const direction = new THREE.Vector3(
      qubit.bloch.x * vectorLength,
      qubit.bloch.y * vectorLength,
      qubit.bloch.z * vectorLength
    );
    
    if (direction.length() > 0) {
      const up = new THREE.Vector3(0, 1, 0); // Default cone direction
      const quaternion = new THREE.Quaternion();
      quaternion.setFromUnitVectors(up, direction.normalize());
      arrowRef.current.setRotationFromQuaternion(quaternion);
    }
  }, [qubit.bloch.x, qubit.bloch.y, qubit.bloch.z, vectorLength]);
  
  // Axis lines data
  const axisLines = useMemo(() => [
    { points: [[-1, 0, 0], [1, 0, 0]], color: '#ff4444' }, // X-axis (red)
    { points: [[0, -1, 0], [0, 1, 0]], color: '#44ff44' }, // Y-axis (green)
    { points: [[0, 0, -1], [0, 0, 1]], color: '#4444ff' }, // Z-axis (blue)
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
      <ambientLight intensity={0.4} />
      <pointLight position={[10, 10, 10]} intensity={0.8} />
      
      {/* Bloch sphere */}
      <mesh>
        <sphereGeometry args={[1, 32, 16]} />
        <meshPhongMaterial 
          color="#1a1a2e"
          transparent 
          opacity={isSelected ? 0.3 : 0.15}
          wireframe={false}
        />
      </mesh>
      
      {/* Wireframe sphere */}
      <mesh>
        <sphereGeometry args={[1.01, 16, 8]} />
        <meshBasicMaterial 
          color={isSelected ? "#00bfff" : "#444444"}
          wireframe 
          transparent 
          opacity={0.3}
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
      
      {/* Axis labels */}
      <Text
        position={[1.2, 0, 0]}
        fontSize={0.15}
        color="#ff4444"
        anchorX="center"
        anchorY="middle"
      >
        X
      </Text>
      <Text
        position={[0, 1.2, 0]}
        fontSize={0.15}
        color="#44ff44"
        anchorX="center"
        anchorY="middle"
      >
        Y
      </Text>
      <Text
        position={[0, 0, 1.2]}
        fontSize={0.15}
        color="#4444ff"
        anchorX="center"
        anchorY="middle"
      >
        Z
      </Text>
      
      {/* State vector */}
      <group ref={vectorRef}>
        {/* Vector line */}
        <Line
          points={[
            [0, 0, 0],
            [
              qubit.bloch.x * vectorLength,
              qubit.bloch.y * vectorLength,
              qubit.bloch.z * vectorLength
            ]
          ]}
          color={isSelected ? "#00bfff" : "#ffaa00"}
          lineWidth={4}
          transparent
          opacity={vectorOpacity}
        />
        
        {/* Vector arrow head */}
        <mesh 
          ref={arrowRef}
          position={[
            qubit.bloch.x * vectorLength,
            qubit.bloch.y * vectorLength,
            qubit.bloch.z * vectorLength
          ]}
        >
          <coneGeometry args={[0.06, 0.12, 8]} />
          <meshBasicMaterial 
            color={isSelected ? "#00bfff" : "#ffaa00"}
            transparent
            opacity={vectorOpacity}
            depthTest={false}
            side={THREE.DoubleSide}
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