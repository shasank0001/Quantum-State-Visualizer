import React, { useRef, useEffect } from 'react';
import Editor from '@monaco-editor/react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Code2, Maximize2, Minimize2, Download, Copy } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

interface MonacoQasmEditorProps {
  value: string;
  onChange: (value: string) => void;
  isFullscreen?: boolean;
  onToggleFullscreen: () => void;
  onClose: () => void;
}

export const MonacoQasmEditor: React.FC<MonacoQasmEditorProps> = ({
  value,
  onChange,
  isFullscreen = false,
  onToggleFullscreen,
  onClose
}) => {
  const editorRef = useRef<any>(null);
  const { toast } = useToast();

  // Handle editor resize when fullscreen mode changes
  useEffect(() => {
    if (editorRef.current) {
      setTimeout(() => {
        editorRef.current.layout();
      }, 100);
    }
  }, [isFullscreen]);

  const handleEditorDidMount = (editor: any, monaco: any) => {
    editorRef.current = editor;

    // Register OpenQASM language
    monaco.languages.register({ id: 'openqasm' });

    // Define OpenQASM tokens
    monaco.languages.setMonarchTokensProvider('openqasm', {
      tokenizer: {
        root: [
          // Comments
          [/\/\/.*$/, 'comment'],
          
          // Version declarations
          [/OPENQASM\s+\d+\.\d+;/, 'keyword.version'],
          
          // Include statements
          [/include\s+"[^"]*";/, 'keyword.include'],
          
          // Register declarations
          [/\b(qreg|creg)\b/, 'keyword.register'],
          
          // Gate definitions and calls
          [/\b(gate|opaque)\b/, 'keyword.gate-def'],
          [/\b(h|x|y|z|s|t|cx|cy|cz|ccx|rx|ry|rz|u1|u2|u3|reset|measure|barrier)\b/, 'keyword.gate'],
          
          // Control flow
          [/\b(if|for|while)\b/, 'keyword.control'],
          
          // Numbers
          [/\d*\.\d+([eE][\-+]?\d+)?/, 'number.float'],
          [/\d+/, 'number'],
          [/pi/, 'number.constant'],
          
          // Strings
          [/"([^"\\]|\\.)*$/, 'string.invalid'],
          [/"/, 'string', '@string'],
          
          // Identifiers
          [/[a-zA-Z_]\w*/, 'identifier'],
          
          // Operators and punctuation
          [/[{}()\[\]]/, '@brackets'],
          [/[<>=!]+/, 'operator'],
          [/[;,.]/, 'delimiter'],
        ],
        
        string: [
          [/[^\\"]+/, 'string'],
          [/\\./, 'string.escape.invalid'],
          [/"/, 'string', '@pop']
        ],
      },
    });

    // Define theme colors
    monaco.editor.defineTheme('openqasm-theme', {
      base: 'vs-dark',
      inherit: true,
      rules: [
        { token: 'comment', foreground: '6A9955', fontStyle: 'italic' },
        { token: 'keyword.version', foreground: '569CD6', fontStyle: 'bold' },
        { token: 'keyword.include', foreground: 'C586C0' },
        { token: 'keyword.register', foreground: '4EC9B0' },
        { token: 'keyword.gate-def', foreground: 'DCDCAA', fontStyle: 'bold' },
        { token: 'keyword.gate', foreground: '9CDCFE' },
        { token: 'keyword.control', foreground: 'C586C0' },
        { token: 'number', foreground: 'B5CEA8' },
        { token: 'number.float', foreground: 'B5CEA8' },
        { token: 'number.constant', foreground: 'D7BA7D' },
        { token: 'string', foreground: 'CE9178' },
        { token: 'identifier', foreground: 'D4D4D4' },
        { token: 'operator', foreground: 'D4D4D4' },
        { token: 'delimiter', foreground: 'D4D4D4' },
      ],
      colors: {
        'editor.background': '#1e1e1e',
        'editor.foreground': '#d4d4d4',
        'editorLineNumber.foreground': '#858585',
        'editor.selectionBackground': '#264f78',
        'editor.inactiveSelectionBackground': '#3a3d41',
      }
    });

    // Set the language and theme
    monaco.editor.setModelLanguage(editor.getModel(), 'openqasm');
    monaco.editor.setTheme('openqasm-theme');

    // Configure editor options
    editor.updateOptions({
      fontSize: 14,
      lineHeight: 20,
      minimap: { enabled: false }, // Disable minimap by default for more space
      scrollBeyondLastLine: false,
      automaticLayout: true,
      wordWrap: 'on',
      lineNumbers: 'on',
      folding: true,
      bracketMatching: 'always',
      autoIndent: 'advanced',
      padding: { top: 10, bottom: 10 },
      scrollbar: {
        verticalScrollbarSize: 8,
        horizontalScrollbarSize: 8,
        useShadows: false,
      },
      overviewRulerLanes: 0, // Remove overview ruler for cleaner look
      hideCursorInOverviewRuler: true,
      renderLineHighlight: 'line',
      selectionHighlight: true,
      occurrencesHighlight: true,
    });

    // Force layout after a brief delay to ensure proper sizing
    setTimeout(() => {
      editor.layout();
    }, 100);
  };

  const handleDownload = () => {
    try {
      const blob = new Blob([value], { type: 'text/plain' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = 'circuit.qasm';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
      
      toast({
        description: "QASM file downloaded successfully",
        duration: 2000,
      });
    } catch (error) {
      console.error('Download error:', error);
      toast({
        title: "Download failed",
        description: "Could not download the file",
        variant: "destructive",
        duration: 3000,
      });
    }
  };

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(value);
      toast({
        description: "Code copied to clipboard",
        duration: 2000,
      });
    } catch (error) {
      console.error('Copy error:', error);
      toast({
        title: "Copy failed",
        description: "Could not copy code to clipboard",
        variant: "destructive",
        duration: 3000,
      });
    }
  };

  const handleFormatCode = () => {
    if (editorRef.current) {
      editorRef.current.getAction('editor.action.formatDocument').run();
    }
  };

  return (
    <Card className={`${isFullscreen ? 'fixed inset-4 z-50' : 'w-full'} flex flex-col animate-in fade-in duration-300`}>
      <CardHeader className="pb-3 flex-shrink-0">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <CardTitle className="flex items-center gap-2 text-lg">
              <Code2 className="h-5 w-5" />
              Monaco QASM Editor
            </CardTitle>
            <Badge variant="secondary" className="text-xs">
              Advanced Editor
            </Badge>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleFormatCode}
              className="transition-all duration-200 hover:scale-105"
            >
              Format
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={handleCopy}
              className="transition-all duration-200 hover:scale-105"
            >
              <Copy className="w-4 h-4" />
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={handleDownload}
              className="transition-all duration-200 hover:scale-105"
            >
              <Download className="w-4 h-4" />
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={onToggleFullscreen}
              className="transition-all duration-200 hover:scale-105"
            >
              {isFullscreen ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={onClose}
              className="transition-all duration-200 hover:scale-105"
            >
              ✕
            </Button>
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="flex-shrink-0 p-0">
        <div className={`w-full ${isFullscreen ? 'h-[calc(100vh-180px)]' : 'h-[500px]'} border rounded-b-lg overflow-hidden`}>
          <Editor
            value={value}
            onChange={(val) => onChange(val || '')}
            onMount={handleEditorDidMount}
            width="100%"
            height="100%"
            options={{
              theme: 'openqasm-theme',
              language: 'openqasm',
              automaticLayout: true,
              scrollBeyondLastLine: false,
              minimap: { enabled: !isFullscreen }, // Hide minimap in normal mode for more space
              lineNumbers: 'on',
              wordWrap: 'on',
              fontSize: isFullscreen ? 16 : 14,
              lineHeight: isFullscreen ? 24 : 20,
            }}
          />
        </div>
      </CardContent>
    </Card>
  );
};

export default MonacoQasmEditor;
