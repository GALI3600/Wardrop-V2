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
      <div className="bg-slate-800 rounded-xl p-4">
        <h3 className="text-sm font-semibold text-slate-300 mb-3">Marketplace</h3>
        <div className="space-y-2">
          <label className="flex items-center gap-2 cursor-pointer text-sm">
            <input
              type="radio"
              name="marketplace"
              checked={selectedMarketplace === ""}
              onChange={() => onMarketplaceChange("")}
              className="accent-indigo-500"
            />
            <span className="text-slate-300">Todos</span>
          </label>
          {marketplaces.map((mp) => (
            <label key={mp.name} className="flex items-center gap-2 cursor-pointer text-sm">
              <input
                type="radio"
                name="marketplace"
                checked={selectedMarketplace === mp.name}
                onChange={() => onMarketplaceChange(mp.name)}
                className="accent-indigo-500"
              />
              <span
                className="w-2 h-2 rounded-full inline-block"
                style={{ background: MARKETPLACE_COLORS[mp.name] || "#6366f1" }}
              />
              <span className="text-slate-300 capitalize">{mp.name}</span>
              <span className="text-slate-500 ml-auto">({mp.count})</span>
            </label>
          ))}
        </div>
      </div>

      <div className="bg-slate-800 rounded-xl p-4">
        <h3 className="text-sm font-semibold text-slate-300 mb-3">Faixa de Preço</h3>
        <div className="flex gap-2 items-center">
          <input
            type="number"
            placeholder="Min"
            value={minPrice}
            onChange={(e) => onMinPriceChange(e.target.value)}
            className="w-full bg-slate-700 border border-slate-600 rounded px-2 py-1.5 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          />
          <span className="text-slate-500">—</span>
          <input
            type="number"
            placeholder="Max"
            value={maxPrice}
            onChange={(e) => onMaxPriceChange(e.target.value)}
            className="w-full bg-slate-700 border border-slate-600 rounded px-2 py-1.5 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          />
        </div>
        <button
          onClick={onApplyPrice}
          className="mt-2 w-full bg-indigo-600 hover:bg-indigo-500 text-white text-sm rounded py-1.5 transition"
        >
          Aplicar
        </button>
      </div>
    </aside>
  );
}
