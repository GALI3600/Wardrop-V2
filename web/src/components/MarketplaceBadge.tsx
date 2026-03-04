import { getMpColor, getMpFavicon } from "@/lib/marketplaces";

interface MarketplaceBadgeProps {
  marketplace: string | null;
}

export default function MarketplaceBadge({ marketplace }: MarketplaceBadgeProps) {
  const color = getMpColor(marketplace);
  const favicon = getMpFavicon(marketplace);
  const label = marketplace || "—";

  return (
    <span
      className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded w-fit"
      style={{ background: color + "20" }}
      title={label}
    >
      {favicon ? (
        <img src={favicon} alt={label} className="w-4 h-4" draggable={false} />
      ) : (
        <span
          className="text-[10px] font-semibold uppercase tracking-wider"
          style={{ color }}
        >
          {label}
        </span>
      )}
    </span>
  );
}
