import { FormEvent, useEffect, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ApiError } from "../api/client";
import { personaApi, researchApi } from "../api/endpoints";
import { Spinner } from "../components/States";
import { useToast } from "../context/ToastContext";
import type { ChatMessage, Persona } from "../types";

export function PersonaChat() {
  const { id = "", personaId = "" } = useParams();
  const { toast } = useToast();
  const [persona, setPersona] = useState<Persona | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [conversationId, setConversationId] = useState<string | undefined>();
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const endRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    researchApi
      .personas(id)
      .then((list) => setPersona(list.find((p) => p.id === personaId) ?? null))
      .catch(() => setPersona(null));
  }, [id, personaId]);

  useEffect(()=>{
    personaApi
      .conversations(personaId)
      .then((list)=>{
        if (list.length>0){
          setConversationId(list[0].id);
          setMessages(list[0].messages);
        }
      })
      .catch(()=>{});
  },[personaId]);

  const newSession=()=>{
    setConversationId(undefined);
    setMessages([]);
  };

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const send = async (e: FormEvent) => {
    e.preventDefault();
    const text = input.trim();
    if (!text || busy) return;
    setBusy(true);
    setInput("");
    const optimistic: ChatMessage = {
      id: `local-${Date.now()}`,
      role: "user",
      content: text,
      order_index: messages.length,
      created_at: new Date().toISOString(),
    };
    setMessages((m) => [...m, optimistic]);
    try {
      const res = await personaApi.chat(personaId, text, conversationId);
      setConversationId(res.conversation_id);
      setMessages((m) => [...m, res.reply]);
    } catch (err) {
      toast(err instanceof ApiError ? err.message : "Message failed.", "error");
      setMessages((m) => m.filter((x) => x.id !== optimistic.id));
    } finally {
      setBusy(false);
    }
  };

  if (!persona) return <Spinner label="Loading persona…" />;

  return (
    <div className="page page-narrow chat-page">
      <div className="page-head">
        <div>
          <h1>Chat with {persona.name}</h1>
          <p className="muted">
            {persona.occupation} ·{" "}
            <Link to={`/research/${id}`}>back to project</Link>
          </p>
        </div>
        <button className="btn btn-secondary btn-sm" onClick={newSession} disabled={busy}>
          New Session
        </button>
      </div>

      <div className="banner banner-warn">
        You are chatting with a synthetic (AI-generated) persona. Responses are simulated.
      </div>

      <div className="chat-window card">
        {messages.length === 0 && (
          <p className="muted chat-empty">
            Ask {persona.name.split(" ")[0]} about the product, their needs, or objections.
          </p>
        )}
        {messages.map((m) => (
          <div key={m.id} className={`bubble bubble-${m.role}`}>
            {m.content}
          </div>
        ))}
        {busy && <div className="bubble bubble-persona bubble-typing">…</div>}
        <div ref={endRef} />
      </div>

      <form className="chat-input" onSubmit={send}>
        <input
          value={input}
          placeholder={`Message ${persona.name.split(" ")[0]}…`}
          onChange={(e) => setInput(e.target.value)}
          disabled={busy}
        />
        <button className="btn btn-primary" type="submit" disabled={busy || !input.trim()}>
          Send
        </button>
      </form>
    </div>
  );
}
