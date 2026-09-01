import React, { useState, useRef } from "react";
import { UploadCloud, Image as ImageIcon, X, RefreshCw } from "lucide-react";

export function ImageUploaderInput({ value, onChange, label = "HERITAGE SITE PHOTOGRAPH *" }) {
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef(null);

  const handleFileChange = (file) => {
    if (!file) return;
    if (!file.type.startsWith("image/")) {
      alert("Please select a valid image file (JPG, PNG, WEBP).");
      return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
      onChange(e.target.result);
    };
    reader.readAsDataURL(file);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileChange(e.dataTransfer.files[0]);
    }
  };

  const handleRemove = () => {
    onChange("");
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  return (
    <div className="form-group" style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
      <label className="form-label">{label}</label>

      {/* Hidden File Input */}
      <input
        ref={fileInputRef}
        type="file"
        accept="image/jpeg,image/png,image/jpg,image/webp"
        style={{ display: "none" }}
        onChange={(e) => {
          if (e.target.files && e.target.files[0]) {
            handleFileChange(e.target.files[0]);
          }
        }}
      />

      {/* Upload Box / Image Preview Area */}
      {value ? (
        <div style={styles.previewCard}>
          <img src={value} alt="Site Preview" style={styles.previewImage} />
          <div style={styles.previewOverlay}>
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="btn-secondary"
              style={{ padding: "4px 10px", fontSize: "11px", backgroundColor: "#FFFFFF" }}
            >
              <RefreshCw size={12} color="#A04022" />
              <span>Replace Image</span>
            </button>
            <button
              type="button"
              onClick={handleRemove}
              className="btn-outline-danger"
              style={{ padding: "4px 10px", fontSize: "11px", backgroundColor: "#FFFFFF" }}
            >
              <X size={12} />
              <span>Remove</span>
            </button>
          </div>
        </div>
      ) : (
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          style={{
            ...styles.dropZone,
            backgroundColor: isDragging ? "#F4EBE6" : "#FAF8F5",
            borderColor: isDragging ? "#A04022" : "#D1C9BF"
          }}
        >
          <div style={styles.dropZoneContent}>
            <div style={styles.iconCircle}>
              <UploadCloud size={20} color="#A04022" />
            </div>
            <div style={{ textAlign: "center" }}>
              <span style={{ fontSize: "12.5px", fontWeight: 600, color: "var(--text-primary)" }}>
                Drag and drop image here, or{" "}
                <span style={{ color: "var(--accent-primary)", textDecoration: "underline", cursor: "pointer" }}>
                  Choose from my Device
                </span>
              </span>
              <div style={{ fontSize: "10.5px", color: "var(--text-muted)", marginTop: "4px" }}>
                Supports JPG, JPEG, PNG, WEBP high-resolution photogrammetric imagery
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

const styles = {
  dropZone: {
    border: "2px dashed #D1C9BF",
    borderRadius: "6px",
    padding: "20px",
    cursor: "pointer",
    transition: "all 0.15s ease",
    display: "flex",
    alignItems: "center",
    justifyContent: "center"
  },
  dropZoneContent: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    gap: "10px"
  },
  iconCircle: {
    width: "38px",
    height: "38px",
    borderRadius: "50%",
    backgroundColor: "#F7EDE9",
    display: "flex",
    alignItems: "center",
    justifyContent: "center"
  },
  previewCard: {
    position: "relative",
    width: "100%",
    height: "180px",
    borderRadius: "6px",
    overflow: "hidden",
    border: "1px solid var(--border-color)",
    backgroundColor: "#1C1917"
  },
  previewImage: {
    width: "100%",
    height: "100%",
    objectFit: "cover"
  },
  previewOverlay: {
    position: "absolute",
    bottom: 0,
    left: 0,
    right: 0,
    padding: "8px 12px",
    backgroundColor: "rgba(28, 25, 23, 0.75)",
    display: "flex",
    alignItems: "center",
    justifyContent: "flex-end",
    gap: "10px"
  }
};
