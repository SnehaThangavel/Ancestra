import React from "react";
import { CheckCircle2, Circle, ArrowRight, RotateCcw, Play } from "lucide-react";
import { useApp } from "../../context/AppContext";

export function AIProgress({ onCompleteResults }) {
  const {
    pipelineStep,
    isPipelineComplete,
    advancePipelineStep,
    completeAllPipelineSteps,
    resetPipeline
  } = useApp();

  const steps = [
    { num: "01", name: "Photometric Calibration", desc: "Color-checker normalization & sensor noise floor correction" },
    { num: "02", name: "Spatial Polygon Anchoring", desc: "Aligning raw pixels with architectural region spatial polygon" },
    { num: "03", name: "Contrast & Noise Normalization", desc: "Shadow suppression & surface ambient lighting equalization" },
    { num: "04", name: "Lithic Texture Extraction", desc: "Granite/Sandstone grain texture segmentation & edge mapping" },
    { num: "05", name: "Crack Segmentation Masking", desc: "Convolutional neural mask output for primary shear fractures" },
    { num: "06", name: "Salt Efflorescence Estimation", desc: "White crust sodium chloride crystalline deposition detection" },
    { num: "07", name: "Severity & Risk Scoring", desc: "Computing structural load impairment percentage and threat level" },
    { num: "08", name: "Temporal Consensus Matrix", desc: "Weighting current observation against historical degradation log" },
    { num: "09", name: "Conservation Recommendation", desc: "Formulating automated emergency intervention protocol" }
  ];

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
      {/* Title Bar */}
      <div style={styles.headerRow}>
        <div>
          <h3 className="font-serif-heading" style={{ fontSize: "15px", margin: 0 }}>
            NEURAL PERCEPTION PIPELINE STEPS
          </h3>
          <div style={{ fontSize: "11px", color: "var(--text-secondary)", marginTop: "2px" }}>
            Step {pipelineStep} of 9 • {isPipelineComplete ? "Analysis Complete (Published)" : "Processing"}
          </div>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          {isPipelineComplete ? (
            <span style={styles.completeBadge}>✓ PUBLISHED</span>
          ) : (
            <span className="version-pill">STEP {pipelineStep}/9</span>
          )}
        </div>
      </div>

      {/* Static 9 Steps List */}
      <div style={styles.stepsList}>
        {steps.map((stepItem, idx) => {
          const stepNum = idx + 1;
          const isDone = isPipelineComplete ? true : stepNum < pipelineStep;
          const isCurrent = !isPipelineComplete && stepNum === pipelineStep;
          const isPending = !isPipelineComplete && stepNum > pipelineStep;

          return (
            <div
              key={stepItem.num}
              style={{
                ...styles.stepCard,
                ...(isDone ? styles.stepDone : {}),
                ...(isCurrent ? styles.stepCurrent : {}),
                ...(isPending ? styles.stepPending : {})
              }}
            >
              <div style={styles.iconCol}>
                {isDone ? (
                  <div style={styles.doneCheckCircle}>
                    <CheckCircle2 size={16} color="#16A34A" />
                  </div>
                ) : isCurrent ? (
                  <div style={styles.currentActiveDot}>
                    <span style={styles.activePulseDot} />
                  </div>
                ) : (
                  <Circle size={14} color="#A8A29E" />
                )}
              </div>

              <div style={{ flex: 1 }}>
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                  <span
                    style={{
                      ...styles.stepName,
                      color: isDone ? "#16A34A" : isCurrent ? "#A04022" : "#57534E",
                      fontWeight: isCurrent || isDone ? 700 : 500
                    }}
                  >
                    {stepItem.num}. {stepItem.name}
                  </span>

                  {isDone && <span style={styles.doneLabel}>VERIFIED</span>}
                  {isCurrent && <span style={styles.currentLabel}>IN PROGRESS</span>}
                  {isPending && <span style={styles.pendingLabel}>INACTIVE</span>}
                </div>

                <div style={{ fontSize: "11px", color: isDone ? "#15803D" : "var(--text-secondary)", marginTop: "2px" }}>
                  {stepItem.desc}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Manual Step Advancement Controls */}
      <div style={styles.controlsBar}>
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <button
            type="button"
            onClick={resetPipeline}
            className="btn-secondary"
            style={{ padding: "6px 10px", fontSize: "11px" }}
            title="Reset to Step 1"
          >
            <RotateCcw size={12} />
            <span>Reset</span>
          </button>

          {!isPipelineComplete && (
            <button
              type="button"
              onClick={advancePipelineStep}
              className="btn-secondary"
              style={{ padding: "6px 12px", fontSize: "11px", borderColor: "rgba(160, 64, 34, 0.4)" }}
            >
              <Play size={12} color="#A04022" />
              <span>Advance Step ({pipelineStep}/9)</span>
            </button>
          )}
        </div>

        <div>
          {!isPipelineComplete ? (
            <button
              type="button"
              onClick={completeAllPipelineSteps}
              className="btn-primary"
              style={{ padding: "6px 14px", fontSize: "11.5px" }}
            >
              <span>Process All 9 Steps</span>
              <ArrowRight size={13} />
            </button>
          ) : (
            <button
              type="button"
              onClick={onCompleteResults}
              className="btn-primary"
              style={{ padding: "6px 16px", fontSize: "11.5px", backgroundColor: "#16A34A", borderColor: "#16A34A" }}
            >
              <span>View Published AI Results</span>
              <ArrowRight size={13} />
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

const styles = {
  headerRow: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    paddingBottom: "10px",
    borderBottom: "1px solid var(--border-light)"
  },
  completeBadge: {
    backgroundColor: "#F0FDF4",
    color: "#16A34A",
    border: "1px solid #BBF7D0",
    borderRadius: "4px",
    padding: "2px 8px",
    fontSize: "10px",
    fontFamily: "var(--font-mono)",
    fontWeight: "700"
  },
  stepsList: {
    display: "flex",
    flexDirection: "column",
    gap: "6px"
  },
  stepCard: {
    display: "flex",
    alignItems: "flex-start",
    gap: "10px",
    padding: "8px 10px",
    borderRadius: "4px",
    border: "1px solid var(--border-light)",
    backgroundColor: "#FAF8F5",
    transition: "all 0.12s ease"
  },
  stepDone: {
    backgroundColor: "#F0FDF4",
    borderColor: "#DCFCE7"
  },
  stepCurrent: {
    backgroundColor: "#F7EDE9",
    borderColor: "rgba(160, 64, 34, 0.4)",
    boxShadow: "0 0 0 1px rgba(160, 64, 34, 0.15)"
  },
  stepPending: {
    backgroundColor: "#FAF8F5",
    opacity: 0.75
  },
  iconCol: {
    marginTop: "2px",
    flexShrink: 0
  },
  doneCheckCircle: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center"
  },
  currentActiveDot: {
    width: "14px",
    height: "14px",
    borderRadius: "50%",
    backgroundColor: "var(--accent-primary-light)",
    border: "2px solid var(--accent-primary)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center"
  },
  activePulseDot: {
    width: "4px",
    height: "4px",
    borderRadius: "50%",
    backgroundColor: "var(--accent-primary)"
  },
  stepName: {
    fontSize: "12px",
    fontFamily: "var(--font-sans)"
  },
  doneLabel: {
    fontSize: "9px",
    fontFamily: "var(--font-mono)",
    fontWeight: "700",
    color: "#16A34A"
  },
  currentLabel: {
    fontSize: "9px",
    fontFamily: "var(--font-mono)",
    fontWeight: "700",
    color: "#A04022"
  },
  pendingLabel: {
    fontSize: "9px",
    fontFamily: "var(--font-mono)",
    fontWeight: "600",
    color: "#A8A29E"
  },
  controlsBar: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    paddingTop: "10px",
    borderTop: "1px solid var(--border-light)"
  }
};
