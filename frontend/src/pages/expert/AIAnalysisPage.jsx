import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useApp } from "../../context/AppContext";
import { AIProgress } from "../../components/expert/AIProgress";
import { api } from "../../services/api";
import { toTitleCase } from "../../utils/formatters";
import { Sparkles } from "lucide-react";

export function AIAnalysisPage() {
  const navigate = useNavigate();
  const {
    pendingAnalysis,
    recordAssessmentResult,
    isPipelineComplete,
    pipelineStep,
    advancePipelineStep,
    completeAllPipelineSteps,
    resetPipeline
  } = useApp();
  const [analysisError, setAnalysisError] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);

  const imageSrc =
    pendingAnalysis?.imageUrl ||
    "https://images.unsplash.com/photo-1582510003544-4d00b7f74220?auto=format&fit=crop&q=80&w=800";

  const delay = (ms) => new Promise((res) => setTimeout(res, ms));

  useEffect(() => {
    let isCancelled = false;

    async function executeLiveAnalysis() {
      if (!pendingAnalysis || isCancelled) return;

      try {
        setAnalysisError(null);
        setIsProcessing(true);
        resetPipeline();

        if (!pendingAnalysis.imageFile) {
          throw new Error("No image file loaded for analysis. Please return to Image Analysis intake.");
        }
        if (!pendingAnalysis.siteId || !pendingAnalysis.regionId) {
          throw new Error("Target monument and architectural region must both be specified.");
        }

        // Stage 1 & 2: Photometric calibration & spatial polygon anchoring
        await delay(450);
        if (isCancelled) return;
        advancePipelineStep(); // Step 2

        // Stage 3 & 4: Upload observation to backend Module 1 (Registration & Ingestion)
        const uploadResp = await api.uploadObservation({
          monumentId: pendingAnalysis.siteId,
          regionId: pendingAnalysis.regionId,
          imageFile: pendingAnalysis.imageFile,
          metadata: {
            capture_date: pendingAnalysis.captureDate,
            sensor_spec: pendingAnalysis.sensorSpec,
            notes: pendingAnalysis.notes,
          },
        });

        await delay(400);
        if (isCancelled) return;
        advancePipelineStep(); // Step 3
        await delay(350);
        advancePipelineStep(); // Step 4

        const obsId = uploadResp?.observation_id;
        if (!obsId) {
          throw new Error("Backend failed to ingest observation photograph.");
        }

        // Stage 5 & 6: Execute SSIM Anomaly Validation & Segmentation (Module 4)
        await delay(400);
        if (isCancelled) return;
        advancePipelineStep(); // Step 5

        const valResp = await api.verifyObservation({
          observationId: obsId,
          regionId: pendingAnalysis.regionId,
        });

        if (!valResp || typeof valResp.severity_score !== "number" || typeof valResp.ssim_score !== "number") {
          throw new Error("Structural anomaly verification failed: invalid response received from inspection engine.");
        }

        await delay(400);
        if (isCancelled) return;
        advancePipelineStep(); // Step 6

        const severityScore = valResp.severity_score;
        const ssimScore = valResp.ssim_score;
        const anomalyType = valResp.anomaly_type ? toTitleCase(valResp.anomaly_type) : "Structural Anomaly";
        const ssimDelta = typeof valResp.ssim_delta === "number" ? valResp.ssim_delta : (1.0 - ssimScore);

        const severityLabel = severityScore > 0.40 ? "High" : severityScore > 0.15 ? "Medium" : "Low";
        const emergencyLabel = severityScore > 0.40 ? "Critical" : severityScore > 0.20 ? "Urgent" : "Attention";

        // Stage 7: Severity & Risk Scoring
        await delay(350);
        if (isCancelled) return;
        advancePipelineStep(); // Step 7

        // Stage 8: Temporal Consensus Matrix
        await delay(350);
        if (isCancelled) return;
        advancePipelineStep(); // Step 8

        const resultObj = {
          id: valResp.validation_id ? `ASM-${String(valResp.validation_id).substring(0, 8).toUpperCase()}` : `ASM-${obsId.substring(0, 8).toUpperCase()}`,
          validation_id: valResp.validation_id,
          observation_id: obsId,
          siteId: pendingAnalysis.siteId,
          siteName: pendingAnalysis.siteName || "Monument",
          regionId: pendingAnalysis.regionId,
          regionCode: `REG-${String(pendingAnalysis.regionId).substring(0, 4).toUpperCase()}`,
          regionName: pendingAnalysis.regionName || "Architectural Region",
          date: pendingAnalysis.captureDate || new Date().toISOString().split("T")[0],
          damageType: anomalyType,
          severity: severityLabel,
          severity_score: severityScore,
          ssim_score: ssimScore,
          ssim_delta: ssimDelta,
          confidence: ssimScore,
          damageTrend: severityScore > 0.2 ? "Increasing" : "Stable",
          emergencyLevel: emergencyLabel,
          recommendation: severityScore > 0.2
            ? "Immediate conservation inspection and structural shoring recommended."
            : "Routine quarterly monitoring recommended.",
          status: "Pending Review",
          imageUrl: imageSrc,
          defect_bounding_boxes: valResp.defect_bounding_boxes || [],
          expertNotes: `Observation registered with alignment confidence ${uploadResp.registration_confidence !== undefined ? uploadResp.registration_confidence.toFixed(2) : "1.00"}. SSIM defect verification completed.`,
        };

        recordAssessmentResult(resultObj);

        // Stage 9: Conservation Recommendation (Complete)
        await delay(350);
        if (isCancelled) return;
        completeAllPipelineSteps();
        setIsProcessing(false);
      } catch (err) {
        if (!isCancelled) {
          console.error("Live analysis pipeline error:", err);
          setAnalysisError(err.message || "An error occurred during structural analysis.");
          setIsProcessing(false);
        }
      }
    }

    executeLiveAnalysis();

    return () => {
      isCancelled = true;
    };
  }, [pendingAnalysis]);

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
          <strong>{pendingAnalysis?.regionName || "Selected Region"}</strong>.
        </p>
      </div>

      {!pendingAnalysis && (
        <div style={{ padding: "16px 20px", backgroundColor: "#F7EDE9", border: "1px solid rgba(160, 64, 34, 0.3)", borderRadius: "6px", display: "flex", alignItems: "center", justifyContent: "space-between", gap: "14px" }}>
          <div>
            <div style={{ fontWeight: 700, color: "#A04022", fontSize: "13px" }}>NO ACTIVE OBSERVATION IMAGE LOADED</div>
            <div style={{ color: "#78716C", fontSize: "12px", marginTop: "2px" }}>
              Please load an observation photo from the Image Analysis workspace or select a heritage site region to trigger the live computer vision pipeline.
            </div>
          </div>
          <button
            onClick={() => navigate("/expert/image-analysis")}
            className="btn-primary"
            style={{ padding: "8px 16px", fontSize: "12px", flexShrink: 0 }}
          >
            Go to Image Analysis
          </button>
        </div>
      )}

      {analysisError && (
        <div style={{ padding: "16px 20px", backgroundColor: "#FEF2F2", border: "1px solid #FCA5A5", borderRadius: "6px", display: "flex", alignItems: "center", justifyContent: "space-between", gap: "14px" }}>
          <div>
            <div style={{ fontWeight: 700, color: "#DC2626", fontSize: "13px" }}>ANALYSIS PIPELINE FAILED</div>
            <div style={{ color: "#991B1B", fontSize: "12px", marginTop: "2px" }}>{analysisError}</div>
          </div>
          <button
            onClick={() => navigate("/expert/image-analysis")}
            className="btn-secondary"
            style={{ padding: "6px 12px", fontSize: "11px", flexShrink: 0 }}
          >
            Back to Image Intake
          </button>
        </div>
      )}

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1.3fr", gap: "24px", alignItems: "flex-start" }}>
        {/* Left Target Frame Card */}
        <div className="ancestra-card" style={{ padding: "20px 22px 22px 22px", display: "flex", flexDirection: "column" }}>
          <div style={styles.imageCardHeader}>
            <span style={styles.imageTitle}>TARGET OBSERVATION FRAME</span>
            <span className="label-code">PROCESSED VIA FASTAPI / OPENCV</span>
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

          <div style={styles.metaRow}>
            <div>
              <span className="label-uppercase">HERITAGE SITE:</span>
              <div style={{ fontWeight: 600, fontSize: "13px", marginTop: "4px", color: "#1C1917", lineHeight: "1.35" }}>
                {pendingAnalysis?.siteName || "Selected Monument"}
              </div>
            </div>
            <div>
              <span className="label-uppercase">ARCHITECTURAL REGION:</span>
              <div style={{ fontWeight: 600, fontSize: "13px", marginTop: "4px", color: "#1C1917", lineHeight: "1.35" }}>
                {pendingAnalysis?.regionName || "Selected Region"}
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
    marginBottom: "14px",
  },
  imageTitle: {
    fontSize: "11px",
    fontFamily: "var(--font-sans)",
    fontWeight: "700",
    letterSpacing: "0.08em",
    color: "#8E857B",
  },
  imageContainer: {
    position: "relative",
    width: "100%",
    height: "270px",
    borderRadius: "4px",
    overflow: "hidden",
    backgroundColor: "#1C1917",
  },
  previewImg: {
    width: "100%",
    height: "100%",
    objectFit: "cover",
    opacity: 0.85,
  },
  scanOverlay: {
    position: "absolute",
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    pointerEvents: "none",
  },
  scanLine: {
    position: "absolute",
    left: 0,
    right: 0,
    height: "2px",
    backgroundColor: "#A04022",
    boxShadow: "0 0 12px #A04022",
    top: "40%",
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
    gap: "6px",
  },
  metaRow: {
    display: "flex",
    alignItems: "flex-start",
    justifyContent: "space-between",
    gap: "16px",
    marginTop: "16px",
    paddingTop: "14px",
    borderTop: "1px solid var(--border-light)",
  },
};
