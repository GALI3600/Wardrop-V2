import Link from "next/link";
import type { ProductListItem } from "@/lib/types";
import { getMpColor } from "@/lib/marketplaces";
import SparklineChart from "./SparklineChart";
import TrendIndicator from "./TrendIndicator";
import BestPriceBadge from "./BestPriceBadge";
import MarketplaceBadge from "./MarketplaceBadge";

interface ProductCardProps {
  product: ProductListItem;
}

export default function ProductCard({ product }: ProductCardProps) {
  const isGrouped = product.marketplace_prices.length > 1;
  const primaryColor = getMpColor(product.marketplace);

  return (
    <Link href={`/products/${product.id}`} className="block">
      <div className="bg-[var(--bg-card)] rounded-xl overflow-hidden hover:-translate-y-1 hover:shadow-lg transition-all duration-200 cursor-pointer h-full flex flex-col" style={{ boxShadow: "var(--shadow)" }}>
        {product.image_url ? (
          <div className="bg-white p-3 h-44 flex items-center justify-center">
            <img
              src={product.image_url}
              alt={product.name || "Produto"}
              className="max-h-full max-w-full object-contain"
            />
          </div>
        ) : (
          <div className="bg-[var(--bg-input)] h-20" />
        )}
        <div className="p-4 flex flex-col flex-1 gap-2">
          <div className="flex items-center gap-1.5 flex-wrap">
            {isGrouped ? (
              product.marketplace_prices.map((mp) => (
                <MarketplaceBadge key={mp.product_id} marketplace={mp.marketplace} />
              ))
            ) : (
              <MarketplaceBadge marketplace={product.marketplace} />
            )}
            <BestPriceBadge isAtLowest={product.is_at_lowest} />
          </div>
          <p className="text-sm font-medium text-[var(--text-primary)] line-clamp-2 flex-1" title={product.name || ""}>
            {product.name || "Produto"}
          </p>
          <div className="flex items-end justify-between gap-2">
            <div>
              {isGrouped && product.price_max ? (
                <p className="text-xl font-bold text-[var(--price-color)]">
                  R$ {Number(product.current_price || 0).toFixed(2)}
                  <span className="text-base font-normal text-[var(--text-secondary)]"> — </span>
                  <span className="text-base text-[var(--text-primary)]">
                    R$ {Number(product.price_max).toFixed(2)}
                  </span>
                </p>
              ) : (
                <p className="text-xl font-bold text-[var(--price-color)]">
                  R$ {Number(product.current_price || 0).toFixed(2)}
                </p>
              )}
              <TrendIndicator pct={product.price_change_pct} />
            </div>
            {product.sparkline.length >= 2 && (
              <div className="w-20">
                <SparklineChart data={product.sparkline} color={primaryColor} />
              </div>
            )}
          </div>
        </div>
      </div>
    </Link>
  );
}
