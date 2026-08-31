import React from "react";

export function EmergencyBadge({ level }) {
  const getBadgeStyle = (lvl) => {
    switch (lvl?.toUpperCase()) {
      case "CRITICAL":
        return { bg: "#FEF2F2", border: "#FCA5A5", text: "#DC2626" };
      case "URGENT":
        return { bg: "#FFF1F2", border: "#FECDD3", text: "#E11D48" };
      case "ATTENTION":
        return { bg: "#FFFBEB", border: "#FDE68A", text: "#D97706" };
      case "MONITOR":
        return { bg: "#EFF6FF", border: "#BFDBFE", text: "#2563EB" };
      default:
        return { bg: "#F0FDF4", border: "#BBF7D0", text: "#16A34A" };
    }
  };

  const style = getBadgeStyle(level);

  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        padding: "2px 8px",
        fontSize: "11px",
        fontFamily: "var(--font-mono)",
        fontWeight: "700",
        textTransform: "uppercase",
        letterSpacing: "0.06em",
        borderRadius: "4px",
        backgroundColor: style.bg,
        border: `1px solid ${style.border}`,
        color: style.text
      }}
    >
      {level || "NORMAL"}
    </span>
  );
}
