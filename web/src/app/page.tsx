"use client";

import { Suspense } from "react";
import { useQuery } from "@tanstack/react-query";
import { useSearchParams, useRouter } from "next/navigation";
import { useCallback, useState } from "react";
import { getProducts, getFilters } from "@/lib/api";
import SearchBar from "@/components/SearchBar";
import FilterSidebar from "@/components/FilterSidebar";
import SortDropdown from "@/components/SortDropdown";
import ProductGrid from "@/components/ProductGrid";
import Pagination from "@/components/Pagination";

function HomeContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const search = searchParams.get("search") || "";
  const marketplace = searchParams.get("marketplace") || "";
  const sortBy = searchParams.get("sort_by") || "created_at";
  const sortOrder = searchParams.get("sort_order") || "desc";
  const page = Number(searchParams.get("page") || "1");
  const minPriceParam = searchParams.get("min_price") || "";
  const maxPriceParam = searchParams.get("max_price") || "";

  const [minPrice, setMinPrice] = useState(minPriceParam);
  const [maxPrice, setMaxPrice] = useState(maxPriceParam);

  const updateParams = useCallback(
    (updates: Record<string, string>) => {
      const params = new URLSearchParams(searchParams.toString());
      for (const [key, value] of Object.entries(updates)) {
        if (value) {
          params.set(key, value);
        } else {
          params.delete(key);
        }
      }
      if (!("page" in updates)) {
        params.delete("page");
      }
      router.push(`?${params.toString()}`);
    },
    [searchParams, router]
  );

  const { data: filtersData } = useQuery({
    queryKey: ["filters"],
    queryFn: getFilters,
  });

  const { data, isLoading } = useQuery({
    queryKey: ["products", search, marketplace, sortBy, sortOrder, page, minPriceParam, maxPriceParam],
    queryFn: () =>
      getProducts({
        search: search || undefined,
        marketplace: marketplace || undefined,
        min_price: minPriceParam ? Number(minPriceParam) : undefined,
        max_price: maxPriceParam ? Number(maxPriceParam) : undefined,
        sort_by: sortBy,
        sort_order: sortOrder,
        page,
        page_size: 24,
      }),
  });

  return (
    <div className="flex flex-col lg:flex-row gap-6">
      <FilterSidebar
        marketplaces={filtersData?.marketplaces || []}
        selectedMarketplace={marketplace}
        onMarketplaceChange={(mp) => updateParams({ marketplace: mp })}
        minPrice={minPrice}
        maxPrice={maxPrice}
        onMinPriceChange={setMinPrice}
        onMaxPriceChange={setMaxPrice}
        onApplyPrice={() =>
          updateParams({ min_price: minPrice, max_price: maxPrice })
        }
      />

      <div className="flex-1 min-w-0">
        <div className="flex flex-col sm:flex-row gap-3 mb-6">
          <div className="flex-1">
            <SearchBar
              value={search}
              onChange={(v) => updateParams({ search: v })}
            />
          </div>
          <SortDropdown
            sortBy={sortBy}
            sortOrder={sortOrder}
            onChange={(sb, so) => updateParams({ sort_by: sb, sort_order: so })}
          />
        </div>

        {filtersData && (
          <p className="text-xs text-slate-500 mb-4">
            {data?.total ?? 0} produto(s) encontrado(s)
          </p>
        )}

        {isLoading ? (
          <div className="text-center py-20 text-slate-500">Carregando...</div>
        ) : (
          <>
            <ProductGrid products={data?.products || []} />
            <Pagination
              page={page}
              totalPages={data?.total_pages || 1}
              onPageChange={(p) => updateParams({ page: String(p) })}
            />
          </>
        )}
      </div>
    </div>
  );
}

export default function HomePage() {
  return (
    <Suspense fallback={<div className="text-center py-20 text-slate-500">Carregando...</div>}>
      <HomeContent />
    </Suspense>
  );
}
