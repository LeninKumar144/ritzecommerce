import { useQuery } from "@tanstack/react-query";
import { CategoryCard } from "../components/CategoryCard";
import { ProductCard } from "../components/ProductCard";
import { LoadingSpinner } from "../components/LoadingSpinner";
import { fetchCategories, fetchProducts } from "../services/catalog";
import type { ProductCard as Product } from "../types/catalog";

export function HomePage() {
  const categories = useQuery({ queryKey: ["categories"], queryFn: fetchCategories });
  const featured = useQuery({
    queryKey: ["products", "featured"],
    queryFn: () => fetchProducts({ featured: true, page_size: 4 }),
  });
  const newest = useQuery({
    queryKey: ["products", "newest"],
    queryFn: () => fetchProducts({ sort: "newest", page_size: 4 }),
  });
  const popular = useQuery({
    queryKey: ["products", "popular"],
    queryFn: () => fetchProducts({ sort: "popular", page_size: 4 }),
  });

  if (categories.isLoading || featured.isLoading) return <LoadingSpinner />;

  return (
    <div className="space-y-14">
      <section className="overflow-hidden rounded-[2rem] bg-moss text-paper">
        <div className="grid gap-6 px-6 py-12 md:grid-cols-2 md:px-10">
          <div>
            <p className="text-sm tracking-[0.2em] uppercase">This week</p>
            <h1 className="mt-3 text-5xl leading-tight md:text-6xl">Cloth, colour, and things for the house.</h1>
          </div>
          <p className="self-end text-lg text-paper/85">
            Free delivery on merchandise over ₹999. Prices on this page come from the shop, not from the browser.
          </p>
        </div>
      </section>
      <section>
        <h2 className="text-4xl">Categories</h2>
        <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {categories.data?.map((category) => (
            <CategoryCard key={category.id} category={category} />
          ))}
        </div>
      </section>
      <ProductRail title="Featured" products={featured.data?.items ?? []} />
      <ProductRail title="New arrivals" products={newest.data?.items ?? []} />
      <ProductRail title="Popular" products={popular.data?.items ?? []} />
    </div>
  );
}

function ProductRail({ title, products }: { title: string; products: Product[] }) {
  return (
    <section>
      <h2 className="text-4xl">{title}</h2>
      {products.length === 0 ? <p className="mt-4 text-sm text-ink/70">Nothing in this rail yet.</p> : null}
      <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {products.map((product) => (
          <ProductCard key={product.slug} product={product} />
        ))}
      </div>
    </section>
  );
}
