import { Link, useNavigate } from "react-router-dom";
import { FormEvent, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchMe, logout } from "../services/auth";

export function Header() {
  const navigate = useNavigate();
  const [term, setTerm] = useState("");
  const session = useQuery({ queryKey: ["me"], queryFn: fetchMe });

  function onSearch(event: FormEvent) {
    event.preventDefault();
    const params = new URLSearchParams();
    if (term.trim()) params.set("search", term.trim());
    navigate(`/products?${params.toString()}`);
  }

  return (
    <header className="sticky top-0 z-40 border-b border-line bg-paper/95 backdrop-blur">
      <div className="mx-auto flex max-w-6xl flex-wrap items-center gap-4 px-4 py-4">
        <Link to="/" className="font-display text-3xl tracking-tight">
          Ritz
        </Link>
        <nav className="flex gap-4 text-sm">
          <Link to="/products">Shop</Link>
          <Link to="/products?sort=newest">New</Link>
        </nav>
        <form onSubmit={onSearch} className="flex min-w-[220px] flex-1" role="search">
          <label className="sr-only" htmlFor="shop-search">
            Search products
          </label>
          <input
            id="shop-search"
            value={term}
            onChange={(event) => setTerm(event.target.value)}
            placeholder="Search shirts, brands, SKUs"
            className="w-full rounded-full border border-line bg-white px-4 py-2"
          />
        </form>
        {session.data ? (
          <button
            type="button"
            className="text-sm"
            onClick={() => {
              void logout().then(() => session.refetch());
            }}
          >
            {session.data.full_name}
          </button>
        ) : (
          <Link to="/login" className="text-sm">
            Sign in
          </Link>
        )}
      </div>
    </header>
  );
}
