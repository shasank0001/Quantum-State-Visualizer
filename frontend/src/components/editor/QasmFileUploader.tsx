import React, { useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Upload, FileText } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

interface QasmFileUploaderProps {
  onFileLoad: (content: string, filename: string) => void;
}

export const QasmFileUploader: React.FC<QasmFileUploaderProps> = ({ onFileLoad }) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { toast } = useToast();

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // Validate file extension
    if (!file.name.toLowerCase().endsWith('.qasm') && !file.name.toLowerCase().endsWith('.txt')) {
      toast({
        title: "Invalid file type",
        description: "Please upload a .qasm or .txt file containing OpenQASM code",
        variant: "destructive",
        duration: 3000,
      });
      return;
    }

    // Validate file size (max 1MB)
    if (file.size > 1024 * 1024) {
      toast({
        title: "File too large",
        description: "Please upload a file smaller than 1MB",
        variant: "destructive",
        duration: 3000,
      });
      return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const content = e.target?.result as string;
        if (content) {
          onFileLoad(content, file.name);
          toast({
            title: "File uploaded successfully",
            description: `Loaded ${file.name}`,
            duration: 2000,
          });
        }
      } catch (error) {
        console.error('Error reading file:', error);
        toast({
          title: "Error reading file",
          description: "Could not read the selected file",
          variant: "destructive",
          duration: 3000,
        });
      }
    };

    reader.onerror = () => {
      toast({
        title: "Error reading file",
        description: "Could not read the selected file",
        variant: "destructive",
        duration: 3000,
      });
    };

    reader.readAsText(file);
    
    // Reset the input value to allow uploading the same file again
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  return (
    <div className="flex items-center gap-2">
      <input
        ref={fileInputRef}
        type="file"
        accept=".qasm,.txt"
        onChange={handleFileUpload}
        className="hidden"
        aria-label="Upload QASM file"
      />
      <Button
        variant="outline"
        size="sm"
        onClick={handleUploadClick}
        className="transition-all duration-200 hover:scale-105"
      >
        <Upload className="w-4 h-4 mr-2" />
        Upload .qasm
      </Button>
      <div className="flex items-center gap-1 text-xs text-muted-foreground">
        <FileText className="w-3 h-3" />
        <span>Max 1MB</span>
      </div>
    </div>
  );
};

export default QasmFileUploader;
