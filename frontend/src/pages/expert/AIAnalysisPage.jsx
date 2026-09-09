import React, { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useApp } from "../../context/AppContext";
import { AIProgress } from "../../components/expert/AIProgress";
import { analyzeHeritageImage } from "../../services/mockAIService";
import { api } from "../../services/api";
import { Sparkles } from "lucide-react";

export function AIAnalysisPage() {
  const navigate = useNavigate();
  const { pendingAnalysis, recordAssessmentResult, isPipelineComplete, isAuthenticated } = useApp();

  const imageSrc =
    pendingAnalysis?.imageUrl ||
    "https://images.unsplash.com/photo-1582510003544-4d00b7f74220?auto=format&fit=crop&q=80&w=800";

  useEffect(() => {
    async function executeAnalysis() {
      // 1. If real file is provided and user is authenticated, submit to backend
      let backendObservation = null;
      if (pendingAnalysis?.imageFile && isAuthenticated) {
        try {
          backendObservation = await api.uploadObservation({
            monumentId: pendingAnalysis.siteId || "a0000000-0000-0000-0000-000000000001",
            imageFile: pendingAnalysis.imageFile,
            metadata: {
              region_id: pendingAnalysis.regionId,
              capture_date: pendingAnalysis.captureDate,
              sensor_spec: pendingAnalysis.sensorSpec,
              notes: pendingAnalysis.notes,
            },
          });
        } catch (apiErr) {
          console.warn("Backend observation upload notice (falling back to local AI service):", apiErr);
        }
      }

      // 2. Perform perceptual analysis & damage segmentation
      const result = await analyzeHeritageImage({
        siteId: pendingAnalysis?.siteId,
        siteName: pendingAnalysis?.siteName,
        regionId: pendingAnalysis?.regionId,
        regionName: pendingAnalysis?.regionName,
        imagePreviewUrl: imageSrc,
      });

      if (backendObservation?.id) {
        result.observationId = backendObservation.id;
      }

      recordAssessmentResult(result);
    }

    executeAnalysis();
  }, []);

  const handleNavigateResults = () => {
    navigate("/expert/results");
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
      <div>
        <h1 className="font-serif-heading" style={{ fontSize: "22px", margin: "0 0 4px 0" }}>
          AI COMPUTER VISION PERCEPTION PIPELINE
        </h1>
        <p style={{ fontSize: "13px", color: "var(--text-secondary)" }}>
          Executing neural lithic damage segmentation and structural stress index calculation for{" "}
          <strong>{pendingAnalysis?.regionName || "East-Facing Rajasimhesvara Vimana"}</strong>.
        </p>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1.3fr", gap: "24px", alignItems: "flex-start" }}>
        {/* Left Target Frame Card (Slightly Expanded Spacing & Comfortable Breathing Room) */}
        <div className="ancestra-card" style={{ padding: "20px 22px 22px 22px", display: "flex", flexDirection: "column" }}>
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
                <span>
                  {isPipelineComplete
                    ? "NEURAL SEGMENTATION COMPLETE"
                    : "AI COMPUTER VISION SEGMENTATION IN PROGRESS"}
                </span>
              </div>
            </div>
          </div>

          {/* Expanded Padding & Spacing for Site Details */}
          <div style={styles.metaRow}>
            <div>
              <span className="label-uppercase">HERITAGE SITE:</span>
              <div style={{ fontWeight: 600, fontSize: "13px", marginTop: "4px", color: "#1C1917", lineHeight: "1.35" }}>
                {pendingAnalysis?.siteName || "Shore Temple, Mahabalipuram"}
              </div>
            </div>
            <div>
              <span className="label-uppercase">ARCHITECTURAL REGION:</span>
              <div style={{ fontWeight: 600, fontSize: "13px", marginTop: "4px", color: "#1C1917", lineHeight: "1.35" }}>
                {pendingAnalysis?.regionName || "East-Facing Rajasimhesvara Vimana"}
              </div>
            </div>
          </div>
        </div>

        {/* Right Processing Steps Card */}
        <div className="ancestra-card">
          <AIProgress onCompleteResults={handleNavigateResults} />
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
    marginBottom: "14px" // Slightly expanded spacing below header
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
    height: "270px", // Comfortable proportional height
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
    alignItems: "flex-start",
    justifyContent: "space-between",
    gap: "16px",
    marginTop: "16px", // Slightly expanded spacing between image and details
    paddingTop: "14px",
    borderTop: "1px solid var(--border-light)"
  }
};
