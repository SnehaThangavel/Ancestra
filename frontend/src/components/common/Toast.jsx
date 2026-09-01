import React from "react";
import { CheckCircle2, AlertCircle, Info, X } from "lucide-react";

export function Toast({ toast, onClose }) {
  if (!toast) return null;

  return (
    <div style={styles.toastContainer}>
      <div style={styles.toastBox}>
        {toast.type === "error" ? (
          <AlertCircle size={16} color="#DC2626" />
        ) : (
          <CheckCircle2 size={16} color="#16A34A" />
        )}
        <span style={styles.messageText}>{toast.message}</span>
        <button onClick={onClose} style={styles.closeBtn}>
          <X size={14} color="#78716C" />
        </button>
      </div>
    </div>
  );
}

const styles = {
  toastContainer: {
    position: "fixed",
    bottom: "24px",
    right: "24px",
    zIndex: 1000,
    animation: "slideUp 0.2s ease"
  },
  toastBox: {
    display: "flex",
    alignItems: "center",
    gap: "10px",
    backgroundColor: "#FFFFFF",
    border: "1px solid var(--border-color)",
    borderLeft: "4px solid var(--accent-primary)",
    borderRadius: "6px",
    padding: "12px 16px",
    boxShadow: "0 10px 25px -5px rgba(28, 25, 23, 0.15)",
    minWidth: "280px"
  },
  messageText: {
    fontSize: "12px",
    fontFamily: "var(--font-sans)",
    fontWeight: "600",
    color: "var(--text-primary)",
    flex: 1
  },
  closeBtn: {
    background: "none",
    border: "none",
    cursor: "pointer",
    padding: "2px",
    display: "flex",
    alignItems: "center"
  }
};
