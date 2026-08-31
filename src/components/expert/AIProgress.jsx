import React from "react";
import { CheckCircle2, Loader2, Circle } from "lucide-react";

export function AIProgress({ activeStep = 1, totalSteps = 9 }) {
  const steps = [
    { num: "01", label: "IMAGE RECEIVED", desc: "Photometric calibration & metadata verify" },
    { num: "02", label: "IMAGE QUALITY CHECK", desc: "Resolution & sensor noise validation" },
    { num: "03", label: "IMAGE PREPROCESSING", desc: "Color-checker normalization & edge filter" },
    { num: "04", label: "STRUCTURAL FEATURE EXTRACTION", desc: "Spatial coordinate anchoring & 3D mesh query" },
    { num: "05", label: "DAMAGE DETECTION", desc: "Lithic damage segmentation (cracks, spalling, efflorescence)" },
    { num: "06", label: "SEVERITY ESTIMATION", desc: "Fracture depth & surface area stress index" },
    { num: "07", label: "DAMAGE TREND ANALYSIS", desc: "Cross-temporal consensus weight calculation" },
    { num: "08", label: "EMERGENCY LEVEL COMPUTATION", desc: "ICOMOS heritage risk matrix evaluation" },
    { num: "09", label: "ANALYSIS COMPLETE", desc: "Structural assessment record generated" }
  ];

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <span className="label-uppercase">AI PERCEPTION PIPELINE</span>
        <span style={styles.stepCounter}>STEP {activeStep} OF {totalSteps}</span>
      </div>

      <div style={styles.stepList}>
        {steps.map((step, idx) => {
          const stepNum = idx + 1;
          const isDone = stepNum < activeStep;
          const isCurrent = stepNum === activeStep;

          return (
            <div
              key={idx}
              style={{
                ...styles.stepRow,
                ...(isCurrent ? styles.stepRowCurrent : {}),
                ...(isDone ? styles.stepRowDone : {})
              }}
            >
              <div style={styles.iconBox}>
                {isDone ? (
                  <CheckCircle2 size={16} color="#16A34A" />
                ) : isCurrent ? (
                  <Loader2 size={16} color="#A04022" style={styles.spinner} />
                ) : (
                  <Circle size={16} color="#D6D3D1" />
                )}
              </div>

              <div style={{ flex: 1 }}>
                <div style={styles.stepLabelRow}>
                  <span style={styles.stepNum}>{step.num}.</span>
                  <span
                    style={{
                      ...styles.stepLabel,
                      color: isDone ? "#16A34A" : isCurrent ? "#A04022" : "#8E857B",
                      fontWeight: isCurrent ? 700 : 600
                    }}
                  >
                    {step.label}
                  </span>
                </div>
                <div style={styles.stepDesc}>{step.desc}</div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

const styles = {
  container: {
    display: "flex",
    flexDirection: "column",
    gap: "12px"
  },
  header: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    paddingBottom: "8px",
    borderBottom: "1px solid var(--border-light)"
  },
  stepCounter: {
    fontFamily: "var(--font-mono)",
    fontSize: "11px",
    fontWeight: "700",
    color: "var(--accent-primary)"
  },
  stepList: {
    display: "flex",
    flexDirection: "column",
    gap: "8px"
  },
  stepRow: {
    display: "flex",
    alignItems: "flex-start",
    gap: "10px",
    padding: "8px 10px",
    borderRadius: "4px",
    border: "1px solid transparent",
    transition: "all 0.15s ease"
  },
  stepRowDone: {
    backgroundColor: "#F0FDF4",
    borderColor: "#DCFCE7"
  },
  stepRowCurrent: {
    backgroundColor: "var(--accent-primary-light)",
    borderColor: "rgba(160, 64, 34, 0.3)"
  },
  iconBox: {
    marginTop: "2px",
    flexShrink: 0
  },
  stepLabelRow: {
    display: "flex",
    alignItems: "center",
    gap: "6px"
  },
  stepNum: {
    fontFamily: "var(--font-mono)",
    fontSize: "11px",
    fontWeight: "700",
    color: "#78716C"
  },
  stepLabel: {
    fontSize: "11px",
    fontFamily: "var(--font-sans)",
    letterSpacing: "0.04em"
  },
  stepDesc: {
    fontSize: "10.5px",
    color: "var(--text-muted)",
    marginTop: "1px"
  },
  spinner: {
    animation: "spin 1s linear infinite"
  }
};
