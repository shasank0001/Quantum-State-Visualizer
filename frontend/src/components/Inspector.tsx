import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { useQuantumStore } from '@/store/quantumStore';
import { CopyIcon, XIcon } from 'lucide-react';

export const Inspector = () => {
  const { qubits, selectedQubit, setSelectedQubit } = useQuantumStore();
  
  if (selectedQubit === null) {
    return (
      <Card className="quantum-card">
        <div className="p-6">
          <h3 className="text-xl font-bold text-foreground mb-4">Quantum Inspector</h3>
          <div className="text-center py-8">
            <div className="text-muted-foreground">
              <p className="mb-2">No qubit selected</p>
              <p className="text-sm">Click on a Bloch sphere to inspect its quantum state</p>
            </div>
          </div>
        </div>
      </Card>
    );
  }
  
  const qubit = qubits.find(q => q.id === selectedQubit);
  if (!qubit) return null;
  
  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    // TODO: Add toast notification
  };
  
  const formatComplex = (valueOrReal: number | [number, number], imag?: number) => {
    let r: number, i: number;
    if (Array.isArray(valueOrReal)) {
      r = valueOrReal[0] ?? 0; i = valueOrReal[1] ?? 0;
    } else {
      r = valueOrReal; i = imag ?? 0;
    }
    r = Math.abs(r) < 1e-10 ? 0 : r;
    i = Math.abs(i) < 1e-10 ? 0 : i;
    if (i === 0) return r.toFixed(4);
    if (r === 0) return `${i.toFixed(4)}i`;
    return `${r.toFixed(4)} ${i >= 0 ? '+' : ''}${i.toFixed(4)}i`;
  };
  
  return (
    <Card className="quantum-card">
      <div className="p-6 space-y-6">
        <div className="flex items-center justify-between">
          <h3 className="text-xl font-bold text-foreground">Quantum Inspector</h3>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setSelectedQubit(null)}
            className="hover:bg-accent"
          >
            <XIcon className="w-4 h-4" />
          </Button>
        </div>
        
        {/* Qubit Header */}
        <div className="flex items-center gap-3">
          <h4 className="text-lg font-semibold text-foreground">{qubit.label}</h4>
          <Badge variant="outline" className="border-quantum-primary text-quantum-primary">
            Qubit {qubit.id}
          </Badge>
        </div>
        
        <Separator className="bg-border" />
        
        {/* Bloch Coordinates */}
        <div className="space-y-3">
          <h5 className="font-semibold text-foreground">Bloch Coordinates</h5>
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center p-3 rounded-lg bg-gradient-quantum-subtle border border-border">
              <div className="text-xs text-muted-foreground mb-1">X</div>
              <div className="text-lg font-bold text-quantum-primary mono-scientific">
                {qubit.bloch.x.toFixed(4)}
              </div>
            </div>
            <div className="text-center p-3 rounded-lg bg-gradient-quantum-subtle border border-border">
              <div className="text-xs text-muted-foreground mb-1">Y</div>
              <div className="text-lg font-bold text-quantum-secondary mono-scientific">
                {qubit.bloch.y.toFixed(4)}
              </div>
            </div>
            <div className="text-center p-3 rounded-lg bg-gradient-quantum-subtle border border-border">
              <div className="text-xs text-muted-foreground mb-1">Z</div>
              <div className="text-lg font-bold text-quantum-accent mono-scientific">
                {qubit.bloch.z.toFixed(4)}
              </div>
            </div>
          </div>
        </div>
        
        <Separator className="bg-border" />
        
        {/* Purity */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <h5 className="font-semibold text-foreground">Purity</h5>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => copyToClipboard(qubit.bloch.purity.toString())}
              className="hover:bg-accent"
            >
              <CopyIcon className="w-3 h-3" />
            </Button>
          </div>
          <div className="p-3 rounded-lg bg-gradient-quantum-subtle border border-border">
            <div className="text-2xl font-bold text-foreground mono-scientific">
              {qubit.bloch.purity.toFixed(6)}
            </div>
            <div className="text-xs text-muted-foreground mt-1">
              {qubit.bloch.purity === 1 ? 'Pure state' : 'Mixed state'}
            </div>
          </div>
        </div>
        
        <Separator className="bg-border" />
        
        {/* Density Matrix */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h5 className="font-semibold text-foreground">Density Matrix &rho;</h5>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => copyToClipboard(JSON.stringify(qubit.rho))}
              className="hover:bg-accent"
            >
              <CopyIcon className="w-3 h-3" />
            </Button>
          </div>
          
          <div className="p-4 rounded-lg bg-gradient-quantum-subtle border border-border">
            <table className="w-full mono-scientific text-sm">
              <tbody>
                <tr>
                  <td className="text-center p-2 border-r border-b border-border">
                    {formatComplex(qubit.rho[0][0] as any)}
                  </td>
                  <td className="text-center p-2 border-b border-border">
                    {formatComplex(qubit.rho[0][1] as any)}
                  </td>
                </tr>
                <tr>
                  <td className="text-center p-2 border-r border-border">
                    {formatComplex(qubit.rho[1][0] as any)}
                  </td>
                  <td className="text-center p-2">
                    {formatComplex(qubit.rho[1][1] as any)}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        
        {/* Vector Length */}
        <div className="space-y-2">
          <h5 className="font-semibold text-foreground">Vector Length</h5>
          <div className="p-3 rounded-lg bg-gradient-quantum-subtle border border-border">
            <div className="text-lg font-bold text-foreground mono-scientific">
              {Math.sqrt(
                qubit.bloch.x * qubit.bloch.x + qubit.bloch.y * qubit.bloch.y + qubit.bloch.z * qubit.bloch.z
              ).toFixed(4)}
            </div>
            <div className="text-xs text-muted-foreground mt-1">
              &radic;(x&sup2; + y&sup2; + z&sup2;)
            </div>
          </div>
        </div>
        
        {/* State Information */}
        <div className="mt-6 p-3 rounded-lg bg-muted/50 border border-border">
          <div className="text-xs text-muted-foreground space-y-1">
            <p>&bull; Bloch vector length indicates purity</p>
            <p>&bull; Pure states: length = 1</p>
            <p>&bull; Mixed states: length &lt; 1</p>
            <p>&bull; Vector direction shows quantum state orientation</p>
          </div>
        </div>
      </div>
    </Card>
  );
};