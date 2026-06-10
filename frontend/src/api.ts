// Thin typed API client for the Mrs IArma backend.
//
// In dev, requests go to `/api/*` which Vite proxies to http://localhost:8000.
// In prod, the same paths are served from the same origin (frontend is bundled
// behind FastAPI as static files, OR deployed to a static host with /api/*
// rewritten to the backend Cloud Run service).
//
// Optional X-API-Key header:
//   The backend reads API_KEY from env. If empty, auth is disabled (dev).
//   For prod, inject this at build time via VITE_API_KEY or via runtime config.

import type {
  CategoriesResponse,
  EvaluateResponse,
  EvaluationFormState,
} from "./types";

const API_KEY = import.meta.env.VITE_API_KEY ?? "";

function authHeaders(): HeadersInit {
  return API_KEY ? { "X-API-Key": API_KEY } : {};
}

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
    this.name = "ApiError";
  }
}

async function handle<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail ?? body.message ?? detail;
    } catch {
      // not json
    }
    throw new ApiError(res.status, detail);
  }
  return (await res.json()) as T;
}

export async function fetchCategories(): Promise<CategoriesResponse> {
  const res = await fetch("/api/categories", { headers: authHeaders() });
  return handle<CategoriesResponse>(res);
}

export async function evaluateBoard(
  form: EvaluationFormState,
): Promise<EvaluateResponse> {
  if (!form.image) {
    throw new Error("Image is required.");
  }
  const fd = new FormData();
  fd.append("campaign_name", form.campaign_name);
  fd.append("category", form.category);
  fd.append("client", form.client);
  fd.append("agency", form.agency);
  fd.append("client_internationally_known", String(form.client_internationally_known));
  fd.append("image", form.image);

  const res = await fetch("/api/evaluate", {
    method: "POST",
    body: fd,
    headers: authHeaders(),
  });
  return handle<EvaluateResponse>(res);
}

export async function fetchHealth(): Promise<{ status: string; index_loaded: boolean }> {
  const res = await fetch("/api/health");
  return handle(res);
}
