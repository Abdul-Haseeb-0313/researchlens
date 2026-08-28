import { useEffect, useRef, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { ArrowLeft, SendHorizonal } from "lucide-react";
import toast from "react-hot-toast";
import api, { errMsg } from "../api/api";
import DocumentList from "../components/DocumentList";
import MarkdownContent from "../components/MarkdownContent";

export default function WorkspaceChat() {
  const { workspaceId } = useParams();
  const [messages, setMessages] = useState([]);
  const [question, setQuestion] = useState("");
  const [asking, setAsking] = useState(false);
  const [loadingHistory, setLoadingHistory] = useState(true);
  const endRef = useRef(null);

  useEffect(() => {
    let alive = true;
    (async () => {
      setLoadingHistory(true);
      try {
        const resp = await api.get(`/workspaces/${workspaceId}/messages`);
        if (alive) {
          setMessages(
            resp.data.map((m) => ({
              role: m.role,
              content: m.content,
              sources: m.sources || [],
            }))
          );
        }
      } catch (err) {
        toast.error(errMsg(err, "Could not load chat history"));
      } finally {
        if (alive) setLoadingHistory(false);
      }
    })();
    return () => {
      alive = false;
    };
  }, [workspaceId]);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, asking]);

  const ask = async () => {
    const q = question.trim();
    if (!q || asking) return;
    setMessages((p) => [...p, { role: "user", content: q }]);
    setQuestion("");
    setAsking(true);
    try {
      const resp = await api.post(`/workspaces/${workspaceId}/ask`, {
        question: q,
      });
      setMessages((p) => [
        ...p,
        {
          role: "assistant",
          content: resp.data.answer,
          sources: resp.data.cited_sources || [],
        },
      ]);
    } catch (err) {
      const m = errMsg(err, "The assistant could not answer that");
      toast.error(m);
      setMessages((p) => [
        ...p,
        { role: "assistant", content: `⚠️ ${m}`, sources: [] },
      ]);
    } finally {
      setAsking(false);
    }
  };

  return (
    <main className="container page">
      <Link to="/app" className="btn btn-ghost" style={{ marginBottom: 18 }}>
        <ArrowLeft size={16} /> All workspaces
      </Link>

      <div className="chat-layout">
        <DocumentList workspaceId={workspaceId} />

        <section className="card chat-panel">
          <div className="chat-head">
            <h3 style={{ fontSize: 16 }}>Ask your documents</h3>
            {asking && (
              <span className="badge">
                <span className="spinner" /> Searching sources…
              </span>
            )}
          </div>

          <div className="messages">
            {loadingHistory ? (
              [0, 1].map((i) => (
                <div className="skeleton" key={i} style={{ maxWidth: "70%" }} />
              ))
            ) : messages.length === 0 ? (
              <div className="empty" style={{ margin: "auto" }}>
                <h3 style={{ fontSize: 17 }}>Start the conversation</h3>
                <p className="muted" style={{ fontSize: 14 }}>
                  Try: “Summarize the main findings across these papers.”
                </p>
              </div>
            ) : (
              messages.map((msg, idx) => (
                <div className={`msg ${msg.role}`} key={idx}>
                  {msg.role === "assistant" ? (
                    <MarkdownContent content={msg.content} />
                  ) : (
                    <div>{msg.content}</div>
                  )}
                  {msg.sources?.length > 0 && (
                    <div className="sources">
                      {msg.sources.map((s, i) => (
                        <span className="src-chip" key={i}>
                          [{i + 1}] {s.document_id} · p.{s.page_start}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ))
            )}

            {asking && (
              <div className="msg assistant">
                <span className="typing">
                  <i />
                  <i />
                  <i />
                </span>
                <span
                  className="muted"
                  style={{ marginLeft: 10, fontSize: 13 }}
                >
                  Reading your documents and drafting a cited answer…
                </span>
              </div>
            )}
            <div ref={endRef} />
          </div>

          <div className="composer">
            <textarea
              className="input"
              rows={1}
              placeholder="Ask a question about these documents…"
              value={question}
              disabled={asking}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  ask();
                }
              }}
            />
            <button
              className="btn btn-primary"
              onClick={ask}
              disabled={asking || !question.trim()}
            >
              {asking ? (
                <span className="spinner" />
              ) : (
                <SendHorizonal size={16} />
              )}
              {asking ? "Thinking…" : "Send"}
            </button>
          </div>
        </section>
      </div>
    </main>
  );
}
