import { motion } from "framer-motion";
import { Shield, Lock, Clock, Bug, Brain, AlertTriangle, CheckCircle, XCircle, Eye } from "lucide-react";

interface AnalysisResult {
  risk_score: number;
  risk_level: "SAFE" | "SUSPICIOUS" | "DANGEROUS";
  verdict_color: string;
  domain_age_days: number | null;
  ssl_valid: boolean | null;
  suspicious_keywords: string[];
  url_flags: string[];
  ml_phishing_probability: number;
  cv_malicious_probability?: number | null;
  cv_prediction?: "BENIGN" | "MALICIOUS";
  cv_model_source?: string;
  reasons: string[];
}

interface ResultsCardProps {
  result: AnalysisResult;
}

const ResultsCard = ({ result }: ResultsCardProps) => {
  const cvProbability =
    typeof result.cv_malicious_probability === "number" ? result.cv_malicious_probability : null;

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
      value: result.ssl_valid === true ? "Valid" : result.ssl_valid === false ? "Invalid" : "Unknown",
      status: result.ssl_valid === true ? "ok" : result.ssl_valid === false ? "bad" : "warn",
    },
    {
      icon: Brain,
      label: "ML Probability",
      value: `${(result.ml_phishing_probability * 100).toFixed(1)}%`,
      status: result.ml_phishing_probability < 0.3 ? "ok" : result.ml_phishing_probability < 0.6 ? "warn" : "bad",
    },
    {
      icon: Eye,
      label: "CV Model",
      value: cvProbability === null ? "Unavailable" : `${(cvProbability * 100).toFixed(1)}%`,
      status: cvProbability === null ? "warn" : cvProbability < 0.3 ? "ok" : cvProbability < 0.6 ? "warn" : "bad",
      note: cvProbability === null ? "Not used in score" : "Included in score",
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
      <div className="grid grid-cols-2 md:grid-cols-4 divide-x divide-border border-b border-border">
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
            {"note" in item && item.note ? (
              <p className="mt-1 text-[11px] text-muted-foreground font-mono">{item.note}</p>
            ) : null}
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

      {/* CV Model Prediction */}
      {result.cv_prediction && (
        <div className="p-4 border-b border-border flex items-center gap-3">
          <Eye className="w-4 h-4 text-primary" />
          <span className="text-xs font-mono text-muted-foreground uppercase tracking-wider">CV Verdict</span>
          <span className={`ml-auto px-3 py-1 rounded-md text-xs font-mono font-semibold border ${
            result.cv_prediction === "BENIGN"
              ? "bg-safe/10 text-safe border-safe/20"
              : "bg-danger/10 text-danger border-danger/20"
          }`}>
            {result.cv_prediction}
          </span>
          {result.cv_model_source && (
            <span className="text-xs font-mono text-muted-foreground">via {result.cv_model_source}</span>
          )}
        </div>
      )}


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
