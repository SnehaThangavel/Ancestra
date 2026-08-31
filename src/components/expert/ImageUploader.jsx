import React, { useRef } from "react";
import { UploadCloud, Image as ImageIcon, CheckCircle } from "lucide-react";

export function ImageUploader({ selectedImage, onImageSelect, sampleImages = [] }) {
  const fileInputRef = useRef(null);

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      const url = URL.createObjectURL(file);
      onImageSelect({ file, url, name: file.name });
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file) {
      const url = URL.createObjectURL(file);
      onImageSelect({ file, url, name: file.name });
    }
  };

  return (
    <div>
      <div
        onDragOver={(e) => e.preventDefault()}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        style={styles.dropZone}
      >
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileChange}
          accept="image/png, image/jpeg, image/jpg, image/tiff"
          style={{ display: "none" }}
        />

        {selectedImage ? (
          <div style={styles.previewBox}>
            <img src={selectedImage.url} alt="Selected Heritage Asset" style={styles.previewImage} />
            <div style={styles.previewMeta}>
              <div style={styles.previewSuccess}>
                <CheckCircle size={14} color="#16A34A" />
                <span style={{ fontSize: "11px", fontWeight: 600, color: "#16A34A" }}>
                  IMAGE READY FOR CV ANALYSIS
                </span>
              </div>
              <span style={{ fontSize: "11px", fontFamily: "var(--font-mono)", color: "var(--text-muted)" }}>
                {selectedImage.name || "heritage_observation_raw.jpg"}
              </span>
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  fileInputRef.current?.click();
                }}
                className="btn-secondary"
                style={{ padding: "4px 10px", fontSize: "11px", marginTop: "4px" }}
              >
                Change Image
              </button>
            </div>
          </div>
        ) : (
          <div style={styles.promptBox}>
            <div style={styles.iconCircle}>
              <UploadCloud size={24} color="#A04022" />
            </div>
            <div style={styles.promptTitle}>Drop heritage imagery file here</div>
            <div style={styles.promptSubtitle}>OR CLICK TO CHOOSE FROM LOCAL DEVICE</div>
            <div style={styles.supportedText}>SUPPORTED FORMATS: RAW, LOSSLESS TIFF, JPEG, PNG (UP TO 50MB)</div>
          </div>
        )}
      </div>

      {/* Preset Sample Images for Fast Testing */}
      {sampleImages.length > 0 && (
        <div style={styles.sampleContainer}>
          <span style={styles.sampleLabel}>OR SELECT PRESET TEST ASSET:</span>
          <div style={styles.sampleGrid}>
            {sampleImages.map((sample, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => onImageSelect({ url: sample.url, name: sample.name })}
                style={{
                  ...styles.sampleBtn,
                  ...(selectedImage?.url === sample.url ? styles.sampleBtnActive : {})
                }}
              >
                <img src={sample.url} alt={sample.name} style={styles.sampleThumb} />
                <span style={styles.sampleName}>{sample.name}</span>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

const styles = {
  dropZone: {
    border: "2px dashed var(--border-color)",
    borderRadius: "6px",
    backgroundColor: "#FAF8F5",
    padding: "24px",
    textAlign: "center",
    cursor: "pointer",
    transition: "border-color 0.15s ease, background-color 0.15s ease"
  },
  promptBox: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    gap: "6px"
  },
  iconCircle: {
    width: "44px",
    height: "44px",
    borderRadius: "50%",
    backgroundColor: "#F7EDE9",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    marginBottom: "4px"
  },
  promptTitle: {
    fontFamily: "var(--font-serif)",
    fontWeight: "600",
    fontSize: "15px",
    color: "var(--text-primary)"
  },
  promptSubtitle: {
    fontSize: "10.5px",
    fontFamily: "var(--font-sans)",
    fontWeight: "700",
    letterSpacing: "0.08em",
    color: "var(--accent-primary)"
  },
  supportedText: {
    fontSize: "10px",
    fontFamily: "var(--font-mono)",
    color: "var(--text-muted)",
    marginTop: "4px"
  },
  previewBox: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    gap: "12px"
  },
  previewImage: {
    maxHeight: "220px",
    maxWidth: "100%",
    borderRadius: "4px",
    border: "1px solid var(--border-color)",
    objectFit: "cover"
  },
  previewMeta: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    gap: "4px"
  },
  previewSuccess: {
    display: "flex",
    alignItems: "center",
    gap: "6px"
  },
  sampleContainer: {
    marginTop: "14px",
    paddingTop: "12px",
    borderTop: "1px dashed var(--border-light)"
  },
  sampleLabel: {
    fontSize: "10px",
    fontWeight: "700",
    letterSpacing: "0.08em",
    color: "var(--text-muted)",
    display: "block",
    marginBottom: "8px"
  },
  sampleGrid: {
    display: "flex",
    gap: "10px"
  },
  sampleBtn: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
    padding: "6px 10px",
    backgroundColor: "#FFFFFF",
    border: "1px solid var(--border-color)",
    borderRadius: "4px",
    cursor: "pointer",
    transition: "all 0.15s ease"
  },
  sampleBtnActive: {
    borderColor: "var(--accent-primary)",
    backgroundColor: "var(--accent-primary-light)"
  },
  sampleThumb: {
    width: "28px",
    height: "28px",
    borderRadius: "3px",
    objectFit: "cover"
  },
  sampleName: {
    fontSize: "11px",
    fontWeight: "600",
    color: "var(--text-primary)"
  }
};
