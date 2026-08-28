import { useEffect, useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import {
  Plus,
  Trash2,
  FolderOpen,
  UploadCloud,
  FileText,
  X,
} from "lucide-react";
import toast from "react-hot-toast";
import api, { errMsg } from "../api/api";
import Modal from "../components/ui/Modal";
import ConfirmDialog from "../components/ui/ConfirmDialog";

export default function Workspaces() {
  const [workspaces, setWorkspaces] = useState([]);
  const [loading, setLoading] = useState(true);
  const [createOpen, setCreateOpen] = useState(false);
  const [name, setName] = useState("");
  const [files, setFiles] = useState([]);
  const [drag, setDrag] = useState(false);
  const [creating, setCreating] = useState(false);
  const [progress, setProgress] = useState(0);
  const [toDelete, setToDelete] = useState(null);
  const [deleting, setDeleting] = useState(false);
  const fileRef = useRef(null);
  const navigate = useNavigate();

  const fetchWorkspaces = async () => {
    try {
      const resp = await api.get("/workspaces");
      setWorkspaces(resp.data);
    } catch (err) {
      toast.error(errMsg(err, "Could not load workspaces"));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWorkspaces();
  }, []);

  const addFiles = (list) => {
    const pdfs = Array.from(list).filter(
      (f) =>
        f.type === "application/pdf" || f.name.toLowerCase().endsWith(".pdf")
    );
    if (pdfs.length !== list.length)
      toast.error("Only PDF files are supported");
    setFiles((prev) => [...prev, ...pdfs]);
  };

  const resetForm = () => {
    setName("");
    setFiles([]);
    setProgress(0);
  };

  const handleCreate = async () => {
    if (!name.trim()) return toast.error("Give your workspace a name");
    setCreating(true);
    setProgress(0);
    const fd = new FormData();
    fd.append("name", name.trim());
    files.forEach((f) => fd.append("files", f));
    try {
      await api.post("/workspaces", fd, {
        headers: { "Content-Type": "multipart/form-data" },
        onUploadProgress: (e) =>
          e.total && setProgress(Math.round((e.loaded * 100) / e.total)),
      });
      toast.success("Workspace created");
      setCreateOpen(false);
      resetForm();
      fetchWorkspaces();
    } catch (err) {
      toast.error(errMsg(err, "Workspace creation failed"));
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async () => {
    setDeleting(true);
    try {
      await api.delete(`/workspaces/${toDelete.id}`);
      setWorkspaces((w) => w.filter((x) => x.id !== toDelete.id));
      toast.success("Workspace deleted");
      setToDelete(null);
    } catch (err) {
      toast.error(errMsg(err, "Delete failed"));
    } finally {
      setDeleting(false);
    }
  };

  return (
    <main className="container page">
      <div className="page-head">
        <div>
          <h2>Your workspaces</h2>
          <p className="muted" style={{ marginTop: 6, fontSize: 14 }}>
            Each workspace is an isolated set of documents and its own chat
            thread.
          </p>
        </div>
        <button className="btn btn-primary" onClick={() => setCreateOpen(true)}>
          <Plus size={16} /> New workspace
        </button>
      </div>

      {loading ? (
        <div className="ws-grid">
          {[0, 1, 2].map((i) => (
            <div className="skeleton" key={i} />
          ))}
        </div>
      ) : workspaces.length === 0 ? (
        <div className="card empty">
          <h3>No workspaces yet</h3>
          <p className="muted" style={{ marginBottom: 20 }}>
            Create one and upload the PDFs you want to question.
          </p>
          <button
            className="btn btn-primary"
            onClick={() => setCreateOpen(true)}
          >
            <Plus size={16} /> Create workspace
          </button>
        </div>
      ) : (
        <div className="ws-grid">
          {workspaces.map((ws) => (
            <div
              className="card ws-card"
              key={ws.id}
              onClick={() => navigate(`/app/w/${ws.id}`)}
            >
              <button
                className="btn-icon del"
                onClick={(e) => {
                  e.stopPropagation();
                  setToDelete(ws);
                }}
                aria-label="Delete workspace"
              >
                <Trash2 size={16} />
              </button>
              <h3>{ws.name}</h3>
              <p
                className="muted"
                style={{
                  fontSize: 13,
                  display: "flex",
                  alignItems: "center",
                  gap: 6,
                  margin: 0,
                }}
              >
                <FolderOpen size={14} /> Open workspace
              </p>
            </div>
          ))}
        </div>
      )}

      <Modal
        open={createOpen}
        onClose={() => {
          if (!creating) {
            setCreateOpen(false);
            resetForm();
          }
        }}
        closable={!creating}
        title="New workspace"
        subtitle="Name it, then add the PDFs you want to search."
      >
        <div className="field">
          <label className="label">Workspace name</label>
          <input
            className="input"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Climate policy review"
            disabled={creating}
          />
        </div>

        <label className="label">Documents (PDF)</label>
        <div
          className={`dropzone ${drag ? "drag" : ""}`}
          onClick={() => !creating && fileRef.current?.click()}
          onDragOver={(e) => {
            e.preventDefault();
            setDrag(true);
          }}
          onDragLeave={() => setDrag(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDrag(false);
            if (!creating) addFiles(e.dataTransfer.files);
          }}
        >
          <UploadCloud size={22} style={{ marginBottom: 8 }} />
          <div style={{ fontSize: 14 }}>Drop PDFs here or click to browse</div>
        </div>
        <input
          ref={fileRef}
          type="file"
          multiple
          accept=".pdf"
          hidden
          onChange={(e) => addFiles(e.target.files)}
        />

        {files.map((f, i) => (
          <div className="file-row" key={`${f.name}-${i}`}>
            <FileText size={15} />
            <span className="name">{f.name}</span>
            <span className="muted">
              {(f.size / 1024 / 1024).toFixed(1)} MB
            </span>
            {!creating && (
              <button
                className="btn-icon"
                onClick={() => setFiles((p) => p.filter((_, x) => x !== i))}
              >
                <X size={14} />
              </button>
            )}
          </div>
        ))}

        {creating && (
          <>
            <div className="progress" style={{ marginTop: 16 }}>
              <i style={{ width: `${progress}%` }} />
            </div>
            <div className="busy-note">
              <span className="spinner" />
              {progress < 100
                ? `Uploading documents… ${progress}%`
                : "Indexing pages — this can take a minute, please keep this open."}
            </div>
          </>
        )}

        <div className="modal-actions">
          <button
            className="btn btn-ghost"
            onClick={() => {
              setCreateOpen(false);
              resetForm();
            }}
            disabled={creating}
          >
            Cancel
          </button>
          <button
            className="btn btn-primary"
            onClick={handleCreate}
            disabled={creating}
          >
            {creating ? (
              <>
                <span className="spinner" /> Creating…
              </>
            ) : (
              "Create workspace"
            )}
          </button>
        </div>
      </Modal>

      <ConfirmDialog
        open={!!toDelete}
        title="Delete workspace?"
        message={`"${toDelete?.name}" and all of its documents will be permanently removed. This cannot be undone.`}
        confirmLabel="Delete"
        busyLabel="Deleting…"
        busy={deleting}
        danger
        onConfirm={handleDelete}
        onClose={() => !deleting && setToDelete(null)}
      />
    </main>
  );
}
