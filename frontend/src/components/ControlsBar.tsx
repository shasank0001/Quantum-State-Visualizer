import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Slider } from '@/components/ui/slider';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { useQuantumStore } from '@/store/quantumStore';
import { 
  RotateCcwIcon, 
  SettingsIcon, 
  ZapIcon,
  ClockIcon,
  DatabaseIcon 
} from 'lucide-react';

export const ControlsBar = () => {
  const { 
    simulation, 
    endianness, 
    toggleEndianness, 
    compactMode, 
    toggleCompactMode,
    resetSimulation,
    qubits 
  } = useQuantumStore();
  
  return (
    <Card className="quantum-card">
      <div className="p-4">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          
          {/* Simulation Controls */}
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <ZapIcon className="w-4 h-4 text-quantum-primary" />
              <Label className="font-semibold">Simulation</Label>
            </div>
            
            <div className="space-y-2">
              <Button
                variant="outline"
                size="sm"
                onClick={resetSimulation}
                disabled={simulation.status === 'running'}
                className="w-full border-border hover:bg-accent"
              >
                <RotateCcwIcon className="w-3 h-3 mr-2" />
                Reset
              </Button>
              
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Pipeline:</span>
                <Badge variant="outline" className="border-quantum-primary text-quantum-primary">
                  {simulation.pipeline.toUpperCase()}
                </Badge>
              </div>
              
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Shots:</span>
                <span className="mono-scientific text-foreground">{simulation.shots}</span>
              </div>
            </div>
          </div>
          
          <Separator orientation="vertical" className="hidden md:block bg-border" />
          
          {/* Speed Controls */}
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <ClockIcon className="w-4 h-4 text-quantum-secondary" />
              <Label className="font-semibold">Speed</Label>
            </div>
            
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Animation:</span>
                <span className="text-foreground">1.0x</span>
              </div>
              <Slider
                value={[1]}
                min={0.1}
                max={3}
                step={0.1}
                className="w-full"
                disabled={simulation.status === 'running'}
              />
              
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Precision:</span>
                <span className="text-foreground">High</span>
              </div>
              <Slider
                value={[3]}
                min={1}
                max={4}
                step={1}
                className="w-full"
              />
            </div>
          </div>
          
          <Separator orientation="vertical" className="hidden md:block bg-border" />
          
          {/* Display Settings */}
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <SettingsIcon className="w-4 h-4 text-quantum-accent" />
              <Label className="font-semibold">Display</Label>
            </div>
            
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <Label htmlFor="endianness" className="text-sm text-muted-foreground">
                  Big Endian
                </Label>
                <Switch
                  id="endianness"
                  checked={endianness === 'big'}
                  onCheckedChange={toggleEndianness}
                />
              </div>
              
              <div className="flex items-center justify-between">
                <Label htmlFor="compact" className="text-sm text-muted-foreground">
                  Compact Mode
                </Label>
                <Switch
                  id="compact"
                  checked={compactMode}
                  onCheckedChange={toggleCompactMode}
                />
              </div>
              
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Qubits:</span>
                <span className="mono-scientific text-foreground">{qubits.length}</span>
              </div>
            </div>
          </div>
          
          <Separator orientation="vertical" className="hidden md:block bg-border" />
          
          {/* System Status */}
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <DatabaseIcon className="w-4 h-4 text-quantum-warning" />
              <Label className="font-semibold">System</Label>
            </div>
            
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Status:</span>
                <Badge 
                  variant={simulation.status === 'completed' ? 'default' : 'secondary'}
                  className={
                    simulation.status === 'running' ? 'animate-quantum-pulse' : ''
                  }
                >
                  {simulation.status.toUpperCase()}
                </Badge>
              </div>
              
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Memory:</span>
                <span className="mono-scientific text-foreground">
                  {Math.pow(2, qubits.length)} states
                </span>
              </div>
              
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Accuracy:</span>
                <span className="text-quantum-success">±1e-6</span>
              </div>
            </div>
          </div>
          
        </div>
      </div>
    </Card>
  );
};