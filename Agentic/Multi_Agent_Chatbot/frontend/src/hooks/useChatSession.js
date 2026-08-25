import { useEffect, useMemo, useRef, useState } from "react";
import { newThreadId, streamChat } from "../lib/api";

const EMPTY_LIVE = { route: "-", method: "-", confidence: null, judgeOverall: null };

function welcomeMessage(id, text) {
  return { id, role: "assistant", text, meta: null };
}

export function useChatSession() {
  const typingTimersRef = useRef(new Map());
  const [query, setQuery] = useState("");
  const [pending, setPending] = useState(false);
  const [threadId, setThreadId] = useState(() => localStorage.getItem("thread_id") || newThreadId());
  const [messages, setMessages] = useState([
    welcomeMessage(
      "welcome",
      "Ciao. Sono pronto. In questo stage rispondo usando la knowledge locale indicizzata nel progetto."
    ),
  ]);
  const [error, setError] = useState("");
  const [live, setLive] = useState(EMPTY_LIVE);

  useEffect(() => {
    localStorage.setItem("thread_id", threadId);
  }, [threadId]);

  const activeThreadLabel = useMemo(() => threadId.slice(0, 18), [threadId]);

  function stopPreviewAnimation(messageId) {
    const timer = typingTimersRef.current.get(messageId);
    if (timer) {
      clearInterval(timer);
      typingTimersRef.current.delete(messageId);
    }
  }

  function patchAssistantMessage(messageId, patch) {
    setMessages((prev) =>
      prev.map((msg) => {
        if (msg.id !== messageId) return msg;
        return {
          ...msg,
          ...(patch.text !== undefined ? { text: patch.text } : {}),
          meta: { ...(msg.meta || {}), ...(patch.meta || {}) },
        };
      })
    );
  }

  function animatePreview(messageId, fullText) {
    if (!fullText) return;
    stopPreviewAnimation(messageId);

    let index = 0;
    const step = Math.max(8, Math.floor(fullText.length / 75));
    const timer = setInterval(() => {
      index = Math.min(fullText.length, index + step);
      patchAssistantMessage(messageId, { text: fullText.slice(0, index) });
      if (index >= fullText.length) stopPreviewAnimation(messageId);
    }, 20);

    typingTimersRef.current.set(messageId, timer);
  }

  function handleStreamEvent(assistantId, event, parsed) {
    if (event === "route") {
      const routePatch = {
        route: parsed.route || "general",
        confidence: parsed.confidence,
        method: parsed.method || "-",
        routePending: false,
      };
      setLive((prev) => ({ ...prev, ...routePatch }));
      patchAssistantMessage(assistantId, { meta: routePatch });
      return;
    }

    if (event === "specialist") {
      if (typeof parsed.preview === "string" && parsed.preview.trim()) {
        animatePreview(assistantId, parsed.preview);
      }
      patchAssistantMessage(assistantId, { meta: { specialistPending: false } });
      return;
    }

    if (event === "judge_status") {
      patchAssistantMessage(assistantId, { meta: { judgePending: parsed.status === "running" } });
      return;
    }

    if (event === "judge") {
      setLive((prev) => ({ ...prev, judgeOverall: parsed.overall ?? null }));
      patchAssistantMessage(assistantId, { meta: { judge: parsed, judgePending: false } });
      return;
    }

    if (event === "answer") {
      stopPreviewAnimation(assistantId);
      patchAssistantMessage(assistantId, {
        text: parsed.answer || "Nessuna risposta disponibile.",
        meta: { answerVisible: true },
      });
      return;
    }

    if (event === "done") {
      stopPreviewAnimation(assistantId);
      patchAssistantMessage(assistantId, {
        meta: {
          trace: Array.isArray(parsed.trace) ? parsed.trace : [],
          complete: true,
          routePending: false,
          judgePending: false,
        },
      });
    }
  }

  async function sendMessage(evt) {
    evt.preventDefault();
    const content = query.trim();
    if (!content || pending) return;

    const userMsg = { id: `u-${Date.now()}`, role: "user", text: content, meta: null };
    setMessages((prev) => [...prev, userMsg]);
    setQuery("");
    setPending(true);
    setError("");
    setLive(EMPTY_LIVE);

    const assistantId = `a-${Date.now()}`;
    setMessages((prev) => [
      ...prev,
      {
        id: assistantId,
        role: "assistant",
        text: "Sto elaborando la richiesta...",
        meta: {
          route: null,
          confidence: null,
          method: null,
          specialistPending: true,
          routePending: true,
          judgePending: false,
          answerVisible: false,
          complete: false,
          judge: {},
          trace: [],
        },
      },
    ]);

    try {
      await streamChat(content, threadId, (event, parsed) => handleStreamEvent(assistantId, event, parsed));
    } catch {
      stopPreviewAnimation(assistantId);
      setError("Errore durante la chiamata API. Controlla backend e proxy Nginx.");
      patchAssistantMessage(assistantId, {
        text: "Non sono riuscito a completare lo stream. Riprova tra pochi secondi.",
        meta: { answerVisible: true, judgePending: false },
      });
    } finally {
      setPending(false);
    }
  }

  function resetThread() {
    stopPreviewAnimation();
    setThreadId(newThreadId());
    setMessages([
      welcomeMessage("welcome-reset", "Nuovo thread creato. Puoi iniziare una nuova conversazione."),
    ]);
    setError("");
    setLive(EMPTY_LIVE);
  }

  return {
    query,
    setQuery,
    pending,
    messages,
    error,
    live,
    activeThreadLabel,
    sendMessage,
    resetThread,
  };
}
