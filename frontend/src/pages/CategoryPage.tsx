import { useQuery } from "@tanstack/react-query";
import { useParams } from "react-router-dom";
import { ProductCard } from "../components/ProductCard";
import { LoadingSpinner } from "../components/LoadingSpinner";
import { fetchCategory, fetchProducts } from "../services/catalog";

export function CategoryPage() {
  const { slug = "" } = useParams();
  const category = useQuery({ queryKey: ["category", slug], queryFn: () => fetchCategory(slug) });
  const products = useQuery({
    queryKey: ["products", { category: slug }],
    queryFn: () => fetchProducts({ category: slug, page_size: 24 }),
  });

  if (category.isLoading || products.isLoading) return <LoadingSpinner />;
  if (category.isError || !category.data) return <p>That category is not available.</p>;

  return (
    <div>
      <div className="overflow-hidden rounded-[2rem] border border-line bg-white">
        {category.data.image_url ? (
          <img src={category.data.image_url} alt="" className="h-56 w-full object-cover" />
        ) : null}
        <div className="p-6">
          <h1 className="text-5xl">{category.data.name}</h1>
          {category.data.description ? <p className="mt-3 max-w-2xl text-ink/75">{category.data.description}</p> : null}
        </div>
      </div>
      <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {products.data?.items.map((product) => (
          <ProductCard key={product.id} product={product} />
        ))}
      </div>
      {products.data?.items.length === 0 ? <p className="mt-6">No products in this category yet.</p> : null}
    </div>
  );
}
