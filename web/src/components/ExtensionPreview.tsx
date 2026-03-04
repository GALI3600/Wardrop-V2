"use client";

import { useQuery } from "@tanstack/react-query";
import { getProducts } from "@/lib/api";
import { getMpFavicon } from "@/lib/marketplaces";
import { Chrome, Bell, Sun, TrendingDown, TrendingUp, Minus } from "lucide-react";
import type { ProductListItem } from "@/lib/types";

function PopupCard({ product }: { product: ProductListItem }) {
  const favicon = getMpFavicon(product.marketplace);
  return (
    <div className="flex gap-3 p-2.5 rounded-lg bg-[var(--bg-input)] cursor-default">
      {product.image_url ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={product.image_url}
          alt={product.name || ""}
          className="w-10 h-10 rounded-md object-contain bg-white p-0.5 shrink-0"
        />
      ) : (
        <div className="w-10 h-10 rounded-md bg-[var(--bg-hover)] shrink-0" />
      )}
      <div className="flex-1 min-w-0">
        <p className="text-[11px] text-[var(--text-primary)] truncate">
          {product.name || "Produto"}
        </p>
        <div className="flex items-center gap-1.5 mt-0.5">
          {favicon && (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={favicon} alt="" width={12} height={12} />
          )}
          <span className="text-sm font-bold text-[var(--price-color)]">
            R$ {Number(product.current_price || 0).toFixed(2)}
          </span>
        </div>
      </div>
    </div>
  );
}

function TrackingCard({ product }: { product: ProductListItem }) {
  const favicon = getMpFavicon(product.marketplace);
  const pct = product.price_change_pct ?? 0;

  return (
    <div className="flex items-center gap-3 p-2.5 rounded-lg bg-[var(--bg-input)]">
      {product.image_url ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={product.image_url}
          alt={product.name || ""}
          className="w-10 h-10 rounded-md object-contain bg-white p-0.5 shrink-0"
        />
      ) : (
        <div className="w-10 h-10 rounded-md bg-[var(--bg-hover)] shrink-0" />
      )}
      <div className="flex-1 min-w-0">
        <p className="text-[11px] text-[var(--text-primary)] truncate">
          {product.name || "Produto"}
        </p>
        <div className="flex items-center gap-1.5 mt-0.5">
          {favicon && (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={favicon} alt="" width={12} height={12} />
          )}
          <span className="text-xs font-semibold text-[var(--price-color)]">
            R$ {Number(product.current_price || 0).toFixed(2)}
          </span>
        </div>
      </div>
      {pct < -0.5 ? (
        <span className="text-xs font-bold text-[var(--price-down)] flex items-center gap-0.5 shrink-0">
          <TrendingDown className="w-3 h-3" />
          {pct.toFixed(0)}%
        </span>
      ) : pct > 0.5 ? (
        <span className="text-xs font-bold text-[var(--price-up)] flex items-center gap-0.5 shrink-0">
          <TrendingUp className="w-3 h-3" />
          +{pct.toFixed(0)}%
        </span>
      ) : (
        <span className="text-xs font-bold text-[var(--text-muted)] flex items-center gap-0.5 shrink-0">
          <Minus className="w-3 h-3" />
          0%
        </span>
      )}
    </div>
  );
}

