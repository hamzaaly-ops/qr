import { useState } from "react";
import { motion } from "framer-motion";
import { Link, ArrowRight, Loader2 } from "lucide-react";

interface UrlInputProps {
  onSubmit: (url: string) => void;
  isAnalyzing: boolean;
}

const UrlInput = ({ onSubmit, isAnalyzing }: UrlInputProps) => {
  const [url, setUrl] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (url.trim()) onSubmit(url.trim());
  };

  return (
    <motion.form
      onSubmit={handleSubmit}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.3 }}
      className="relative"
    >
      <div className="flex items-center gap-3 bg-card border border-border rounded-xl px-4 py-3 focus-within:border-primary/50 focus-within:glow-primary transition-all duration-300">
        <Link className="w-5 h-5 text-muted-foreground shrink-0" />
        <input
          type="url"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://suspicious-url.com/login"
          className="flex-1 bg-transparent text-foreground placeholder:text-muted-foreground font-mono text-sm outline-none"
          disabled={isAnalyzing}
        />
        <button
          type="submit"
          disabled={!url.trim() || isAnalyzing}
          className="shrink-0 w-10 h-10 rounded-lg bg-primary text-primary-foreground flex items-center justify-center disabled:opacity-40 disabled:cursor-not-allowed hover:bg-primary/90 transition-colors"
        >
          {isAnalyzing ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : (
            <ArrowRight className="w-5 h-5" />
          )}
        </button>
      </div>
    </motion.form>
  );
};

export default UrlInput;
