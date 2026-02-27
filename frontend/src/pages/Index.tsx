import { useState, useRef } from "react";
import { AnimatePresence, motion } from "framer-motion";
import HeroSection from "@/components/HeroSection";
import UploadZone from "@/components/UploadZone";
import UrlInput from "@/components/UrlInput";
import LiveScanner from "@/components/LiveScanner";
import RiskGauge from "@/components/RiskGauge";
import ResultsCard from "@/components/ResultsCard";

const API_BASE = "http://127.0.0.1:8000";

interface AnalysisResult {
  risk_score: number;
  risk_level: "SAFE" | "SUSPICIOUS" | "DANGEROUS";
  verdict_color: string;
  domain_age_days: number | null;
  ssl_valid: boolean;
  suspicious_keywords: string[];
  url_flags: string[];
  ml_phishing_probability: number;
  reasons: string[];
}

const Index = () => {
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [lastAnalyzedUrl, setLastAnalyzedUrl] = useState<string | null>(null);

  const analyzeUrl = async (url: string) => {
    setIsAnalyzing(true);
    setResult(null);
    setError(null);
    setLastAnalyzedUrl(url);
    try {
      const res = await fetch(`${API_BASE}/analyze-url`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url }),
      });
      if (!res.ok) throw new Error("Analysis failed");
      const data = await res.json();
      setResult(data);
    } catch {
      setError("Could not connect to the analysis server. Make sure your backend is running.");
    } finally {
      setIsAnalyzing(false);
    }
  };

  const analyzeQr = async (file: File) => {
    setIsAnalyzing(true);
    setResult(null);
    setError(null);
    try {
      const formData = new FormData();
      formData.append("file", file);
      const res = await fetch(`${API_BASE}/analyze-qr`, {
        method: "POST",
        body: formData,
      });
      if (!res.ok) throw new Error("Analysis failed");
      const data = await res.json();
      setResult(data);
    } catch {
      setError("Could not connect to the analysis server. Make sure your backend is running.");
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div className="min-h-screen bg-background relative">
      <HeroSection />

      <div className="max-w-2xl mx-auto px-4 pb-20 -mt-8 relative z-10 space-y-6">
        {/* Divider label */}
        <div className="flex items-center gap-3">
          <div className="h-px flex-1 bg-border" />
          <span className="text-xs font-mono text-muted-foreground uppercase tracking-widest">
            Analyze
          </span>
          <div className="h-px flex-1 bg-border" />
        </div>

        <UploadZone onFileSelect={analyzeQr} isAnalyzing={isAnalyzing} />

        <div className="flex items-center gap-3">
          <div className="h-px flex-1 bg-border" />
          <span className="text-xs font-mono text-muted-foreground">or scan live</span>
          <div className="h-px flex-1 bg-border" />
        </div>

        <LiveScanner onUrlDetected={analyzeUrl} isAnalyzing={isAnalyzing} lastAnalyzedUrl={lastAnalyzedUrl} />

        <div className="flex items-center gap-3">
          <div className="h-px flex-1 bg-border" />
          <span className="text-xs font-mono text-muted-foreground">or paste URL</span>
          <div className="h-px flex-1 bg-border" />
        </div>

        <UrlInput onSubmit={analyzeUrl} isAnalyzing={isAnalyzing} />

        {/* Error */}
        <AnimatePresence>
          {error && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="p-4 rounded-xl bg-danger/10 border border-danger/20 text-danger text-sm font-mono text-center"
            >
              {error}
            </motion.div>
          )}
        </AnimatePresence>

        {/* Results */}
        <AnimatePresence>
          {result && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="space-y-6 mt-8"
            >
              <RiskGauge score={result.risk_score} level={result.risk_level} />
              <ResultsCard result={result} />
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Footer */}
      <footer className="border-t border-border py-6 text-center">
        <p className="text-xs font-mono text-muted-foreground">
          QR PhishGuard · AI-Powered Phishing Detection
        </p>
      </footer>
    </div>
  );
};

export default Index;
