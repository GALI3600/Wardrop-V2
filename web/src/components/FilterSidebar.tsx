"use client";

import type { MarketplaceOption } from "@/lib/types";

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

interface FilterSidebarProps {
  marketplaces: MarketplaceOption[];
  selectedMarketplace: string;
  onMarketplaceChange: (mp: string) => void;
  minPrice: string;
  maxPrice: string;
  onMinPriceChange: (v: string) => void;
  onMaxPriceChange: (v: string) => void;
  onApplyPrice: () => void;
}

export default function FilterSidebar({
  marketplaces,
  selectedMarketplace,
  onMarketplaceChange,
  minPrice,
  maxPrice,
  onMinPriceChange,
  onMaxPriceChange,
  onApplyPrice,
}: FilterSidebarProps) {
  return (
    <aside className="w-full lg:w-64 shrink-0 space-y-6">
      <div className="bg-[var(--bg-card)] rounded-xl p-4" style={{ boxShadow: "var(--shadow)" }}>
        <h3 className="text-sm font-semibold text-[var(--text-secondary)] mb-3">Marketplace</h3>
        <div className="space-y-2">
          <label className="flex items-center gap-2 cursor-pointer text-sm">
            <input
              type="radio"
              name="marketplace"
              checked={selectedMarketplace === ""}
              onChange={() => onMarketplaceChange("")}
              className="accent-[var(--accent)]"
            />
            <span className="text-[var(--text-primary)]">Todos</span>
          </label>
          {marketplaces.map((mp) => (
            <label key={mp.name} className="flex items-center gap-2 cursor-pointer text-sm">
              <input
                type="radio"
                name="marketplace"
                checked={selectedMarketplace === mp.name}
                onChange={() => onMarketplaceChange(mp.name)}
                className="accent-[var(--accent)]"
              />
              <span
                className="w-2 h-2 rounded-full inline-block"
                style={{ background: MARKETPLACE_COLORS[mp.name] || "#6366f1" }}
              />
              <span className="text-[var(--text-primary)] capitalize">{mp.name}</span>
              <span className="text-[var(--text-muted)] ml-auto">({mp.count})</span>
            </label>
          ))}
        </div>
      </div>

      <div className="bg-[var(--bg-card)] rounded-xl p-4" style={{ boxShadow: "var(--shadow)" }}>
        <h3 className="text-sm font-semibold text-[var(--text-secondary)] mb-3">Faixa de Preço</h3>
        <div className="flex gap-2 items-center">
          <input
            type="number"
            placeholder="Min"
            value={minPrice}
            onChange={(e) => onMinPriceChange(e.target.value)}
            className="w-full bg-[var(--bg-input)] border border-[var(--border-color)] rounded px-2 py-1.5 text-sm text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none focus:ring-1 focus:ring-[var(--accent)]"
          />
          <span className="text-[var(--text-muted)]">—</span>
          <input
            type="number"
            placeholder="Max"
            value={maxPrice}
            onChange={(e) => onMaxPriceChange(e.target.value)}
            className="w-full bg-[var(--bg-input)] border border-[var(--border-color)] rounded px-2 py-1.5 text-sm text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none focus:ring-1 focus:ring-[var(--accent)]"
          />
        </div>
        <button
          onClick={onApplyPrice}
          className="mt-2 w-full bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-white text-sm rounded py-1.5 transition"
        >
          Aplicar
        </button>
      </div>
    </aside>
  );
}
