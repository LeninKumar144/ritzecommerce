import { useQuery } from "@tanstack/react-query";
import { useSearchParams } from "react-router-dom";
import { FilterPanel } from "../components/FilterPanel";
import { LoadingSpinner } from "../components/LoadingSpinner";
import { Pagination } from "../components/Pagination";
import { ProductCard } from "../components/ProductCard";
import { fetchBrands, fetchProducts } from "../services/catalog";

export function ProductListPage() {
  const [params, setParams] = useSearchParams();
  const search = params.get("search") ?? "";
  const category = params.get("category") ?? undefined;
  const brand = params.get("brand") ?? "";
  const minPrice = params.get("min_price") ?? "";
  const maxPrice = params.get("max_price") ?? "";
  const inStock = params.get("in_stock") === "true";
  const sort = params.get("sort") ?? "newest";
  const page = Number(params.get("page") ?? "1");

  const products = useQuery({
    queryKey: ["products", { search, category, brand, minPrice, maxPrice, inStock, sort, page }],
    queryFn: () =>
      fetchProducts({
        search: search || undefined,
        category,
        brand: brand || undefined,
        min_price: minPrice || undefined,
        max_price: maxPrice || undefined,
        in_stock: inStock ? true : undefined,
        sort: sort as "newest",
        page,
        page_size: 8,
      }),
  });
  const brands = useQuery({ queryKey: ["brands"], queryFn: fetchBrands });

  function update(next: { brand?: string; minPrice?: string; maxPrice?: string; inStock?: boolean; sort?: string }) {
    const updated = new URLSearchParams(params);
    if (next.brand !== undefined) {
      if (next.brand) updated.set("brand", next.brand);
      else updated.delete("brand");
    }
    if (next.minPrice !== undefined) {
      if (next.minPrice) updated.set("min_price", next.minPrice);
      else updated.delete("min_price");
    }
    if (next.maxPrice !== undefined) {
      if (next.maxPrice) updated.set("max_price", next.maxPrice);
      else updated.delete("max_price");
    }
    if (next.inStock !== undefined) {
      if (next.inStock) updated.set("in_stock", "true");
      else updated.delete("in_stock");
    }
    if (next.sort) updated.set("sort", next.sort);
    updated.delete("page");
    setParams(updated);
  }

  return (
    <div>
      <h1 className="text-5xl">{search ? `Results for “${search}”` : "Shop"}</h1>
      <div className="mt-8 grid gap-6 lg:grid-cols-[240px_1fr]">
        <FilterPanel
          brands={brands.data ?? []}
          brand={brand}
          minPrice={minPrice}
          maxPrice={maxPrice}
          inStock={inStock}
          sort={sort}
          onChange={update}
        />
        <div>
          {products.isLoading ? <LoadingSpinner /> : null}
          {products.isError ? <p>The product list could not be loaded.</p> : null}
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
            {products.data?.items.map((product) => (
              <ProductCard key={product.id} product={product} />
            ))}
          </div>
          {products.data && products.data.items.length === 0 ? <p className="mt-6">No matching products.</p> : null}
          <Pagination
            page={products.data?.page ?? page}
            pageSize={products.data?.page_size ?? 8}
            total={products.data?.total ?? 0}
            onPage={(nextPage) => {
              const updated = new URLSearchParams(params);
              updated.set("page", String(nextPage));
              setParams(updated);
            }}
          />
        </div>
      </div>
    </div>
  );
}
