import type { ProductListItem } from "@/lib/types";
import ProductCard from "./ProductCard";

interface ProductGridProps {
  products: ProductListItem[];
}

export default function ProductGrid({ products }: ProductGridProps) {
  if (products.length === 0) {
    return (
      <div className="text-center py-20 text-slate-500">
        Nenhum produto encontrado.
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      {products.map((product) => (
        <ProductCard key={product.id} product={product} />
      ))}
    </div>
  );
}
