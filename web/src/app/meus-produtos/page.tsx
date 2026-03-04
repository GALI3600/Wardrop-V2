"use client";

import { useEffect, useMemo } from "react";
import { useRouter } from "next/navigation";
import { useQuery, useQueries, useQueryClient } from "@tanstack/react-query";
import { useAuth } from "@/providers/AuthProvider";
import { getTrackedProducts, getGroupComparison, untrackProduct } from "@/lib/api";
import TrackedProductCard from "@/components/TrackedProductCard";
import type { GroupComparisonOut, ProductOut } from "@/lib/types";

interface DisplayItem {
  id: string;
  name: string | null;
  imageUrl: string | null;
  marketplace: string | null;
  marketplaces?: string[];
  minPrice: number | null;
  maxPrice: number | null;
  currency: string;
  productIds: string[];
}

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
  } = useQuery({
    queryKey: ["tracked-products"],
    queryFn: getTrackedProducts,
    enabled: !!user,
  });

  // Collect unique group IDs
  const groupIds = useMemo(() => {
    if (!trackedProducts) return [];
    const ids = new Set<string>();
    for (const p of trackedProducts) {
      if (p.group_id) ids.add(p.group_id);
    }
    return [...ids];
  }, [trackedProducts]);

  // Fetch group comparisons
  const groupQueries = useQueries({
    queries: groupIds.map((gid) => ({
      queryKey: ["group-comparison", gid],
      queryFn: () => getGroupComparison(gid),
      enabled: !!user,
    })),
  });

  const groupsLoading = groupQueries.some((q) => q.isLoading);

  // Build display items
  const displayItems = useMemo((): DisplayItem[] => {
    if (!trackedProducts) return [];

    const groupDataMap: Record<string, GroupComparisonOut> = {};
    for (let i = 0; i < groupIds.length; i++) {
      const data = groupQueries[i]?.data;
      if (data) groupDataMap[groupIds[i]] = data;
    }

    const seenGroups = new Set<string>();
    const items: DisplayItem[] = [];

    for (const product of trackedProducts) {
      if (product.group_id) {
        if (seenGroups.has(product.group_id)) continue;
        seenGroups.add(product.group_id);

        const groupData = groupDataMap[product.group_id];
        const products: ProductOut[] = groupData
          ? groupData.group.products
          : trackedProducts.filter((p) => p.group_id === product.group_id);

        const prices = products
          .map((p) => Number(p.current_price))
          .filter((v) => v > 0);
        const sorted = [...products].sort(
          (a, b) => (Number(a.current_price) || Infinity) - (Number(b.current_price) || Infinity),
        );
        const cheapest = sorted[0];

        items.push({
          id: cheapest.id,
          name: cheapest.name,
          imageUrl: cheapest.image_url,
          marketplace: cheapest.marketplace,
          marketplaces: products.map((p) => p.marketplace || "—"),
          minPrice: prices.length ? Math.min(...prices) : null,
          maxPrice: prices.length ? Math.max(...prices) : null,
          currency: cheapest.currency || "BRL",
          productIds: products.map((p) => p.id),
        });
      } else {
        items.push({
          id: product.id,
          name: product.name,
          imageUrl: product.image_url,
          marketplace: product.marketplace,
          minPrice: product.current_price,
          maxPrice: product.current_price,
          currency: product.currency || "BRL",
          productIds: [product.id],
        });
      }
    }

    return items;
  }, [trackedProducts, groupIds, groupQueries]);

  async function handleUntrack(item: DisplayItem) {
    for (const pid of item.productIds) {
      await untrackProduct(pid);
    }
    queryClient.invalidateQueries({ queryKey: ["tracked-products"] });
  }

  if (authLoading || !user) return null;

  const loading = productsLoading || groupsLoading;

  return (
    <div>
      <h1 className="text-2xl font-bold text-[var(--text-primary)] mb-6">Meus Produtos</h1>

      {loading ? (
        <p className="text-[var(--text-secondary)]">Carregando...</p>
      ) : displayItems.length === 0 ? (
        <p className="text-[var(--text-secondary)]">
          Nenhum produto acompanhado ainda.
        </p>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {displayItems.map((item) => (
            <TrackedProductCard
              key={item.id}
              id={item.id}
              name={item.name}
              imageUrl={item.imageUrl}
              marketplace={item.marketplace}
              marketplaces={item.marketplaces}
              minPrice={item.minPrice}
              maxPrice={item.maxPrice}
              currency={item.currency}
              onUntrack={() => handleUntrack(item)}
            />
          ))}
        </div>
      )}
    </div>
  );
}
