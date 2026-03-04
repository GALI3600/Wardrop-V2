"use client";

import { useQuery } from "@tanstack/react-query";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, ExternalLink } from "lucide-react";
import { getProductHistory, getGroupComparison } from "@/lib/api";
import { SinglePriceChart, ComparisonPriceChart } from "@/components/PriceChart";
import ComparisonTable from "@/components/ComparisonTable";
import MarketplaceBadge from "@/components/MarketplaceBadge";

export default function ProductDetailPage() {
  const params = useParams();
  const router = useRouter();
  const productId = params.id as string;

  const { data, isLoading } = useQuery({
    queryKey: ["product-history", productId],
    queryFn: () => getProductHistory(productId),
  });

  const groupId = data?.product.group_id;
  const { data: groupData } = useQuery({
    queryKey: ["group-comparison", groupId],
    queryFn: () => getGroupComparison(groupId!),
    enabled: !!groupId,
  });

  if (isLoading) {
    return <div className="text-center py-20 text-[var(--text-muted)]">Carregando...</div>;
  }

  if (!data) {
    return <div className="text-center py-20 text-[var(--text-muted)]">Produto não encontrado.</div>;
  }

  const { product, history } = data;
  return (
    <div>
      <button
        onClick={() => router.back()}
        className="inline-flex items-center gap-1 text-[var(--accent)] hover:opacity-80 text-sm mb-6 transition"
      >
        <ArrowLeft className="w-4 h-4" />
        Voltar
      </button>

      {/* Product info */}
      <div className="bg-[var(--bg-card)] rounded-xl p-6 flex flex-col md:flex-row gap-6" style={{ boxShadow: "var(--shadow)" }}>
        {product.image_url && (
          <div className="bg-white rounded-lg p-4 flex items-center justify-center w-full md:w-64 h-64 shrink-0">
            <img
              src={product.image_url}
              alt={product.name || "Produto"}
              className="max-h-full max-w-full object-contain"
            />
          </div>
        )}
        <div className="flex flex-col gap-3 flex-1">
          <MarketplaceBadge marketplace={product.marketplace} />
          <h1 className="text-xl font-bold text-[var(--text-primary)]">
            {product.name || "Produto"}
          </h1>
          <p className="text-3xl font-bold text-[var(--price-color)]">
            {product.currency} {Number(product.current_price || 0).toFixed(2)}
          </p>
          {product.seller && (
            <p className="text-sm text-[var(--text-secondary)]">
              Vendedor: {product.seller}
            </p>
          )}
          <a
            href={product.url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 text-sm text-[var(--accent)] hover:opacity-80 mt-2 w-fit transition"
          >
            <ExternalLink className="w-4 h-4" />
            Ver no marketplace
          </a>
        </div>
      </div>

      {/* Comparison table + multi-marketplace chart (if grouped) */}
      {groupData && (
        <>
          <ComparisonTable
            products={groupData.group.products}
            priceHistories={groupData.price_histories}
          />
          <ComparisonPriceChart priceHistories={groupData.price_histories} />
        </>
      )}

      {/* Single price chart (only if not grouped) */}
      {!groupId && history.length > 0 && (
        <SinglePriceChart history={history} />
      )}
    </div>
  );
}
