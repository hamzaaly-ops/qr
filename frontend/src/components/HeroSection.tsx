import { motion } from "framer-motion";
import { Shield, ScanLine } from "lucide-react";

const HeroSection = () => {
  return (
    <section className="relative min-h-[60vh] flex items-center justify-center overflow-hidden">
      {/* Grid background */}
      <div className="absolute inset-0 bg-grid opacity-40" />
      
      {/* Radial glow */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] rounded-full bg-primary/5 blur-[120px]" />

      <div className="relative z-10 text-center px-4 max-w-3xl mx-auto">
        <motion.div
          initial={{ scale: 0, rotate: -180 }}
          animate={{ scale: 1, rotate: 0 }}
          transition={{ type: "spring", duration: 1, bounce: 0.3 }}
          className="mx-auto mb-8 w-20 h-20 rounded-2xl bg-primary/10 border border-primary/20 flex items-center justify-center animate-pulse-glow"
        >
          <Shield className="w-10 h-10 text-primary" />
        </motion.div>

        <motion.h1
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3, duration: 0.6 }}
          className="text-5xl md:text-7xl font-bold tracking-tight mb-4"
        >
          QR <span className="text-gradient">Phish</span> Difa
        </motion.h1>

        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5, duration: 0.6 }}
          className="text-lg md:text-xl text-muted-foreground max-w-xl mx-auto mb-2"
        >
          Scan QR codes & URLs for phishing threats instantly.
          <br />
          <span className="font-mono text-sm text-primary/70">AI-powered risk analysis in seconds.</span>
        </motion.p>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.8 }}
          className="flex items-center justify-center gap-6 mt-8 text-sm font-mono text-muted-foreground"
        >
          <span className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-safe" />
            SAFE
          </span>
          <span className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-warning" />
            SUSPICIOUS
          </span>
          <span className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-danger" />
            DANGEROUS
          </span>
        </motion.div>
      </div>
    </section>
  );
};

export default HeroSection;
