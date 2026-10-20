import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { LoadingSpinner } from "../components/LoadingSpinner";
import { useToast } from "../components/Toast";
import { fetchProduct } from "../services/catalog";
import { fetchMe } from "../services/auth";
import { formatInr } from "../utils/money";

export function ProductDetailPage() {
  const { slug = "" } = useParams();
  const navigate = useNavigate();
  const { notify } = useToast();
  const [quantity, setQuantity] = useState(1);
  const [activeImage, setActiveImage] = useState(0);
  const product = useQuery({ queryKey: ["product", slug], queryFn: () => fetchProduct(slug) });

  if (product.isLoading) return <LoadingSpinner />;
  if (product.isError || !product.data) return <p>This product is not available.</p>;

  const item = product.data;
  const gallery = item.gallery.length > 0 ? item.gallery : item.image_url ? [{ id: 0, url: item.image_url, alt_text: item.name, is_primary: true }] : [];
  const image = gallery[activeImage] ?? gallery[0];
  const maxQuantity = Math.max(item.stock_quantity, 1);

  async function requireSignIn() {
    const session = await fetchMe();
    if (!session) {
      navigate("/login");
      return;
    }
    notify("The shopping cart is not open yet. Your quantity is saved on this page only.");
  }

  return (
    <div className="grid gap-8 lg:grid-cols-2">
      <div>
        <div className="aspect-square overflow-hidden rounded-[2rem] bg-[#efe7da]">
          {image ? <img src={image.url} alt={image.alt_text ?? item.name} className="h-full w-full object-cover" /> : null}
        </div>
        <div className="mt-3 flex gap-2">
          {gallery.map((entry, index) => (
            <button key={entry.id} type="button" onClick={() => setActiveImage(index)} className="h-16 w-16 overflow-hidden rounded-xl border border-line">
              <img src={entry.url} alt="" className="h-full w-full object-cover" />
            </button>
          ))}
        </div>
      </div>
      <div>
        <p className="text-sm tracking-wide text-moss uppercase">{item.brand}</p>
        <h1 className="mt-2 text-5xl">{item.name}</h1>
        <p className="mt-2 text-sm text-ink/60">SKU {item.sku}</p>
        <p className="mt-4 text-2xl">
          {formatInr(item.selling_price)}
          {Number(item.discount_percent) > 0 ? (
            <span className="ml-3 text-base text-ink/50 line-through">{formatInr(item.list_price)}</span>
          ) : null}
        </p>
        <p className="mt-2 text-sm">{item.in_stock ? `${item.stock_quantity} available` : "Out of stock"}</p>
        <p className="mt-6 leading-7">{item.description}</p>
        {Object.keys(item.specifications).length > 0 ? (
          <dl className="mt-6 grid grid-cols-2 gap-2 text-sm">
            {Object.entries(item.specifications).map(([key, value]) => (
              <div key={key}>
                <dt className="text-ink/50">{key}</dt>
                <dd>{value}</dd>
              </div>
            ))}
          </dl>
        ) : null}
        <label className="mt-6 block text-sm">
          Quantity
          <input
            aria-label="Quantity"
            type="number"
            min={1}
            max={maxQuantity}
            value={quantity}
            disabled={!item.in_stock}
            onChange={(event) => setQuantity(Math.min(maxQuantity, Math.max(1, Number(event.target.value) || 1)))}
            className="mt-1 w-24 rounded-xl border border-line px-3 py-2"
          />
        </label>
        <div className="mt-6 flex flex-wrap gap-3">
          <button
            type="button"
            disabled={!item.in_stock}
            onClick={() => void requireSignIn()}
            className="rounded-full bg-clay px-5 py-3 text-paper disabled:opacity-40"
          >
            Add to cart
          </button>
          <button
            type="button"
            disabled={!item.in_stock}
            onClick={() => void requireSignIn()}
            className="rounded-full border border-ink px-5 py-3 disabled:opacity-40"
          >
            Buy now
          </button>
        </div>
        <section className="mt-10">
          <h2 className="text-3xl">Reviews</h2>
          {item.reviews.length === 0 ? <p className="mt-3 text-sm text-ink/70">No reviews yet.</p> : null}
          <ul className="mt-4 space-y-4">
            {item.reviews.map((review) => (
              <li key={review.id} className="rounded-2xl border border-line bg-white p-4">
                <p className="text-sm">
                  {review.author_name} · {review.rating}/5
                </p>
                {review.title ? <p className="mt-1 font-medium">{review.title}</p> : null}
                <p className="mt-1 text-sm">{review.body}</p>
              </li>
            ))}
          </ul>
        </section>
      </div>
    </div>
  );
}
