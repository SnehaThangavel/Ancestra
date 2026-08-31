import React from "react";

export function StatCard({ label, value, subtitle, icon: Icon, iconBg = "#F7EDE9", iconColor = "#A04022" }) {
  return (
    <div className="ancestra-card" style={styles.card}>
      <div style={styles.topRow}>
        <span style={styles.label}>{label}</span>
        {Icon && (
          <div style={{ ...styles.iconBox, backgroundColor: iconBg }}>
            <Icon size={16} color={iconColor} />
          </div>
        )}
      </div>
      <div style={styles.valueRow}>
        <span style={styles.value}>{value}</span>
      </div>
      {subtitle && <div style={styles.subtitle}>{subtitle}</div>}
    </div>
  );
}

const styles = {
  card: {
    display: "flex",
    flexDirection: "column",
    justifyContent: "space-between",
    minHeight: "105px"
  },
  topRow: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between"
  },
  label: {
    fontSize: "10.5px",
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
    marginTop: "6px",
    marginBottom: "4px"
  },
  value: {
    fontFamily: "var(--font-serif)",
    fontSize: "26px",
    fontWeight: "700",
    color: "var(--text-primary)",
    lineHeight: "1"
  },
  subtitle: {
    fontSize: "11px",
    color: "var(--text-muted)"
  }
};
