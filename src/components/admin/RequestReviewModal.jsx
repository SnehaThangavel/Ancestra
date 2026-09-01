import React, { useState } from "react";
import { useApp } from "../../context/AppContext";
import { Modal } from "../common/Modal";
import { CheckCircle, PlusCircle, XCircle, AlertTriangle } from "lucide-react";

export function RequestReviewModal({ isOpen, onClose, request, onAddDetails }) {
  const { acceptSiteRequest, rejectSiteRequest } = useApp();

  const [isRejecting, setIsRejecting] = useState(false);
  const [rejectionReason, setRejectionReason] = useState("");

  if (!request) return null;

  const handleAccept = () => {
    acceptSiteRequest(request.id);
    onClose();
  };

  const handleAddDetails = () => {
    onClose();
    onAddDetails(request);
  };

  const handleConfirmReject = (e) => {
    e.preventDefault();
    if (!rejectionReason.trim()) {
      alert("Please provide a reason for rejecting the site request.");
      return;
    }
    rejectSiteRequest(request.id, rejectionReason);
    setIsRejecting(false);
    setRejectionReason("");
    onClose();
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={`REVIEW HERITAGE SITE REQUEST: ${request.id}`}
      width="600px"
    >
      <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
        {/* Request Meta Info */}
        <div style={styles.metaGrid}>
          <div>
            <span className="label-uppercase">REQUESTED SITE NAME</span>
            <div style={{ fontWeight: "700", fontSize: "14px", color: "var(--text-primary)" }}>
              {request.siteName}
            </div>
          </div>
          <div>
            <span className="label-uppercase">LOCATION & STATE</span>
            <div style={{ fontWeight: "600", fontSize: "12.5px" }}>{request.location}</div>
          </div>
          <div>
            <span className="label-uppercase">REQUESTING EXPERT</span>
            <div style={{ fontWeight: "600", fontSize: "12.5px" }}>{request.expertName}</div>
          </div>
          <div>
            <span className="label-uppercase">SUBMISSION DATE</span>
            <div style={{ fontFamily: "var(--font-mono)", fontSize: "12px" }}>{request.createdAt}</div>
          </div>
        </div>

        {/* Uploaded Photograph */}
        <div>
          <span className="label-uppercase" style={{ marginBottom: "6px", display: "block" }}>
            SUBMITTED PHOTOGRAMMETRIC IMAGE
          </span>
          <div style={styles.imagePreviewBox}>
            <img src={request.image} alt={request.siteName} style={styles.siteImage} />
          </div>
        </div>

        {/* Detailed Fields */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
          <div>
            <span className="label-uppercase">ASI CIRCLE:</span>
            <div style={{ fontSize: "12px", fontWeight: 600 }}>{request.circle}</div>
          </div>
          <div>
            <span className="label-uppercase">CONSTRUCTION MATERIAL:</span>
            <div style={{ fontSize: "12px", fontWeight: 600 }}>{request.material}</div>
          </div>
        </div>

        <div>
          <span className="label-uppercase">ARCHITECTURAL DESCRIPTION:</span>
          <p style={{ fontSize: "12px", color: "var(--text-secondary)", marginTop: "4px", lineHeight: "1.4" }}>
            {request.description || "No description provided."}
          </p>
        </div>

        {/* Rejection Input Mode */}
        {isRejecting ? (
          <form onSubmit={handleConfirmReject} style={styles.rejectionBox}>
            <div style={{ display: "flex", alignItems: "center", gap: "6px", marginBottom: "6px" }}>
              <AlertTriangle size={14} color="#DC2626" />
              <strong style={{ fontSize: "12px", color: "#DC2626" }}>SPECIFY REJECTION REASON *</strong>
            </div>
            <textarea
              className="form-textarea"
              rows="2"
              placeholder="e.g. Duplicate heritage site record, or insufficient architectural evidence..."
              value={rejectionReason}
              onChange={(e) => setRejectionReason(e.target.value)}
              required
            />
            <div style={{ display: "flex", justifyContent: "flex-end", gap: "8px", marginTop: "8px" }}>
              <button
                type="button"
                onClick={() => setIsRejecting(false)}
                className="btn-secondary"
                style={{ padding: "4px 10px", fontSize: "11px" }}
              >
                Cancel
              </button>
              <button
                type="submit"
                className="btn-primary"
                style={{ backgroundColor: "#DC2626", borderColor: "#DC2626", padding: "4px 12px", fontSize: "11px" }}
              >
                Confirm Rejection
              </button>
            </div>
          </form>
        ) : (
          /* Three Action Buttons */
          <div style={styles.actionRow}>
            <button onClick={handleAccept} className="btn-secondary">
              <CheckCircle size={14} color="#16A34A" />
              <span>1. Accept</span>
            </button>

            <button onClick={handleAddDetails} className="btn-primary">
              <PlusCircle size={14} />
              <span>2. Add New Site Details</span>
            </button>

            <button onClick={() => setIsRejecting(true)} className="btn-outline-danger">
              <XCircle size={14} />
              <span>3. Reject</span>
            </button>
          </div>
        )}
      </div>
    </Modal>
  );
}

const styles = {
  metaGrid: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr",
    gap: "12px",
    paddingBottom: "12px",
    borderBottom: "1px solid var(--border-light)"
  },
  imagePreviewBox: {
    width: "100%",
    height: "200px",
    borderRadius: "6px",
    overflow: "hidden",
    backgroundColor: "#1C1917"
  },
  siteImage: {
    width: "100%",
    height: "100%",
    objectFit: "cover"
  },
  rejectionBox: {
    backgroundColor: "#FEF2F2",
    border: "1px solid #FCA5A5",
    borderRadius: "6px",
    padding: "12px",
    marginTop: "8px"
  },
  actionRow: {
    display: "flex",
    alignItems: "center",
    justifyContent: "flex-end",
    gap: "10px",
    paddingTop: "14px",
    borderTop: "1px solid var(--border-light)"
  }
};
