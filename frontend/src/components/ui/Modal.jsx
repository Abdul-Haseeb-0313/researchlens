import { useEffect } from "react";
import { X } from "lucide-react";

export default function Modal({
  open,
  onClose,
  title,
  subtitle,
  children,
  closable = true,
}) {
  useEffect(() => {
    if (!open) return;
    const onKey = (e) => e.key === "Escape" && closable && onClose?.();
    document.addEventListener("keydown", onKey);
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = "";
    };
  }, [open, closable, onClose]);

  if (!open) return null;

  return (
    <div
      className="overlay"
      onMouseDown={(e) =>
        e.target === e.currentTarget && closable && onClose?.()
      }
    >
      <div className="card modal" role="dialog" aria-modal="true">
        <div className="modal-head">
          <div>
            <h3>{title}</h3>
            {subtitle && <p>{subtitle}</p>}
          </div>
          {closable && (
            <button className="btn-icon" onClick={onClose} aria-label="Close">
              <X size={18} />
            </button>
          )}
        </div>
        {children}
      </div>
    </div>
  );
}
