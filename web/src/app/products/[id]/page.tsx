"use client";

import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, ExternalLink, Trash2 } from "lucide-react";
import { getProductHistory, getGroupComparison, getTrackedProducts, untrackProduct } from "@/lib/api";
import { useAuth } from "@/providers/AuthProvider";
import { SinglePriceChart, ComparisonPriceChart } from "@/components/PriceChart";
import ComparisonTable from "@/components/ComparisonTable";
import MarketplaceBadge from "@/components/MarketplaceBadge";
import ConfirmDialog from "@/components/ConfirmDialog";

export default function ProductDetailPage() {
  const params = useParams();
  const router = useRouter();
  const queryClient = useQueryClient();
  const { user } = useAuth();
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

  const { data: trackedProducts } = useQuery({
    queryKey: ["tracked-products"],
    queryFn: getTrackedProducts,
    enabled: !!user,
  });

  const isTracked = trackedProducts?.some((p) => p.id === productId || (groupId && p.group_id === groupId));
  const [showConfirm, setShowConfirm] = useState(false);

  async function handleUntrack() {
    if (groupData) {
      for (const p of groupData.group.products) {
        await untrackProduct(p.id);
      }
    } else {
      await untrackProduct(productId);
    }
    queryClient.invalidateQueries({ queryKey: ["tracked-products"] });
    router.push("/meus-produtos");
  }

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
          <div className="flex items-center gap-3 mt-2 flex-wrap">
            <a
              href={product.url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-sm text-[var(--accent)] hover:opacity-80 transition"
            >
              <ExternalLink className="w-4 h-4" />
              Ver no marketplace
            </a>
            {user && isTracked && (
              <button
                onClick={() => setShowConfirm(true)}
                className="inline-flex items-center gap-1.5 text-sm text-red-500 hover:text-red-600 hover:bg-red-500/10 px-3 py-1.5 rounded-lg transition"
              >
                <Trash2 className="w-4 h-4" />
                Remover acompanhamento
              </button>
            )}
            <ConfirmDialog
              isOpen={showConfirm}
              title="Remover acompanhamento"
              message="Tem certeza que deseja parar de acompanhar este produto?"
              confirmLabel="Remover"
              cancelLabel="Cancelar"
              onConfirm={() => {
                setShowConfirm(false);
                handleUntrack();
              }}
              onCancel={() => setShowConfirm(false)}
            />
          </div>
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
