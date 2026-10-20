export type Category = {
  id: number;
  name: string;
  slug: string;
  description: string | null;
  image_url: string | null;
};

export type ProductCard = {
  id: number;
  name: string;
  slug: string;
  brand: string;
  image_url: string | null;
  list_price: string;
  selling_price: string;
  discount_percent: string;
  in_stock: boolean;
};

export type ProductList = {
  items: ProductCard[];
  page: number;
  page_size: number;
  total: number;
};

export type ProductImage = {
  id: number;
  url: string;
  alt_text: string | null;
  is_primary: boolean;
};

export type Review = {
  id: number;
  rating: number;
  title: string | null;
  body: string;
  author_name: string;
};

export type ProductDetail = ProductCard & {
  sku: string;
  description: string;
  specifications: Record<string, string>;
  tax_rate: string | null;
  stock_quantity: number;
  gallery: ProductImage[];
  reviews: Review[];
  review_page: number;
  review_total: number;
};

export type ProductQuery = {
  search?: string;
  category?: string;
  brand?: string;
  min_price?: string;
  max_price?: string;
  in_stock?: boolean;
  featured?: boolean;
  sort?: "newest" | "price_asc" | "price_desc" | "name" | "popular";
  page?: number;
  page_size?: number;
};

export type SessionUser = {
  id: number;
  email: string;
  full_name: string;
  phone: string | null;
  role: string;
  is_active: boolean;
};
