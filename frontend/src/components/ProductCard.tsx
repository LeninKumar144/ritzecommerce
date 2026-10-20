import { Link } from "react-router-dom";
import type { ProductCard as Product } from "../types/catalog";
import { formatInr } from "../utils/money";

export function ProductCard({ product }: { product: Product }) {
  const discounted = Number(product.discount_percent) > 0;
  return (
    <article className="overflow-hidden rounded-3xl border border-line bg-white">
      <Link to={`/products/${product.slug}`} className="block">
        <div className="aspect-[4/5] bg-[#efe7da]">
          {product.image_url ? (
            <img src={product.image_url} alt="" className="h-full w-full object-cover" />
          ) : (
            <div className="flex h-full items-center justify-center text-sm text-ink/50">No image</div>
          )}
        </div>
        <div className="space-y-1 p-4">
          <p className="text-xs tracking-wide text-moss uppercase">{product.brand}</p>
          <h3 className="text-xl">{product.name}</h3>
          <p className="text-sm">
            <span className="font-medium">{formatInr(product.selling_price)}</span>
            {discounted ? (
              <span className="ml-2 text-ink/50 line-through">{formatInr(product.list_price)}</span>
            ) : null}
          </p>
          <p className="text-xs text-ink/70">{product.in_stock ? "In stock" : "Out of stock"}</p>
        </div>
      </Link>
    </article>
  );
}
