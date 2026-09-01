import React from "react";
import { X } from "lucide-react";

export function Modal({ isOpen, onClose, title, children, width = "540px" }) {
  if (!isOpen) return null;

  return (
    <div style={styles.overlay} onClick={onClose}>
      <div
        style={{ ...styles.modalBox, width }}
        onClick={(e) => e.stopPropagation()}
        className="paper-grid"
      >
        <div style={styles.header}>
          <h3 className="font-serif-heading" style={{ fontSize: "16px", margin: 0 }}>
            {title}
          </h3>
          <button style={styles.closeBtn} onClick={onClose}>
            <X size={16} color="#78716C" />
          </button>
        </div>
        <div style={styles.body}>{children}</div>
      </div>
    </div>
  );
}

const styles = {
  overlay: {
    position: "fixed",
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: "rgba(28, 25, 23, 0.45)",
    backdropFilter: "blur(2px)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    zIndex: 100
  },
  modalBox: {
    backgroundColor: "#FFFFFF",
    border: "1px solid var(--border-color)",
    borderRadius: "8px",
    boxShadow: "0 10px 25px -5px rgba(0,0,0,0.1)",
    maxHeight: "90vh",
    display: "flex",
    flexDirection: "column",
    overflow: "hidden"
  },
  header: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    padding: "14px 18px",
    borderBottom: "1px solid var(--border-color)",
    backgroundColor: "#F9F7F2"
  },
  closeBtn: {
    background: "none",
    border: "none",
    cursor: "pointer",
    padding: "2px",
    borderRadius: "4px"
  },
  body: {
    padding: "18px",
    overflowY: "auto"
  }
};
