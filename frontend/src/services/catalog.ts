import { api } from "./api";
import type { Category, ProductDetail, ProductList, ProductQuery } from "../types/catalog";

export async function fetchCategories(): Promise<Category[]> {
  const response = await api.get<Category[]>("/categories");
  return response.data;
}

export async function fetchCategory(slug: string): Promise<Category> {
  const response = await api.get<Category>(`/categories/${slug}`);
  return response.data;
}

export async function fetchProducts(query: ProductQuery): Promise<ProductList> {
  const response = await api.get<ProductList>("/products", { params: query });
  return response.data;
}

export async function fetchProduct(slug: string): Promise<ProductDetail> {
  const response = await api.get<ProductDetail>(`/products/${slug}`);
  return response.data;
}

export async function fetchBrands(): Promise<string[]> {
  const response = await api.get<string[]>("/products/brands");
  return response.data;
}
