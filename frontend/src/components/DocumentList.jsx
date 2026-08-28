import { useEffect, useState } from "react";
import { FileText, ExternalLink } from "lucide-react";
import toast from "react-hot-toast";
import api, { errMsg } from "../api/api";

export default function DocumentList({ workspaceId }) {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [openingId, setOpeningId] = useState(null);

  useEffect(() => {
    let alive = true;
    (async () => {
      setLoading(true);
      try {
        const resp = await api.get(`/workspaces/${workspaceId}/documents`);
        if (alive) setDocuments(resp.data);
      } catch (err) {
        toast.error(errMsg(err, "Could not load documents"));
      } finally {
        if (alive) setLoading(false);
      }
    })();
    return () => {
      alive = false;
    };
  }, [workspaceId]);

  const open = async (doc) => {
    setOpeningId(doc.id);
    const t = toast.loading("Preparing document…");
    try {
      const resp = await api.get(`/documents/${doc.id}/download`);
      window.open(resp.data.url, "_blank", "noopener,noreferrer");
      toast.success("Opened in a new tab", { id: t });
    } catch (err) {
      toast.error(errMsg(err, "Unable to open document"), { id: t });
    } finally {
      setOpeningId(null);
    }
  };

  return (
    <aside className="card sidebar">
      <h4>Documents {documents.length > 0 && `(${documents.length})`}</h4>
      {loading ? (
        <div style={{ display: "grid", gap: 8 }}>
          {[0, 1, 2].map((i) => (
            <div className="skeleton" style={{ height: 34 }} key={i} />
          ))}
        </div>
      ) : documents.length === 0 ? (
        <p className="muted" style={{ fontSize: 13 }}>
          No documents in this workspace yet.
        </p>
      ) : (
        documents.map((doc) => (
          <div
            className="doc-row"
            key={doc.id}
            onClick={() => open(doc)}
            title={doc.filename}
          >
            <FileText
              size={15}
              style={{ flex: "none", color: "var(--accent-2)" }}
            />
            <span className="fn">{doc.filename}</span>
            {openingId === doc.id ? (
              <span className="spinner" />
            ) : (
              <ExternalLink size={13} className="muted" />
            )}
          </div>
        ))
      )}
    </aside>
  );
}
