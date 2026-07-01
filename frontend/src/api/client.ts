const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";
const WS_BASE = API_BASE.replace(/^http/, "ws");

export async function startResearch(question: string): Promise<{ session_id: string; websocket_url: string }> {
  const response = await fetch(`${API_BASE}/api/research`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
  if (!response.ok) {
    throw new Error(`Research request failed: ${response.status}`);
  }
  return response.json();
}

export function sessionWebSocketUrl(path: string): string {
  return `${WS_BASE}${path}`;
}

