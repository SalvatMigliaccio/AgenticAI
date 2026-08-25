export const API_BASE = import.meta.env.VITE_API_BASE || "/api/v1";
export const CHAT_STREAM_ENDPOINT = `${API_BASE}/chat/stream`;
export const GITHUB_MAIN_URL = import.meta.env.VITE_GITHUB_MAIN_URL || "https://github.com";
export const GITHUB_BACKEND_URL = import.meta.env.VITE_GITHUB_BACKEND_URL || "https://github.com";
export const GITHUB_FRONTEND_URL = import.meta.env.VITE_GITHUB_FRONTEND_URL || "https://github.com";

export function newThreadId() {
  return `thread-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
}

export function toPercent(value) {
  if (typeof value !== "number" || Number.isNaN(value)) return "-";
  return `${Math.max(0, Math.min(100, value * 100)).toFixed(1)}%`;
}

export function scoreClass(score) {
  if (typeof score !== "number") return "neutral";
  if (score >= 4) return "good";
  if (score >= 3) return "mid";
  return "low";
}

function parseSSEBlock(block) {
  const lines = block.split("\n");
  let event = "message";
  const dataLines = [];

  for (const rawLine of lines) {
    const line = rawLine.trimEnd();
    if (!line || line.startsWith(":")) continue;
    if (line.startsWith("event:")) {
      event = line.slice(6).trim();
      continue;
    }
    if (line.startsWith("data:")) {
      dataLines.push(line.slice(5).trimStart());
    }
  }

  return { event, data: dataLines.join("\n") };
}

export async function fetchAgents() {
  const res = await fetch(`${API_BASE}/agents`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const data = await res.json();
  return Array.isArray(data) ? data : [];
}

/**
 * Streams a chat turn from the backend and invokes `onEvent(eventName, payload)`
 * for each typed SSE event (route, specialist, judge_status, judge, answer, done).
 */
export async function streamChat(queryText, threadId, onEvent) {
  const response = await fetch(CHAT_STREAM_ENDPOINT, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query: queryText, thread_id: threadId }),
  });

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }
  if (!response.body) {
    throw new Error("Streaming non disponibile dal backend.");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true }).replace(/\r\n/g, "\n");

    while (true) {
      const sep = buffer.indexOf("\n\n");
      if (sep === -1) break;

      const block = buffer.slice(0, sep);
      buffer = buffer.slice(sep + 2);
      const { event, data } = parseSSEBlock(block);
      if (!data) continue;

      let parsed;
      try {
        parsed = JSON.parse(data);
      } catch {
        continue;
      }

      onEvent(event, parsed);
    }
  }
}
