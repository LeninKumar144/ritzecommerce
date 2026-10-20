import { api, csrfHeaders, readCsrfToken } from "./api";
import type { SessionUser } from "../types/catalog";

export async function fetchMe(): Promise<SessionUser | null> {
  try {
    const response = await api.get<SessionUser>("/auth/me");
    return response.data;
  } catch {
    return null;
  }
}

export async function ensureCsrf(): Promise<string | undefined> {
  await api.get("/health");
  return readCsrfToken();
}

export async function login(email: string, password: string): Promise<SessionUser> {
  const token = (await ensureCsrf()) ?? readCsrfToken();
  const response = await api.post<SessionUser>(
    "/auth/login",
    { email, password },
    { headers: csrfHeaders(token) },
  );
  return response.data;
}

export async function register(input: {
  email: string;
  password: string;
  full_name: string;
  phone?: string;
}): Promise<SessionUser> {
  const token = (await ensureCsrf()) ?? readCsrfToken();
  const response = await api.post<SessionUser>("/auth/register", input, { headers: csrfHeaders(token) });
  return response.data;
}

export async function logout(): Promise<void> {
  const token = readCsrfToken();
  await api.post("/auth/logout", null, { headers: csrfHeaders(token) });
}
