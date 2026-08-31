import React from "react";

export function StatusBadge({ status, size = "md" }) {
  const getStyles = () => {
    switch (status?.toUpperCase()) {
      case "HIGH":
      case "CRITICAL":
      case "HIGH_RISK":
        return {
          bg: "#FEF2F2",
          border: "#FCA5A5",
          text: "#DC2626"
        };
      case "MEDIUM":
      case "MONITOR":
      case "ATTENTION":
        return {
          bg: "#FFFBEB",
          border: "#FDE68A",
          text: "#D97706"
        };
      case "LOW":
      case "STABLE":
      case "CONFIRMED":
        return {
          bg: "#F0FDF4",
          border: "#BBF7D0",
          text: "#16A34A"
        };
      default:
        return {
          bg: "#F3F4F6",
          border: "#E5E7EB",
          text: "#4B5563"
        };
    }
  };

  const styleConfig = getStyles();

  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: "4px",
        padding: size === "sm" ? "1px 6px" : "3px 8px",
        fontSize: size === "sm" ? "10px" : "11px",
        fontFamily: "var(--font-mono)",
        fontWeight: "700",
        textTransform: "uppercase",
        letterSpacing: "0.04em",
        borderRadius: "4px",
        backgroundColor: styleConfig.bg,
        border: `1px solid ${styleConfig.border}`,
        color: styleConfig.text
      }}
    >
      <span
        style={{
          width: "5px",
          height: "5px",
          borderRadius: "50%",
          backgroundColor: styleConfig.text
        }}
      />
      {status}
    </span>
  );
}
