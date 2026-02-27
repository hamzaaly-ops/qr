import { useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Upload, Image, X } from "lucide-react";

interface UploadZoneProps {
  onFileSelect: (file: File) => void;
  isAnalyzing: boolean;
}

const UploadZone = ({ onFileSelect, isAnalyzing }: UploadZoneProps) => {
  const [isDragging, setIsDragging] = useState(false);
  const [preview, setPreview] = useState<string | null>(null);

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(e.type === "dragenter" || e.type === "dragover");
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (file?.type.startsWith("image/")) {
      setPreview(URL.createObjectURL(file));
      onFileSelect(file);
    }
  }, [onFileSelect]);

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setPreview(URL.createObjectURL(file));
      onFileSelect(file);
    }
  };

  const clearPreview = () => {
    setPreview(null);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.2 }}
    >
      <label
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        className={`
          relative block w-full rounded-2xl border-2 border-dashed p-8 text-center cursor-pointer
          transition-all duration-300 overflow-hidden
          ${isDragging
            ? "border-primary bg-primary/5 glow-primary"
            : "border-border hover:border-primary/40 hover:bg-card"
          }
          ${isAnalyzing ? "pointer-events-none opacity-60" : ""}
        `}
      >
        {/* Scan line animation when analyzing */}
        {isAnalyzing && (
          <div className="absolute inset-0 overflow-hidden">
            <div className="absolute inset-x-0 h-20 scan-line animate-scan" />
          </div>
        )}

        <input
          type="file"
          accept="image/*"
          onChange={handleFileInput}
          className="hidden"
          disabled={isAnalyzing}
        />

        <AnimatePresence mode="wait">
          {preview ? (
            <motion.div
              key="preview"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              className="relative"
            >
              <img
                src={preview}
                alt="QR Preview"
                className="mx-auto max-h-40 rounded-lg object-contain"
              />
              {!isAnalyzing && (
                <button
                  onClick={(e) => { e.preventDefault(); clearPreview(); }}
                  className="absolute -top-2 -right-2 w-8 h-8 rounded-full bg-secondary flex items-center justify-center text-muted-foreground hover:text-foreground transition-colors"
                >
                  <X className="w-4 h-4" />
                </button>
              )}
            </motion.div>
          ) : (
            <motion.div
              key="upload"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="space-y-3"
            >
              <div className="mx-auto w-14 h-14 rounded-xl bg-secondary flex items-center justify-center">
                {isDragging ? (
                  <Image className="w-7 h-7 text-primary" />
                ) : (
                  <Upload className="w-7 h-7 text-muted-foreground" />
                )}
              </div>
              <div>
                <p className="text-foreground font-medium">
                  Drop your QR code image here
                </p>
                <p className="text-sm text-muted-foreground mt-1">
                  or click to browse · PNG, JPG, SVG
                </p>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </label>
    </motion.div>
  );
};

export default UploadZone;
