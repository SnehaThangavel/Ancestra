import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useApp } from "../../context/AppContext";
import { SiteRequestModal } from "../expert/SiteRequestModal";
import { Clock, Bell, Landmark, Settings } from "lucide-react";

export function TopHeader() {
  const navigate = useNavigate();
  const { currentUser, notifications } = useApp();
  const [currentTime, setCurrentTime] = useState("");
  const [isRequestModalOpen, setIsRequestModalOpen] = useState(false);

  const unreadCount = notifications.filter((n) => !n.read).length;
  const isExpert = currentUser?.role === "CONSERVATION_EXPERT";

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      const timeStr = now.toLocaleTimeString("en-US", { hour12: false }) + " GMT+5:30";
      setCurrentTime(timeStr);
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header style={styles.headerContainer}>
      <div style={styles.headerMain}>
        {/* Left Side Branding Label */}
        <div style={styles.headerLeftTitle}>
          <span style={styles.headerBrandLabel}>ANCESTRA PLATFORM</span>
        </div>

        {/* Header Right Tools: Clock, Bell, Settings Button, and Expert Request Button */}
        <div style={styles.headerRightGroup}>
          <div style={styles.clockBox}>
            <Clock size={13} color="#8E857B" />
            <span style={styles.clockText}>{currentTime || "12:04:02 GMT+5:30"}</span>
          </div>

          {/* Notification Quick Bell */}
          <button
            onClick={() => navigate("/notifications")}
            style={styles.bellBtn}
            title="Notifications"
          >
            <Bell size={15} color="#57534E" />
            {unreadCount > 0 && <span style={styles.bellBadge}>{unreadCount}</span>}
          </button>

          {/* Change 2: Settings Button (Matching Bell Button Size & Style, Navigates to /profile) */}
          <button
            onClick={() => navigate("/profile")}
            style={styles.settingsBtn}
            title="User Profile & Account Settings"
          >
            <Settings size={15} color="#57534E" />
          </button>

          {/* Heritage Site Request Option (Expert Side ONLY) */}
          {isExpert && (
            <button
              onClick={() => setIsRequestModalOpen(true)}
              className="btn-primary"
              style={{ padding: "6px 14px", height: "32px", fontSize: "11.5px" }}
            >
              <Landmark size={14} />
              <span>HERITAGE SITE REQUEST</span>
            </button>
          )}
        </div>
      </div>

      {/* Expert Site Request Modal */}
      <SiteRequestModal
        isOpen={isRequestModalOpen}
        onClose={() => setIsRequestModalOpen(false)}
      />
    </header>
  );
}

const styles = {
  headerContainer: {
    position: "sticky",
    top: 0,
    zIndex: 30,
    backgroundColor: "var(--bg-header)",
    borderBottom: "1px solid var(--border-color)"
  },
  headerMain: {
    height: "56px", // Change 3: Slightly expanded vertical height for breathing space
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    padding: "0 22px"
  },
  headerLeftTitle: {
    display: "flex",
    alignItems: "center"
  },
  headerBrandLabel: {
    fontSize: "11px",
    fontFamily: "var(--font-mono)",
    fontWeight: "700",
    letterSpacing: "0.08em",
    color: "#8E857B"
  },
  headerRightGroup: {
    display: "flex",
    alignItems: "center",
    gap: "10px"
  },
  clockBox: {
    display: "flex",
    alignItems: "center",
    gap: "6px",
    backgroundColor: "#FFFFFF",
    padding: "6px 12px",
    border: "1px solid var(--border-color)",
    borderRadius: "6px"
  },
  clockText: {
    fontFamily: "var(--font-mono)",
    fontSize: "11px",
    color: "#57534E"
  },
  bellBtn: {
    position: "relative",
    background: "#FFFFFF",
    border: "1px solid var(--border-color)",
    borderRadius: "6px",
    width: "32px",
    height: "32px",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    cursor: "pointer",
    transition: "background-color 0.12s ease"
  },
  bellBadge: {
    position: "absolute",
    top: "-3px",
    right: "-3px",
    backgroundColor: "var(--accent-primary)",
    color: "#FFFFFF",
    fontSize: "9px",
    fontWeight: "700",
    borderRadius: "8px",
    padding: "1px 4px"
  },
  settingsBtn: {
    background: "#FFFFFF",
    border: "1px solid var(--border-color)",
    borderRadius: "6px",
    width: "32px",
    height: "32px",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    cursor: "pointer",
    transition: "background-color 0.12s ease"
  }
};
