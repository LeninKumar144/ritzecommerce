import axios from "axios";

export const api = axios.create({
  baseURL: "/api/v1",
  withCredentials: true,
});

export function csrfHeaders(token: string | undefined): { "X-CSRF-Token": string } | undefined {
  return token ? { "X-CSRF-Token": token } : undefined;
}

export function readCsrfToken(): string | undefined {
  const match = document.cookie.split("; ").find((item) => item.startsWith("csrf_token="));
  return match ? decodeURIComponent(match.split("=")[1]) : undefined;
}
