import React from "react";

export function SectionCard({ title, badgeText, subtitle, children, action }) {
  return (
    <div className="ancestra-card" style={{ marginBottom: "20px" }}>
      {(title || action) && (
        <div style={styles.headerRow}>
          <div>
            <div style={styles.titleGroup}>
              {badgeText && <span className="module-badge">{badgeText}</span>}
              {title && <h2 className="font-serif-heading" style={styles.title}>{title}</h2>}
            </div>
            {subtitle && <p style={styles.subtitle}>{subtitle}</p>}
          </div>
          {action && <div>{action}</div>}
        </div>
      )}
      <div>{children}</div>
    </div>
  );
}

const styles = {
  headerRow: {
    display: "flex",
    alignItems: "flex-start",
    justifyContent: "space-between",
    marginBottom: "16px",
    paddingBottom: "12px",
    borderBottom: "1px solid var(--border-light)"
  },
  titleGroup: {
    display: "flex",
    alignItems: "center",
    gap: "10px"
  },
  title: {
    fontSize: "17px",
    margin: 0
  },
  subtitle: {
    fontSize: "12px",
    color: "var(--text-muted)",
    marginTop: "4px"
  }
};
