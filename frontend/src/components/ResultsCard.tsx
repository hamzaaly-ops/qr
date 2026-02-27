import { motion } from "framer-motion";
import { Shield, Lock, Clock, Bug, Brain, AlertTriangle, CheckCircle, XCircle } from "lucide-react";

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

interface ResultsCardProps {
  result: AnalysisResult;
}

const ResultsCard = ({ result }: ResultsCardProps) => {
  const items = [
    {
      icon: Clock,
      label: "Domain Age",
      value: result.domain_age_days !== null ? `${result.domain_age_days} days` : "Unknown",
      status: result.domain_age_days !== null && result.domain_age_days > 365 ? "ok" : "warn",
    },
    {
      icon: Lock,
      label: "SSL Certificate",
      value: result.ssl_valid ? "Valid" : "Invalid",
      status: result.ssl_valid ? "ok" : "bad",
    },
    {
      icon: Brain,
      label: "ML Probability",
      value: `${(result.ml_phishing_probability * 100).toFixed(1)}%`,
      status: result.ml_phishing_probability < 0.3 ? "ok" : result.ml_phishing_probability < 0.6 ? "warn" : "bad",
    },
  ];

  const statusIcon = {
    ok: <CheckCircle className="w-4 h-4 text-safe" />,
    warn: <AlertTriangle className="w-4 h-4 text-warning" />,
    bad: <XCircle className="w-4 h-4 text-danger" />,
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.3, duration: 0.5 }}
      className="bg-card border border-border rounded-2xl overflow-hidden"
    >
      {/* Metrics grid */}
      <div className="grid grid-cols-3 divide-x divide-border border-b border-border">
        {items.map((item, i) => (
          <motion.div
            key={item.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 + i * 0.1 }}
            className="p-4 text-center"
          >
            <div className="flex items-center justify-center gap-2 mb-2">
              <item.icon className="w-4 h-4 text-muted-foreground" />
              <span className="text-xs text-muted-foreground font-mono uppercase tracking-wider">
                {item.label}
              </span>
            </div>
            <div className="flex items-center justify-center gap-2">
              {statusIcon[item.status as keyof typeof statusIcon]}
              <span className="text-sm font-semibold text-foreground">{item.value}</span>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Flags */}
      {(result.suspicious_keywords.length > 0 || result.url_flags.length > 0) && (
        <div className="p-4 border-b border-border">
          <div className="flex items-center gap-2 mb-3">
            <Bug className="w-4 h-4 text-danger" />
            <span className="text-xs font-mono text-muted-foreground uppercase tracking-wider">
              Detected Flags
            </span>
          </div>
          <div className="flex flex-wrap gap-2">
            {[...result.suspicious_keywords, ...result.url_flags].map((flag, i) => (
              <motion.span
                key={i}
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.6 + i * 0.05 }}
                className="px-2.5 py-1 rounded-md bg-danger/10 text-danger text-xs font-mono border border-danger/20"
              >
                {flag}
              </motion.span>
            ))}
          </div>
        </div>
      )}

      {/* Reasons */}
      {result.reasons.length > 0 && (
        <div className="p-4">
          <div className="flex items-center gap-2 mb-3">
            <Shield className="w-4 h-4 text-primary" />
            <span className="text-xs font-mono text-muted-foreground uppercase tracking-wider">
              Analysis Reasons
            </span>
          </div>
          <ul className="space-y-2">
            {result.reasons.map((reason, i) => (
              <motion.li
                key={i}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.7 + i * 0.1 }}
                className="text-sm text-secondary-foreground flex items-start gap-2"
              >
                <span className="text-primary mt-1">›</span>
                {reason}
              </motion.li>
            ))}
          </ul>
        </div>
      )}
    </motion.div>
  );
};

export default ResultsCard;
