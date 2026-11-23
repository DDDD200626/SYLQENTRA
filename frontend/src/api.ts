const API = "/api/v1";

export type Session = {
  accessToken: string;
  organizationName: string;
  demo?: boolean;
};

export async function request<T>(path: string, options: RequestInit = {}, token?: string): Promise<T> {
  const headers = new Headers(options.headers);
  headers.set("Content-Type", "application/json");
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const response = await fetch(`${API}${path}`, { ...options, headers });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    if (!body?.error) {
      const offline = new Error("API 서버에 연결하지 못했습니다.");
      offline.name = "OfflineError";
      throw offline;
    }
    const message = body.error.message || response.statusText;
    throw new Error(message);
  }
  return body as T;
}
