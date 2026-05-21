"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useAuth } from "@/providers/AuthProvider";
import { getTrackedProducts, untrackProduct } from "@/lib/api";
import TrackedProductCard from "@/components/TrackedProductCard";
import type { ProductListItem } from "@/lib/types";

export default function MeusProdutosPage() {
  const { user, isLoading: authLoading } = useAuth();
  const router = useRouter();
  const queryClient = useQueryClient();

  useEffect(() => {
    if (!authLoading && !user) {
      router.replace("/login?redirect=/meus-produtos");
    }
  }, [authLoading, user, router]);

  const {
    data: trackedProducts,
    isLoading: productsLoading,
  } = useQuery<ProductListItem[]>({
    queryKey: ["tracked-products"],
    queryFn: getTrackedProducts,
    enabled: !!user,
  });

  async function handleUntrack(item: ProductListItem) {
    const productIds = item.marketplace_prices.map((mp) => mp.product_id);
    for (const pid of productIds) {
      await untrackProduct(pid);
    }
    queryClient.invalidateQueries({ queryKey: ["tracked-products"] });
  }

  if (authLoading || !user) return null;

  return (
    <div>
      <h1 className="text-2xl font-bold text-[var(--text-primary)] mb-6">Meus Produtos</h1>

      {productsLoading ? (
        <p className="text-[var(--text-secondary)]">Carregando...</p>
      ) : !trackedProducts || trackedProducts.length === 0 ? (
        <p className="text-[var(--text-secondary)]">
          Nenhum produto acompanhado ainda.
        </p>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {trackedProducts.map((item) => (
            <TrackedProductCard
              key={item.id}
              id={item.id}
              name={item.name}
              imageUrl={item.image_url}
              marketplace={item.marketplace}
              marketplaces={
                item.marketplace_prices.length > 1
                  ? item.marketplace_prices.map((mp) => mp.marketplace || "—")
                  : undefined
              }
              minPrice={item.current_price}
              maxPrice={item.price_max}
              currency={item.currency || "BRL"}
              sparkline={item.sparkline}
              priceChangePct={item.price_change_pct}
              isAtLowest={item.is_at_lowest}
              onUntrack={() => handleUntrack(item)}
            />
          ))}
        </div>
      )}
    </div>
  );
}
