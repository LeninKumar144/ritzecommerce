import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, vi } from "vitest";
import { fetchBrands, fetchProduct, fetchProducts } from "../services/catalog";
import { ProductDetailPage } from "./ProductDetailPage";
import { ProductListPage } from "./ProductListPage";

vi.mock("../services/catalog", () => ({
  fetchProducts: vi.fn(),
  fetchBrands: vi.fn(),
  fetchProduct: vi.fn(),
}));

vi.mock("../services/auth", () => ({
  fetchMe: vi.fn().mockResolvedValue(null),
}));

const sample = {
  id: 1,
  name: "Cotton shirt",
  slug: "cotton-shirt",
  brand: "Ritz",
  image_url: null,
  list_price: "1499.00",
  selling_price: "1349.10",
  discount_percent: "10.00",
  in_stock: true,
};

function renderList(path = "/products") {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[path]}>
        <ProductListPage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  vi.mocked(fetchProducts).mockResolvedValue({ items: [sample], page: 1, page_size: 8, total: 1 });
  vi.mocked(fetchBrands).mockResolvedValue(["Ritz"]);
});

it("lists products returned by the catalog", async () => {
  renderList();
  expect(await screen.findByRole("heading", { name: "Cotton shirt" })).toBeInTheDocument();
  expect(screen.getByText("In stock")).toBeInTheDocument();
});

it("shows the search term from the query string", async () => {
  renderList("/products?search=cotton");
  expect(await screen.findByRole("heading", { name: /Results for/ })).toHaveTextContent("cotton");
});

it("loads the next page when Next is clicked", async () => {
  vi.mocked(fetchProducts).mockResolvedValue({ items: [sample], page: 1, page_size: 8, total: 9 });
  const user = userEvent.setup();
  renderList();
  expect(await screen.findByText("Page 1 of 2")).toBeInTheDocument();
  await user.click(screen.getByRole("button", { name: "Next" }));
  expect(fetchProducts).toHaveBeenCalledWith(expect.objectContaining({ page: 2, page_size: 8 }));
});

it("requests a new sort when the filter changes", async () => {
  const user = userEvent.setup();
  renderList();
  await screen.findByRole("heading", { name: "Cotton shirt" });
  await user.selectOptions(screen.getByLabelText("Sort"), "price_asc");
  expect(fetchProducts).toHaveBeenCalledWith(expect.objectContaining({ sort: "price_asc" }));
});

it("shows product details and sends an unsigned shopper to sign in", async () => {
  vi.mocked(fetchProduct).mockResolvedValue({
    ...sample,
    sku: "SHIRT-001",
    description: "Woven cotton shirt",
    specifications: { material: "cotton" },
    tax_rate: "18.00",
    stock_quantity: 4,
    gallery: [],
    reviews: [],
    review_page: 1,
    review_total: 0,
  });
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const user = userEvent.setup();
  render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={["/products/cotton-shirt"]}>
        <Routes>
          <Route path="/products/:slug" element={<ProductDetailPage />} />
          <Route path="/login" element={<h1>Sign in form</h1>} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
  expect(await screen.findByText("SKU SHIRT-001")).toBeInTheDocument();
  expect(screen.getByText("Woven cotton shirt")).toBeInTheDocument();
  await user.clear(screen.getByLabelText("Quantity"));
  await user.type(screen.getByLabelText("Quantity"), "2");
  await user.click(screen.getByRole("button", { name: "Add to cart" }));
  expect(await screen.findByRole("heading", { name: "Sign in form" })).toBeInTheDocument();
});
