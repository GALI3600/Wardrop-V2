import { TrendingDown, TrendingUp, Minus } from "lucide-react";

interface TrendIndicatorProps {
  pct: number | null;
}

export default function TrendIndicator({ pct }: TrendIndicatorProps) {
  if (pct === null || pct === undefined) return null;

  if (Math.abs(pct) < 0.5) {
    return (
      <span className="inline-flex items-center gap-1 text-xs text-[var(--text-secondary)]">
        <Minus className="w-3 h-3" />
        {pct.toFixed(1)}%
      </span>
    );
  }

  if (pct < 0) {
    return (
      <span className="inline-flex items-center gap-1 text-xs text-[var(--price-down)]">
        <TrendingDown className="w-3 h-3" />
        {pct.toFixed(1)}%
      </span>
    );
  }

  return (
    <span className="inline-flex items-center gap-1 text-xs text-[var(--price-up)]">
      <TrendingUp className="w-3 h-3" />
      +{pct.toFixed(1)}%
    </span>
  );
}
