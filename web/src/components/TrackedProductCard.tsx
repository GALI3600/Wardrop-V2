"use client";

import { useState } from "react";
import Link from "next/link";
import { BellOff } from "lucide-react";
import MarketplaceBadge from "./MarketplaceBadge";
import ConfirmDialog from "./ConfirmDialog";

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
  const [showConfirm, setShowConfirm] = useState(false);
  const isGrouped = marketplaces && marketplaces.length > 1;

  function handleUntrackClick(e: React.MouseEvent) {
    e.preventDefault();
    e.stopPropagation();
    setShowConfirm(true);
  }

  function handleConfirmUntrack() {
    setShowConfirm(false);
    onUntrack();
  }

  function handleCancelUntrack() {
    setShowConfirm(false);
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
    <>
      {/* Confirmation dialog - outside Link to avoid hover conflicts */}
      <ConfirmDialog
        isOpen={showConfirm}
        title="Remover acompanhamento"
        message="Tem certeza que deseja parar de acompanhar este produto?"
        confirmLabel="Remover"
        cancelLabel="Cancelar"
        onConfirm={handleConfirmUntrack}
        onCancel={handleCancelUntrack}
      />

      <Link href={`/products/${id}`} className="block group">
        <div
          className="bg-[var(--bg-card)] rounded-xl overflow-hidden hover:-translate-y-1 hover:shadow-lg transition-all duration-200 cursor-pointer h-full flex flex-col relative"
          style={{ boxShadow: "var(--shadow)" }}
        >
          {/* Untrack button */}
          <button
            onClick={handleUntrackClick}
            className="absolute top-2 right-2 z-10 p-1.5 rounded-lg bg-[var(--bg-input)] text-[var(--text-muted)] hover:text-[var(--price-up)] hover:bg-[var(--bg-card)] border border-[var(--border-color)] transition"
            aria-label="Parar de acompanhar"
          >
            <BellOff className="w-4 h-4" />
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
              marketplaces.map((mp) => (
                <MarketplaceBadge key={mp} marketplace={mp} />
              ))
            ) : (
              <MarketplaceBadge marketplace={marketplace} />
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
    </>
  );
}
