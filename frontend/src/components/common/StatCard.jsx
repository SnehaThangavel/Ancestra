import React from "react";

export function StatCard({
  label,
  value,
  subtitle,
  icon: Icon,
  iconBg = "#F7EDE9",
  iconColor = "#A04022",
  onClick
}) {
  return (
    <div
      onClick={onClick}
      className="ancestra-card"
      style={{
        ...styles.card,
        cursor: onClick ? "pointer" : "default"
      }}
    >
      <div style={styles.topRow}>
        <span style={styles.label}>{label}</span>
        {Icon && (
          <div style={{ ...styles.iconBox, backgroundColor: iconBg }}>
            <Icon size={16} color={iconColor} />
          </div>
        )}
      </div>
      <div style={styles.valueRow}>
        {typeof value === "string" || typeof value === "number" ? (
          <span style={styles.value}>{value}</span>
        ) : (
          value
        )}
      </div>
      {subtitle ? <div style={styles.subtitle}>{subtitle}</div> : null}
    </div>
  );
}

const styles = {
  card: {
    display: "flex",
    flexDirection: "column",
    justifyContent: "space-between",
    minHeight: "110px",
    padding: "16px 18px",
    transition: "transform 0.12s ease, border-color 0.12s ease"
  },
  topRow: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between"
  },
  label: {
    fontSize: "11px",
    fontFamily: "var(--font-sans)",
    fontWeight: "700",
    letterSpacing: "0.08em",
    color: "#8E857B",
    textTransform: "uppercase"
  },
  iconBox: {
    width: "28px",
    height: "28px",
    borderRadius: "4px",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    flexShrink: 0
  },
  valueRow: {
    marginTop: "8px",
    marginBottom: "2px"
  },
  value: {
    fontFamily: "var(--font-serif)",
    fontSize: "30px",
    fontWeight: "700",
    color: "var(--text-primary)",
    lineHeight: "1"
  },
  subtitle: {
    fontSize: "11px",
    color: "var(--text-muted)",
    marginTop: "4px"
  }
};
