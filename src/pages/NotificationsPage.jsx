import React from "react";
import { useNavigate } from "react-router-dom";
import { useApp } from "../context/AppContext";
import { AlertTriangle, ShieldAlert, Info, ArrowRight, CheckCircle2, XCircle } from "lucide-react";

export function NotificationsPage() {
  const navigate = useNavigate();
  const { notifications, currentUser, markNotificationAsRead } = useApp();

  // Filter notifications relevant to current user role and identity
  const userNotifications = notifications.filter((n) => {
    if (n.targetRole && n.targetRole !== currentUser?.role) return false;
    if (n.targetEmail && n.targetEmail !== currentUser?.email) return false;
    return true;
  });

  const handleCardClick = (notificationObj) => {
    markNotificationAsRead(notificationObj.id);
    if (notificationObj.link) {
      navigate(notificationObj.link);
    }
  };

  const getPriorityIcon = (priority, title = "") => {
    if (title.includes("ACCEPTED") || title.includes("APPROVED")) {
      return <CheckCircle2 size={18} color="#16A34A" />;
    }
    if (title.includes("REJECTED")) {
      return <XCircle size={18} color="#DC2626" />;
    }
    switch (priority?.toUpperCase()) {
      case "CRITICAL":
        return <ShieldAlert size={18} color="#DC2626" />;
      case "URGENT":
        return <AlertTriangle size={18} color="#D97706" />;
      default:
        return <Info size={18} color="#2563EB" />;
    }
  };

  const getPriorityBadge = (priority, title = "") => {
    if (title.includes("ACCEPTED") || title.includes("APPROVED")) {
      return { bg: "#F0FDF4", text: "#16A34A", border: "#BBF7D0" };
    }
    if (title.includes("REJECTED")) {
      return { bg: "#FEF2F2", text: "#DC2626", border: "#FCA5A5" };
    }
    switch (priority?.toUpperCase()) {
      case "CRITICAL":
        return { bg: "#FEF2F2", text: "#DC2626", border: "#FCA5A5" };
      case "URGENT":
        return { bg: "#FFFBEB", text: "#D97706", border: "#FDE68A" };
      default:
        return { bg: "#EFF6FF", text: "#2563EB", border: "#BFDBFE" };
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
      {/* Header */}
      <div>
        <h1 className="font-serif-heading" style={{ fontSize: "22px", margin: "0 0 4px 0" }}>
          SYSTEM NOTIFICATIONS & CONSERVATION ALERTS
        </h1>
        <p style={{ fontSize: "13px", color: "var(--text-secondary)" }}>
          Real-time structural anomaly alerts, pending reviews, and autonomous AI consensus updates.
        </p>
      </div>

      {/* Notifications List (Entire Card Container is Clickable) */}
      <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
        {userNotifications.length === 0 ? (
          <div className="ancestra-card" style={{ padding: "24px", textAlign: "center", color: "var(--text-muted)" }}>
            No active notifications recorded for your workspace account.
          </div>
        ) : (
          userNotifications.map((n) => {
            const badgeStyle = getPriorityBadge(n.priority, n.title);
            return (
              <div
                key={n.id}
                onClick={() => handleCardClick(n)}
                className="ancestra-card"
                style={{
                  ...styles.notifCard,
                  backgroundColor: n.read ? "#FFFFFF" : "#FAF8F5",
                  borderColor: n.read ? "var(--border-color)" : "rgba(160, 64, 34, 0.3)",
                  cursor: "pointer"
                }}
                title="Click notification card to inspect details"
              >
                <div style={styles.iconBox}>{getPriorityIcon(n.priority, n.title)}</div>

                <div style={{ flex: 1 }}>
                  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "4px" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                      <h3 style={styles.notifTitle}>{n.title}</h3>
                      <span
                        style={{
                          fontSize: "10px",
                          fontFamily: "var(--font-mono)",
                          fontWeight: 700,
                          padding: "1px 6px",
                          borderRadius: "3px",
                          backgroundColor: badgeStyle.bg,
                          color: badgeStyle.text,
                          border: `1px solid ${badgeStyle.border}`
                        }}
                      >
                        {n.priority}
                      </span>
                    </div>
                    <span style={{ fontSize: "11px", color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
                      {n.time}
                    </span>
                  </div>

                  <p style={styles.notifDesc}>{n.description}</p>
                </div>

                <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                  {!n.read && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        markNotificationAsRead(n.id);
                      }}
                      className="btn-secondary"
                      style={{ padding: "4px 8px", fontSize: "11px" }}
                    >
                      Mark Read
                    </button>
                  )}
                  {n.link && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleCardClick(n);
                      }}
                      className="btn-primary"
                      style={{ padding: "4px 10px", fontSize: "11px" }}
                    >
                      <span>Inspect</span>
                      <ArrowRight size={12} />
                    </button>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}

const styles = {
  notifCard: {
    display: "flex",
    alignItems: "flex-start",
    gap: "14px",
    padding: "14px",
    transition: "transform 0.12s ease, border-color 0.12s ease"
  },
  iconBox: {
    marginTop: "2px",
    flexShrink: 0
  },
  notifTitle: {
    fontSize: "13px",
    fontFamily: "var(--font-mono)",
    fontWeight: "700",
    color: "var(--text-primary)",
    margin: 0
  },
  notifDesc: {
    fontSize: "12px",
    color: "var(--text-secondary)",
    margin: 0
  }
};
