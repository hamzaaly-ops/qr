import { useEffect, useRef, useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Camera, CameraOff, ScanLine, Wifi, WifiOff } from "lucide-react";
import { Html5Qrcode } from "html5-qrcode";

interface LiveScannerProps {
  onUrlDetected: (url: string) => void;
  onLiveFrame?: (url: string, imageBlob: Blob) => void;
  isAnalyzing: boolean;
  lastAnalyzedUrl: string | null;
}

const LiveScanner = ({ onUrlDetected, onLiveFrame, isAnalyzing, lastAnalyzedUrl }: LiveScannerProps) => {
  const [isActive, setIsActive] = useState(false);
  const [detectedUrl, setDetectedUrl] = useState<string | null>(null);
  const [cameraError, setCameraError] = useState<string | null>(null);
  const scannerRef = useRef<Html5Qrcode | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const lastSentUrlRef = useRef<string | null>(null);

  const handleQrDetected = useCallback(
    (decodedText: string) => {
      setDetectedUrl(decodedText);

      // Only send if URL changed and debounce 500ms
      if (decodedText === lastSentUrlRef.current) return;

      if (debounceRef.current) clearTimeout(debounceRef.current);
      debounceRef.current = setTimeout(() => {
        lastSentUrlRef.current = decodedText;

        // If onLiveFrame is provided, capture a frame and send both
        if (onLiveFrame) {
          const videoEl = document.querySelector("#live-scanner-region video") as HTMLVideoElement | null;
          if (videoEl) {
            const canvas = document.createElement("canvas");
            canvas.width = videoEl.videoWidth;
            canvas.height = videoEl.videoHeight;
            const ctx = canvas.getContext("2d");
            ctx?.drawImage(videoEl, 0, 0);
            canvas.toBlob((blob) => {
              if (blob) onLiveFrame(decodedText, blob);
            }, "image/jpeg", 0.8);
            return;
          }
        }
        onUrlDetected(decodedText);
      }, 500);
    },
    [onUrlDetected, onLiveFrame]
  );

  const startScanner = async () => {
    setCameraError(null);
    try {
      const scanner = new Html5Qrcode("live-scanner-region");
      scannerRef.current = scanner;
      await scanner.start(
        { facingMode: "environment" },
        { fps: 10, qrbox: { width: 250, height: 250 } },
        handleQrDetected,
        () => {} // ignore errors on each frame
      );
      setIsActive(true);
    } catch (err: any) {
      setCameraError(err?.message || "Camera access denied");
      setIsActive(false);
    }
  };

  const stopScanner = async () => {
    if (scannerRef.current?.isScanning) {
      await scannerRef.current.stop();
    }
    scannerRef.current = null;
    setIsActive(false);
    setDetectedUrl(null);
    lastSentUrlRef.current = null;
  };

  useEffect(() => {
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
      if (scannerRef.current?.isScanning) {
        scannerRef.current.stop().catch(() => {});
      }
    };
  }, []);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.15 }}
      className="space-y-3"
    >
      {/* Toggle button */}
      <button
        onClick={isActive ? stopScanner : startScanner}
        className={`
          w-full flex items-center justify-center gap-3 py-3 px-4 rounded-xl font-medium text-sm transition-all duration-300 border
          ${isActive
            ? "bg-primary/10 border-primary/30 text-primary glow-primary"
            : "bg-card border-border text-muted-foreground hover:border-primary/30 hover:text-foreground"
          }
        `}
      >
        {isActive ? (
          <>
            <CameraOff className="w-4 h-4" />
            Stop Live Scan
          </>
        ) : (
          <>
            <Camera className="w-4 h-4" />
            Start Live Camera Scan
          </>
        )}
      </button>

      {/* Camera error */}
      <AnimatePresence>
        {cameraError && (
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="text-xs text-danger font-mono text-center"
          >
            {cameraError}
          </motion.p>
        )}
      </AnimatePresence>

      {/* Scanner viewport */}
      <AnimatePresence>
        {isActive && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.4, ease: "easeInOut" }}
            className="overflow-hidden"
          >
            <div className="relative rounded-2xl overflow-hidden border border-border bg-secondary">
              {/* Scanner container */}
              <div
                id="live-scanner-region"
                ref={containerRef}
                className="w-full aspect-square max-h-[320px]"
              />

              {/* Scanning overlay */}
              <div className="absolute inset-0 pointer-events-none">
                {/* Corner markers */}
                <div className="absolute top-4 left-4 w-8 h-8 border-t-2 border-l-2 border-primary rounded-tl-md" />
                <div className="absolute top-4 right-4 w-8 h-8 border-t-2 border-r-2 border-primary rounded-tr-md" />
                <div className="absolute bottom-4 left-4 w-8 h-8 border-b-2 border-l-2 border-primary rounded-bl-md" />
                <div className="absolute bottom-4 right-4 w-8 h-8 border-b-2 border-r-2 border-primary rounded-br-md" />

                {/* Scan line */}
                <div className="absolute inset-x-8 h-0.5 bg-primary/60 animate-scan" />
              </div>

              {/* Status bar */}
              <div className="absolute bottom-0 inset-x-0 bg-background/80 backdrop-blur-sm px-4 py-2 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  {isAnalyzing ? (
                    <Wifi className="w-3 h-3 text-primary animate-pulse" />
                  ) : (
                    <WifiOff className="w-3 h-3 text-muted-foreground" />
                  )}
                  <span className="text-xs font-mono text-muted-foreground">
                    {isAnalyzing ? "Analyzing..." : "Scanning..."}
                  </span>
                </div>
                {detectedUrl && (
                  <span className="text-xs font-mono text-primary truncate max-w-[200px]">
                    {detectedUrl}
                  </span>
                )}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
};

export default LiveScanner;
