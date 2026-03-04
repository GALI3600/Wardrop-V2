"use client";

import Link from "next/link";
import { X } from "lucide-react";

const MARKETPLACE_COLORS: Record<string, string> = {
  amazon: "#ff9900",
  mercadolivre: "#ffe600",
  magalu: "#0086ff",
  shopee: "#ee4d2d",
  casasbahia: "#0060a8",
  americanas: "#e60014",
  kabum: "#ff6500",
  aliexpress: "#e43225",
};

function getMpColor(mp: string | null) {
  return MARKETPLACE_COLORS[mp || ""] || "#6366f1";
}

interface TrackedProductCardProps {
  id: string;
  name: string | null;
  imageUrl: string | null;
  marketplace: string | null;
  marketplaces?: string[];
  minPrice: number | null;
  maxPrice: number | null;
  currency: string;
  onUntrack: () => void;
}

export default function TrackedProductCard({
  id,
  name,
  imageUrl,
  marketplace,
  marketplaces,
  minPrice,
  maxPrice,
  currency,
  onUntrack,
}: TrackedProductCardProps) {
  const isGrouped = marketplaces && marketplaces.length > 1;
  const primaryColor = getMpColor(marketplace);

  function handleUntrack(e: React.MouseEvent) {
    e.preventDefault();
    e.stopPropagation();
    onUntrack();
  }

  const priceDisplay = (() => {
    if (minPrice == null) return `${currency} —`;
    const min = Number(minPrice);
    const max = Number(maxPrice);
    if (isGrouped && maxPrice != null && max !== min) {
      return `${currency} ${min.toFixed(2)} — ${max.toFixed(2)}`;
    }
    return `${currency} ${min.toFixed(2)}`;
  })();

  return (
    <Link href={`/products/${id}`} className="block group">
      <div
        className="bg-[var(--bg-card)] rounded-xl overflow-hidden hover:-translate-y-1 hover:shadow-lg transition-all duration-200 cursor-pointer h-full flex flex-col relative"
        style={{ boxShadow: "var(--shadow)" }}
      >
        {/* Untrack button */}
        <button
          onClick={handleUntrack}
          className="absolute top-2 right-2 z-10 p-1 rounded-lg bg-[var(--bg-card)]/80 text-[var(--text-muted)] hover:text-[var(--price-up)] hover:bg-[var(--bg-input)] transition opacity-0 group-hover:opacity-100"
          aria-label="Parar de acompanhar"
        >
          <X className="w-4 h-4" />
        </button>

        {imageUrl ? (
          <div className="bg-white p-3 h-44 flex items-center justify-center">
            <img
              src={imageUrl}
              alt={name || "Produto"}
              className="max-h-full max-w-full object-contain"
            />
          </div>
        ) : (
          <div className="bg-[var(--bg-input)] h-20" />
        )}

        <div className="p-4 flex flex-col flex-1 gap-2">
          <div className="flex items-center gap-1.5 flex-wrap">
            {isGrouped ? (
              marketplaces.map((mp) => {
                const color = getMpColor(mp);
                return (
                  <span
                    key={mp}
                    className="text-[10px] font-semibold uppercase tracking-wider px-1.5 py-0.5 rounded"
                    style={{ background: color + "20", color }}
                  >
                    {mp}
                  </span>
                );
              })
            ) : (
              <span
                className="text-[10px] font-semibold uppercase tracking-wider px-1.5 py-0.5 rounded"
                style={{ background: primaryColor + "20", color: primaryColor }}
              >
                {marketplace || "—"}
              </span>
            )}
          </div>

          <p
            className="text-sm font-medium text-[var(--text-primary)] line-clamp-2 flex-1"
            title={name || ""}
          >
            {name || "Produto"}
          </p>

          <p className="text-xl font-bold text-[var(--price-color)]">{priceDisplay}</p>
        </div>
      </div>
    </Link>
  );
}