export default function ExtensionPreview() {
  const { data } = useQuery({
    queryKey: ["extension-preview"],
    queryFn: () => getProducts({ page_size: 6, sort_by: "created_at", sort_order: "desc" }),
  });

  const products = data?.products || [];
  const popupProducts = products.slice(0, 3);
  const trackingProducts = products.slice(3, 6).length >= 3
    ? products.slice(3, 6)
    : products.slice(0, 3);

  return (
    <div className="grid sm:grid-cols-2 gap-6">
      {/* Popup replica */}
      <div className="rounded-2xl border border-[var(--border-color)] bg-[var(--bg-card)] overflow-hidden">
        <div className="flex items-center gap-2 p-4 pb-0">
          <Chrome className="w-5 h-5 text-[var(--accent)]" />
          <span className="font-semibold text-sm">Popup da extensão</span>
        </div>

        {/* Mini popup frame */}
        <div className="p-4">
          <div
            className="rounded-xl border border-[var(--border-color)] bg-[var(--bg-body)] overflow-hidden"
            style={{ maxWidth: 320, margin: "0 auto" }}
          >
            {/* Popup header */}
            <div className="px-4 py-3 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="w-6 h-6 rounded-md bg-[var(--accent)] flex items-center justify-center text-white text-xs font-bold">
                  W
                </div>
                <span className="text-sm font-bold text-[var(--text-primary)]">Wardrop</span>
                <span className="text-[10px] text-[var(--text-muted)]">Price Tracker</span>
              </div>
              <Sun className="w-4 h-4 text-[var(--text-muted)]" />
            </div>

            {/* User info */}
            <div className="px-4 py-2 flex items-center justify-between border-t border-[var(--border-color)]">
              <span className="text-[11px] text-[var(--text-secondary)]">user@email.com</span>
              <span className="text-[11px] text-[var(--accent)] cursor-default">Sair</span>
            </div>

            {/* Tracked list */}
            <div className="px-4 pt-3 pb-1">
              <div className="flex items-center gap-2 mb-2">
                <span className="text-xs font-semibold text-[var(--text-secondary)]">Acompanhando</span>
                <span className="text-[10px] font-semibold bg-[var(--accent)] text-white px-1.5 py-0.5 rounded-full">
                  {popupProducts.length}
                </span>
              </div>
            </div>

            <div className="px-4 pb-3 space-y-2">
              {popupProducts.length > 0 ? (
                popupProducts.map((p) => <PopupCard key={p.id} product={p} />)
              ) : (
                <>
                  <div className="h-14 rounded-lg bg-[var(--bg-input)] animate-pulse" />
                  <div className="h-14 rounded-lg bg-[var(--bg-input)] animate-pulse" />
                  <div className="h-14 rounded-lg bg-[var(--bg-input)] animate-pulse" />
                </>
              )}
            </div>

            {/* Footer */}
            <div className="px-4 pb-3">
              <div className="w-full py-2 rounded-lg bg-[var(--accent)] text-white text-xs font-medium text-center">
                Dashboard
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Tracking in action */}
      <div className="rounded-2xl border border-[var(--border-color)] bg-[var(--bg-card)] overflow-hidden">
        <div className="flex items-center gap-2 p-4 pb-0">
          <Bell className="w-5 h-5 text-[var(--accent)]" />
          <span className="font-semibold text-sm">Rastreamento em acao</span>
        </div>

        <div className="p-4">
          <div
            className="rounded-xl border border-[var(--border-color)] bg-[var(--bg-body)] overflow-hidden"
            style={{ maxWidth: 320, margin: "0 auto" }}
          >
            {/* Simulated page with FAB */}
            <div className="relative px-4 py-3">
              {/* Fake page content */}
              <div className="space-y-2 mb-3">
                <div className="h-2.5 rounded bg-[var(--bg-input)] w-2/3" />
                <div className="h-2 rounded bg-[var(--bg-input)] w-full" />
                <div className="h-2 rounded bg-[var(--bg-input)] w-5/6" />
              </div>

              {/* Product cards with real data and price changes */}
              <div className="space-y-2">
                {trackingProducts.length > 0 ? (
                  trackingProducts.map((p) => <TrackingCard key={p.id} product={p} />)
                ) : (
                  <>
                    <div className="h-14 rounded-lg bg-[var(--bg-input)] animate-pulse" />
                    <div className="h-14 rounded-lg bg-[var(--bg-input)] animate-pulse" />
                    <div className="h-14 rounded-lg bg-[var(--bg-input)] animate-pulse" />
                  </>
                )}
              </div>

              {/* FAB */}
              <div className="flex justify-end mt-3">
                <div className="w-10 h-10 rounded-full bg-[#16a34a] flex items-center justify-center text-white text-sm font-bold shadow-md">
                  W
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
