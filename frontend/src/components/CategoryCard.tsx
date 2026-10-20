import { Link } from "react-router-dom";
import type { Category } from "../types/catalog";

export function CategoryCard({ category }: { category: Category }) {
  return (
    <Link
      to={`/categories/${category.slug}`}
      className="group overflow-hidden rounded-3xl border border-line bg-white"
    >
      <div className="aspect-[5/3] bg-moss/15">
        {category.image_url ? (
          <img src={category.image_url} alt="" className="h-full w-full object-cover" />
        ) : (
          <div className="flex h-full items-end p-4 font-display text-3xl">{category.name}</div>
        )}
      </div>
      <div className="p-4">
        <h3 className="text-2xl group-hover:text-clay">{category.name}</h3>
        {category.description ? <p className="mt-1 text-sm text-ink/70">{category.description}</p> : null}
      </div>
    </Link>
  );
}
