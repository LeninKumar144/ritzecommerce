import { Link } from "react-router-dom";

export function Footer() {
  return (
    <footer className="mt-16 border-t border-line bg-ink text-paper">
      <div className="mx-auto grid max-w-6xl gap-8 px-4 py-10 md:grid-cols-3">
        <div>
          <p className="font-display text-2xl">Ritz</p>
          <p className="mt-2 text-sm text-paper/80">Clothes and household goods, priced in INR.</p>
        </div>
        <div className="text-sm">
          <p className="font-medium">Policies</p>
          <ul className="mt-2 space-y-1 text-paper/80">
            <li>
              <Link to="/products">Shipping on orders over ₹999</Link>
            </li>
            <li>Returns reviewed after delivery</li>
          </ul>
        </div>
        <div className="text-sm">
          <p className="font-medium">Contact</p>
          <a className="mt-2 block text-paper/80" href="mailto:hello@ritz.shop">
            hello@ritz.shop
          </a>
        </div>
      </div>
    </footer>
  );
}
