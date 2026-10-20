type Props = {
  brands: string[];
  brand: string;
  minPrice: string;
  maxPrice: string;
  inStock: boolean;
  sort: string;
  onChange: (next: { brand?: string; minPrice?: string; maxPrice?: string; inStock?: boolean; sort?: string }) => void;
};

export function FilterPanel({ brands, brand, minPrice, maxPrice, inStock, sort, onChange }: Props) {
  return (
    <form className="space-y-4 rounded-3xl border border-line bg-white p-4" aria-label="Product filters">
      <label className="block text-sm">
        Brand
        <select
          aria-label="Brand"
          value={brand}
          onChange={(event) => onChange({ brand: event.target.value })}
          className="mt-1 w-full rounded-xl border border-line px-3 py-2"
        >
          <option value="">All brands</option>
          {brands.map((item) => (
            <option key={item} value={item}>
              {item}
            </option>
          ))}
        </select>
      </label>
      <label className="block text-sm">
        Minimum price
        <input
          aria-label="Minimum price"
          value={minPrice}
          onChange={(event) => onChange({ minPrice: event.target.value })}
          inputMode="decimal"
          className="mt-1 w-full rounded-xl border border-line px-3 py-2"
        />
      </label>
      <label className="block text-sm">
        Maximum price
        <input
          aria-label="Maximum price"
          value={maxPrice}
          onChange={(event) => onChange({ maxPrice: event.target.value })}
          inputMode="decimal"
          className="mt-1 w-full rounded-xl border border-line px-3 py-2"
        />
      </label>
      <label className="flex items-center gap-2 text-sm">
        <input
          aria-label="In stock only"
          type="checkbox"
          checked={inStock}
          onChange={(event) => onChange({ inStock: event.target.checked })}
        />
        In stock only
      </label>
      <label className="block text-sm">
        Sort
        <select
          aria-label="Sort"
          value={sort}
          onChange={(event) => onChange({ sort: event.target.value })}
          className="mt-1 w-full rounded-xl border border-line px-3 py-2"
        >
          <option value="newest">Newest</option>
          <option value="price_asc">Price, low to high</option>
          <option value="price_desc">Price, high to low</option>
          <option value="name">Name</option>
          <option value="popular">Popular</option>
        </select>
      </label>
    </form>
  );
}
