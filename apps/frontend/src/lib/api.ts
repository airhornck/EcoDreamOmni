import type { BaseResponse } from "../types/api";

export function authHeaders(contentType = true): Record<string, string> {
  const h: Record<string, string> = {};
  if (contentType) h["Content-Type"] = "application/json";
  try {
    const token = localStorage.getItem("token");
    if (token) h["Authorization"] = `Bearer ${token}`;
    h["X-Tenant-ID"] = localStorage.getItem("tenant_id") || "";
  } catch {
    // localStorage 不可用（隐私模式等）
  }
  try {
    h["X-Request-ID"] = crypto.randomUUID();
  } catch {
    h["X-Request-ID"] = `${Date.now()}-${Math.random().toString(36).slice(2)}`;
  }
  return h;
}

/**
 * 解包后端标准响应 {code, message, data}
 * 兼容旧版直接返回 data 的格式（过渡期）
 */
export function unwrapResponse<T>(json: unknown): T {
  if (json && typeof json === "object" && "code" in json && "data" in json) {
    const r = json as BaseResponse<T>;
    if (r.code !== "OK" && r.code !== "CREATED" && r.code !== "ACCEPTED") {
      throw new ApiError(r.code, r.message, r.trace_id);
    }
    return r.data as T;
  }
  // 兼容旧版直接返回 data 的格式
  return json as T;
}

export class ApiError extends Error {
  code: string;
  traceId?: string;

  constructor(code: string, message: string, traceId?: string) {
    super(message);
    this.name = "ApiError";
    this.code = code;
    this.traceId = traceId;
  }
}

/**
 * 统一封装的 fetch 请求
 * - 自动携带 auth headers
 * - 自动解包 data.data
 * - 统一错误处理
 */
export async function apiClient<T>(
  endpoint: string,
  options: RequestInit = {},
): Promise<T> {
  const url = endpoint.startsWith("/api/") ? endpoint : `/api${endpoint}`;
  const headers = {
    ...authHeaders(options.body instanceof FormData ? false : true),
    ...options.headers,
  };

  const res = await fetch(url, {
    ...options,
    headers,
  });

  if (!res.ok) {
    // 尝试解析后端返回的错误体
    let errBody: { code?: string; message?: string; trace_id?: string } = {};
    try {
      errBody = await res.json();
    } catch {
      // ignore parse error
    }
    throw new ApiError(
      errBody.code || `HTTP_${res.status}`,
      errBody.message || `请求失败: ${res.statusText}`,
      errBody.trace_id,
    );
  }

  const json = await res.json();
  return unwrapResponse<T>(json);
}
