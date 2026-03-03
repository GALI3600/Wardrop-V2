interface BestPriceBadgeProps {
  isAtLowest: boolean;
}

export default function BestPriceBadge({ isAtLowest }: BestPriceBadgeProps) {
  if (!isAtLowest) return null;

  return (
    <span className="inline-block bg-[var(--price-color)]/20 text-[var(--price-color)] text-xs font-semibold px-2 py-0.5 rounded-full">
      Menor preço!
    </span>
  );
}
