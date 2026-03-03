import { TrendingDown, TrendingUp, Minus } from "lucide-react";

interface TrendIndicatorProps {
  pct: number | null;
}

export default function TrendIndicator({ pct }: TrendIndicatorProps) {
  if (pct === null || pct === undefined) return null;

  if (Math.abs(pct) < 0.5) {
    return (
      <span className="inline-flex items-center gap-1 text-xs text-slate-400">
        <Minus className="w-3 h-3" />
        {pct.toFixed(1)}%
      </span>
    );
  }

  if (pct < 0) {
    return (
      <span className="inline-flex items-center gap-1 text-xs text-emerald-400">
        <TrendingDown className="w-3 h-3" />
        {pct.toFixed(1)}%
      </span>
    );
  }

  return (
    <span className="inline-flex items-center gap-1 text-xs text-red-400">
      <TrendingUp className="w-3 h-3" />
      +{pct.toFixed(1)}%
    </span>
  );
}
