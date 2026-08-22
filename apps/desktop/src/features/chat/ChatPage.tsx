import { useCallback, useEffect, useState } from "react";
import { Button } from "@/components/ui/Button";
import { Icon } from "@/components/ui/Icon";
import { createConversation, fetchConversation, fetchConversations, fetchLlmStatus, fetchMessageSources, streamMessage, type ChatMessage, type Conversation, type MessageSource } from "@/lib/api/client";

export function ChatPage() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [current, setCurrent] = useState<number | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [sources, setSources] = useState<Record<number, MessageSource[]>>({});
  const [input, setInput] = useState("");
  const [available, setAvailable] = useState<boolean | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [controller, setController] = useState<AbortController | null>(null);

  const loadConversation = useCallback(async (id: number) => {
    const detail = await fetchConversation(id);
    setCurrent(id); setMessages(detail.messages);
    const assistants = detail.messages.filter((m) => m.role === "assistant" && m.status === "complete");
    const entries = await Promise.all(assistants.map(async (m) => [m.id, await fetchMessageSources(m.id)] as const));
    setSources(Object.fromEntries(entries));
  }, []);
  const refresh = useCallback(async () => {
    try { const list = await fetchConversations(); setConversations(list); if (list[0] && current === null) await loadConversation(list[0].id); } catch (reason) { setError(reason instanceof Error ? reason.message : "Could not load conversations"); }
  }, [current, loadConversation]);
  useEffect(() => { void refresh(); void fetchLlmStatus().then((s) => setAvailable(s.available)).catch(() => setAvailable(false)); }, [refresh]);

  async function newConversation() { const conversation = await createConversation(); setConversations((items) => [conversation, ...items]); setCurrent(conversation.id); setMessages([]); setSources({}); }
  async function send() {
    if (!input.trim() || !available) return;
    let id = current;
    if (!id) { const conversation = await createConversation(); id = conversation.id; setCurrent(id); setConversations((items) => [conversation, ...items]); }
    const text = input.trim(); setInput(""); setError(null);
    const aborter = new AbortController(); setController(aborter); let assistantId = 0;
    setMessages((items) => [...items, { id: -Date.now(), conversation_id: id!, role: "user", content: text, status: "complete", model_used: null, error: null, created_at: "", updated_at: "" }]);
    try {
      await streamMessage(id, text, (event, data) => {
        if (event === "message") { assistantId = Number(data.id); setMessages((items) => [...items, { id: assistantId, conversation_id: id!, role: "assistant", content: "", status: "streaming", model_used: null, error: null, created_at: "", updated_at: "" }]); }
        if (event === "token") setMessages((items) => items.map((m) => m.id === assistantId ? { ...m, content: m.content + String(data.content) } : m));
        if (event === "complete") { setMessages((items) => items.map((m) => m.id === assistantId ? { ...m, status: "complete" } : m)); void fetchMessageSources(assistantId).then((value) => setSources((all) => ({ ...all, [assistantId]: value }))); }
        if (event === "error") { const message = String(data.error); setError(message); setMessages((items) => items.map((m) => m.id === assistantId ? { ...m, status: "failed", error: message } : m)); }
      }, aborter.signal);
    } catch (reason) { if (!aborter.signal.aborted) setError(reason instanceof Error ? reason.message : "Message failed"); }
    finally { setController(null); void refresh(); }
  }

  return <section className="page page-reading chat-page">
    {available === false && <div className="chat-banner">Ollama isn't running. Start Ollama to chat with your study material.</div>}
    <header className="page-header chat-header"><div><p className="eyebrow">Chat</p><h1>Ask about your study material.</h1></div><Button onClick={() => void newConversation()}>New conversation</Button></header>
    <div className="chat-layout"><aside className="conversation-list">{conversations.map((conversation) => <button className={conversation.id === current ? "conversation-item active" : "conversation-item"} key={conversation.id} onClick={() => void loadConversation(conversation.id)} type="button">{conversation.title || "New conversation"}</button>)}</aside><div className="chat-thread" aria-label="Conversation">{messages.map((message) => <article className={`message message-${message.role}`} key={message.id}><p>{message.content || (message.status === "streaming" ? "Thinking…" : "")}</p>{message.error && <small className="status-error">{message.error}</small>}{sources[message.id]?.length ? <div className="citation-row">{sources[message.id].map((source) => <span className="citation-chip" key={source.id}><Icon name="fileText" size={16}/>{source.filename}</span>)}</div> : null}</article>)}</div></div>
    {error && <p className="status-error">{error}</p>}
    <form className="composer" onSubmit={(event) => { event.preventDefault(); void send(); }}><textarea disabled={!available || !!controller} value={input} onChange={(event) => setInput(event.target.value)} placeholder={available === false ? "Start Ollama to chat" : "Ask about a lecture, assignment, or concept…"} rows={3}/><div className="composer-footer"><span>Answers cite your study material when it is relevant.</span>{controller ? <Button type="button" onClick={() => controller.abort()}>Stop</Button> : <Button disabled={!available || !input.trim()} variant="primary" type="submit">Send</Button>}</div></form>
  </section>;
}
