interface BestPriceBadgeProps {
  isAtLowest: boolean;
}

export default function BestPriceBadge({ isAtLowest }: BestPriceBadgeProps) {
  if (!isAtLowest) return null;

  return (
    <span className="inline-block bg-emerald-500/20 text-emerald-400 text-xs font-semibold px-2 py-0.5 rounded-full">
      Menor preço!
    </span>
  );
}
