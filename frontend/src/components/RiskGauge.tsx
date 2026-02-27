import { motion } from "framer-motion";

interface RiskGaugeProps {
  score: number;
  level: "SAFE" | "SUSPICIOUS" | "DANGEROUS";
}

const RiskGauge = ({ score, level }: RiskGaugeProps) => {
  const colorMap = {
    SAFE: "text-safe",
    SUSPICIOUS: "text-warning",
    DANGEROUS: "text-danger",
  };

  const bgMap = {
    SAFE: "bg-safe",
    SUSPICIOUS: "bg-warning",
    DANGEROUS: "bg-danger",
  };

  const glowMap = {
    SAFE: "0 0 40px hsl(142 71% 45% / 0.3)",
    SUSPICIOUS: "0 0 40px hsl(45 93% 47% / 0.3)",
    DANGEROUS: "0 0 40px hsl(14 89% 55% / 0.3)",
  };

  const circumference = 2 * Math.PI * 80;
  const strokeDashoffset = circumference - (score / 100) * circumference;

  const strokeColorMap = {
    SAFE: "hsl(142, 71%, 45%)",
    SUSPICIOUS: "hsl(45, 93%, 47%)",
    DANGEROUS: "hsl(14, 89%, 55%)",
  };

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ type: "spring", duration: 0.8 }}
      className="flex flex-col items-center"
    >
      <div className="relative w-48 h-48">
        <svg
          className="w-full h-full -rotate-90"
          viewBox="0 0 180 180"
        >
          <circle
            cx="90"
            cy="90"
            r="80"
            fill="none"
            stroke="hsl(0, 0%, 18%)"
            strokeWidth="8"
          />
          <motion.circle
            cx="90"
            cy="90"
            r="80"
            fill="none"
            stroke={strokeColorMap[level]}
            strokeWidth="8"
            strokeLinecap="round"
            strokeDasharray={circumference}
            initial={{ strokeDashoffset: circumference }}
            animate={{ strokeDashoffset }}
            transition={{ duration: 1.5, ease: "easeOut" }}
          />
        </svg>

        <motion.div
          className="absolute inset-0 flex flex-col items-center justify-center"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
          style={{ textShadow: glowMap[level] }}
        >
          <span className={`text-5xl font-bold font-mono ${colorMap[level]}`}>
            {score}
          </span>
          <span className="text-xs text-muted-foreground font-mono mt-1">/ 100</span>
        </motion.div>
      </div>

      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.8 }}
        className={`mt-4 px-4 py-1.5 rounded-full text-sm font-bold font-mono tracking-wider ${bgMap[level]} ${level === "SUSPICIOUS" ? "text-warning-foreground" : "text-primary-foreground"}`}
      >
        {level}
      </motion.div>
    </motion.div>
  );
};

export default RiskGauge;
