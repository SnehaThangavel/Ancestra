import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useApp } from "../../context/AppContext";
import { AIProgress } from "../../components/expert/AIProgress";
import { analyzeHeritageImage } from "../../services/mockAIService";
import { Cpu, ShieldAlert, Sparkles } from "lucide-react";

export function AIAnalysisPage() {
  const navigate = useNavigate();
  const { pendingAnalysis, recordAssessmentResult } = useApp();
  const [activeStep, setActiveStep] = useState(1);

  const imageSrc =
    pendingAnalysis?.imageUrl ||
    "https://images.unsplash.com/photo-1582510003544-4d00b7f74220?auto=format&fit=crop&q=80&w=800";

  useEffect(() => {
    // Step animation interval over 3 seconds (9 steps)
    const stepInterval = setInterval(() => {
      setActiveStep((prev) => {
        if (prev < 9) return prev + 1;
        return prev;
      });
    }, 320);

    // Call mock AI Service
    let isMounted = true;
    analyzeHeritageImage({
      siteId: pendingAnalysis?.siteId,
      siteName: pendingAnalysis?.siteName,
      regionId: pendingAnalysis?.regionId,
      regionName: pendingAnalysis?.regionName,
      imagePreviewUrl: imageSrc
    }).then((result) => {
      if (isMounted) {
        recordAssessmentResult(result);
        setTimeout(() => {
          navigate("/expert/results");
        }, 600);
      }
    });

    return () => {
      isMounted = false;
      clearInterval(stepInterval);
    };
  }, []);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
      <div>
        <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "4px" }}>
          <span className="module-badge">PROC-04</span>
          <h1 className="font-serif-heading" style={{ fontSize: "22px", margin: 0 }}>
            AI COMPUTER VISION PERCEPTION PIPELINE
          </h1>
        </div>
        <p style={{ fontSize: "13px", color: "var(--text-secondary)" }}>
          Executing neural lithic damage segmentation and structural stress index calculation for{" "}
          <strong>{pendingAnalysis?.regionName || "East-Facing Rajasimhesvara Vimana"}</strong>.
        </p>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1.2fr 1fr", gap: "24px" }}>
        {/* Uploaded Image View Card */}
        <div className="ancestra-card" style={{ padding: "16px" }}>
          <div style={styles.imageCardHeader}>
            <span style={styles.imageTitle}>TARGET OBSERVATION FRAME</span>
            <span className="label-code">RESOLUTION: 6000x4000 (RAW)</span>
          </div>

          <div style={styles.imageContainer}>
            <img src={imageSrc} alt="Target Observation" style={styles.previewImg} />
            <div style={styles.scanOverlay}>
              <div style={styles.scanLine} />
              <div style={styles.scanningBadge}>
                <Sparkles size={12} color="#FFFFFF" />
                <span>AI COMPUTER VISION SEGMENTATION IN PROGRESS</span>
              </div>
            </div>
          </div>

          <div style={styles.metaRow}>
            <div>
              <span className="label-uppercase">HERITAGE SITE:</span>
              <div style={{ fontWeight: 600, fontSize: "12px" }}>
                {pendingAnalysis?.siteName || "Shore Temple, Mahabalipuram"}
              </div>
            </div>
            <div>
              <span className="label-uppercase">ARCHITECTURAL REGION:</span>
              <div style={{ fontWeight: 600, fontSize: "12px" }}>
                {pendingAnalysis?.regionName || "East-Facing Rajasimhesvara Vimana"}
              </div>
            </div>
          </div>
        </div>

        {/* Right Processing Steps */}
        <div className="ancestra-card">
          <AIProgress activeStep={activeStep} totalSteps={9} />
        </div>
      </div>
    </div>
  );
}

const styles = {
  imageCardHeader: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    marginBottom: "12px"
  },
  imageTitle: {
    fontSize: "11px",
    fontFamily: "var(--font-sans)",
    fontWeight: "700",
    letterSpacing: "0.08em",
    color: "#8E857B"
  },
  imageContainer: {
    position: "relative",
    width: "100%",
    height: "360px",
    borderRadius: "4px",
    overflow: "hidden",
    backgroundColor: "#1C1917"
  },
  previewImg: {
    width: "100%",
    height: "100%",
    objectFit: "cover",
    opacity: 0.85
  },
  scanOverlay: {
    position: "absolute",
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    pointerEvents: "none"
  },
  scanLine: {
    position: "absolute",
    left: 0,
    right: 0,
    height: "2px",
    backgroundColor: "#A04022",
    boxShadow: "0 0 12px #A04022",
    top: "40%"
  },
  scanningBadge: {
    position: "absolute",
    bottom: "12px",
    left: "12px",
    backgroundColor: "rgba(160, 64, 34, 0.9)",
    color: "#FFFFFF",
    fontSize: "10px",
    fontFamily: "var(--font-mono)",
    fontWeight: "700",
    padding: "4px 10px",
    borderRadius: "4px",
    display: "flex",
    alignItems: "center",
    gap: "6px"
  },
  metaRow: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    marginTop: "14px",
    paddingTop: "12px",
    borderTop: "1px solid var(--border-light)"
  }
};
