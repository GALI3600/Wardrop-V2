"use client";

import { useQuery } from "@tanstack/react-query";
import { getProducts, getFilters } from "@/lib/api";
import { getMpFavicon, getMpColor, MARKETPLACE_COLORS } from "@/lib/marketplaces";
import {
  TrendingDown,
  TrendingUp,
  Search,
  ChevronDown,
  Minus,
} from "lucide-react";
import type { ProductListItem } from "@/lib/types";

function MiniSparkline({ data, color }: { data: { price: number }[]; color: string }) {
  if (data.length < 2) return null;
  const prices = data.map((d) => d.price);
  const min = Math.min(...prices);
  const max = Math.max(...prices);
  const range = max - min || 1;
  const h = 32;
  const w = 80;
  const points = prices
    .map((v, i) => `${(i / (prices.length - 1)) * w},${h - ((v - min) / range) * h}`)
    .join(" ");
  return (
    <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`} className="overflow-visible">
      <polyline
        points={points}
        fill="none"
        stroke={color}
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function ProductCardMini({ product }: { product: ProductListItem }) {
  const favicon = getMpFavicon(product.marketplace);
  const color = getMpColor(product.marketplace);
  const pct = product.price_change_pct ?? 0;

  return (
    <div
      className="bg-[var(--bg-card)] rounded-xl overflow-hidden flex flex-col"
      style={{ boxShadow: "var(--shadow)" }}
    >
      {product.image_url ? (
        <div className="bg-white p-2 h-32 flex items-center justify-center">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={product.image_url}
            alt={product.name || "Produto"}
            className="max-h-full max-w-full object-contain"
          />
        </div>
      ) : (
        <div className="bg-[var(--bg-input)] h-20" />
      )}
      <div className="p-3 flex flex-col flex-1 gap-1.5">
        <div className="flex items-center gap-1.5">
          {favicon && (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={favicon} alt={product.marketplace || ""} width={16} height={16} />
          )}
          {product.is_at_lowest && (
            <span className="text-[9px] font-medium text-[var(--price-down)] bg-[var(--price-down)]/10 px-1.5 py-0.5 rounded">
              Menor preço!
            </span>
          )}
        </div>
        <p className="text-xs font-medium text-[var(--text-primary)] line-clamp-2 flex-1">
          {product.name || "Produto"}
        </p>
        <div className="flex items-end justify-between gap-2">
          <div>
            <p className="text-base font-bold text-[var(--price-color)]">
              R$ {Number(product.current_price || 0).toFixed(2)}
            </p>
            {pct < -0.5 ? (
              <span className="text-[10px] text-[var(--price-down)] flex items-center gap-0.5">
                <TrendingDown className="w-3 h-3" />
                {pct.toFixed(1)}%
              </span>
            ) : pct > 0.5 ? (
              <span className="text-[10px] text-[var(--price-up)] flex items-center gap-0.5">
                <TrendingUp className="w-3 h-3" />
                +{pct.toFixed(1)}%
              </span>
            ) : (
              <span className="text-[10px] text-[var(--text-muted)] flex items-center gap-0.5">
                <Minus className="w-3 h-3" />
                0.0%
              </span>
            )}
          </div>
          {product.sparkline.length >= 2 && (
            <MiniSparkline data={product.sparkline} color={color} />
          )}
        </div>
      </div>
    </div>
  );
}

export default function DashboardShowcase() {
  const { data: productsData } = useQuery({
    queryKey: ["showcase-products"],
    queryFn: () => getProducts({ page_size: 6, sort_by: "created_at", sort_order: "desc" }),
  });

  const { data: filtersData } = useQuery({
    queryKey: ["showcase-filters"],
    queryFn: getFilters,
  });

  const products = productsData?.products || [];
  const marketplaces = filtersData?.marketplaces || [];
  const total = filtersData?.total_products ?? 0;

  return (
    <div className="rounded-2xl border border-[var(--border-color)] overflow-hidden shadow-lg bg-[var(--bg-body)]">
      {/* Browser chrome */}
      <div className="flex items-center gap-2 px-4 py-3 border-b border-[var(--border-color)] bg-[var(--bg-input)]">
        <span className="w-3 h-3 rounded-full bg-[#ef4444]" />
        <span className="w-3 h-3 rounded-full bg-[#eab308]" />
        <span className="w-3 h-3 rounded-full bg-[#22c55e]" />
        <span className="ml-4 text-xs text-[var(--text-muted)]">
          wardrop.app/produtos
        </span>
      </div>

      {/* Dashboard content */}
      <div className="p-4 sm:p-6">
        <div className="flex flex-col lg:flex-row gap-4">
          {/* Sidebar */}
          <aside className="w-full lg:w-52 shrink-0 space-y-4 hidden sm:block">
            <div className="bg-[var(--bg-card)] rounded-xl p-3" style={{ boxShadow: "var(--shadow)" }}>
              <h3 className="text-xs font-semibold text-[var(--text-secondary)] mb-2">Marketplace</h3>
              <div className="space-y-1.5">
                <label className="flex items-center gap-2 text-xs cursor-default">
                  <span className="w-3 h-3 rounded-full border-2 border-[var(--accent)] flex items-center justify-center">
                    <span className="w-1.5 h-1.5 rounded-full bg-[var(--accent)]" />
                  </span>
                  <span className="text-[var(--text-primary)]">Todos</span>
                </label>
                {marketplaces.map((mp) => {
                  const favicon = getMpFavicon(mp.name);
                  return (
                    <label key={mp.name} className="flex items-center gap-2 text-xs cursor-default">
                      <span className="w-3 h-3 rounded-full border-2 border-[var(--border-color)]" />
                      {favicon ? (
                        // eslint-disable-next-line @next/next/no-img-element
                        <img src={favicon} alt={mp.name} width={14} height={14} />
                      ) : (
                        <span
                          className="w-2 h-2 rounded-full inline-block"
                          style={{ background: MARKETPLACE_COLORS[mp.name] || "#6366f1" }}
                        />
                      )}
                      <span className="text-[var(--text-primary)] capitalize">{mp.name}</span>
                      <span className="text-[var(--text-muted)] ml-auto">({mp.count})</span>
                    </label>
                  );
                })}
              </div>
            </div>
            <div className="bg-[var(--bg-card)] rounded-xl p-3" style={{ boxShadow: "var(--shadow)" }}>
              <h3 className="text-xs font-semibold text-[var(--text-secondary)] mb-2">Faixa de Preço</h3>
              <div className="flex gap-1.5 items-center">
                <div className="w-full bg-[var(--bg-input)] border border-[var(--border-color)] rounded px-2 py-1 text-xs text-[var(--text-muted)]">
                  Min
                </div>
                <span className="text-[var(--text-muted)] text-xs">—</span>
                <div className="w-full bg-[var(--bg-input)] border border-[var(--border-color)] rounded px-2 py-1 text-xs text-[var(--text-muted)]">
                  Max
                </div>
              </div>
              <div className="mt-2 w-full bg-[var(--accent)] text-white text-xs rounded py-1 text-center">
                Aplicar
              </div>
            </div>
          </aside>

          {/* Main content */}
          <div className="flex-1 min-w-0">
            {/* Toolbar */}
            <div className="flex flex-col sm:flex-row gap-2 mb-4">
              <div className="flex-1 relative">
                <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-[var(--text-muted)]" />
                <div className="w-full bg-[var(--bg-card)] border border-[var(--border-color)] rounded-lg pl-8 pr-3 py-2 text-xs text-[var(--text-muted)]">
                  Buscar produtos...
                </div>
              </div>
              <div className="bg-[var(--bg-card)] border border-[var(--border-color)] rounded-lg px-3 py-2 text-xs text-[var(--text-primary)] flex items-center gap-1 whitespace-nowrap">
                Mais recentes
                <ChevronDown className="w-3 h-3 text-[var(--text-muted)]" />
              </div>
            </div>

            <p className="text-[10px] text-[var(--text-muted)] mb-3">
              {total} produto(s) encontrado(s)
            </p>

            {/* Product grid */}
            {products.length > 0 ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                {products.map((product) => (
                  <ProductCardMini key={product.id} product={product} />
                ))}
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                {[...Array(6)].map((_, i) => (
                  <div
                    key={i}
                    className="bg-[var(--bg-card)] rounded-xl overflow-hidden"
                    style={{ boxShadow: "var(--shadow)" }}
                  >
                    <div className="bg-[var(--bg-input)] h-32 animate-pulse" />
                    <div className="p-3 space-y-2">
                      <div className="h-3 rounded bg-[var(--bg-input)] w-1/3 animate-pulse" />
                      <div className="h-3 rounded bg-[var(--bg-input)] w-full animate-pulse" />
                      <div className="h-4 rounded bg-[var(--bg-input)] w-1/2 animate-pulse" />
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
