import React, { useState } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { useApp } from "../../context/AppContext";
import { EngineStatusModal } from "../admin/EngineStatusModal";
import { Modal } from "../common/Modal";
import {
  LayoutDashboard,
  Landmark,
  Layers,
  Camera,
  Cpu,
  CheckCircle2,
  TrendingUp,
  FileText,
  Bell,
  UserCheck,
  Building2,
  LogOut,
  Edit3
} from "lucide-react";

export function Sidebar() {
  const navigate = useNavigate();
  const { currentUser, logout, notifications, aiEngineStatus } = useApp();
  const unreadCount = notifications.filter((n) => !n.read).length;

  const [isLogoutModalOpen, setIsLogoutModalOpen] = useState(false);
  const [isEngineModalOpen, setIsEngineModalOpen] = useState(false);

  const isExpert = currentUser?.role === "CONSERVATION_EXPERT";
  const isAdmin = currentUser?.role === "ADMINISTRATOR";

  const handleConfirmLogout = () => {
    setIsLogoutModalOpen(false);
    logout();
    navigate("/login");
  };

  const expertNavItems = [
    { label: "Overview", num: "01", icon: LayoutDashboard, path: "/dashboard" },
    { label: "Image Analysis", num: "03", icon: Camera, path: "/expert/image-analysis" },
    { label: "AI Perception", num: "04", icon: Cpu, path: "/expert/ai-analysis" },
    { label: "AI Results", num: "05", icon: CheckCircle2, path: "/expert/results" },
    { label: "Damage History", num: "06", icon: TrendingUp, path: "/expert/damage-history" },
    { label: "Reports", num: "07", icon: FileText, path: "/reports" },
    { label: "Notifications", num: "08", icon: Bell, path: "/notifications", badge: unreadCount > 0 ? unreadCount : null }
  ];

  const adminNavItems = [
    { label: "Overview", num: "01", icon: LayoutDashboard, path: "/dashboard" },
    { label: "Heritage Sites", num: "02", icon: Landmark, path: "/admin/heritage-sites" },
    { label: "Architectural Regions", num: "03", icon: Layers, path: "/admin/architectural-regions" },
    { label: "Reports", num: "04", icon: FileText, path: "/reports" },
    { label: "Notifications", num: "05", icon: Bell, path: "/notifications", badge: unreadCount > 0 ? unreadCount : null }
  ];

  const navItems = isExpert ? expertNavItems : adminNavItems;

  return (
    <aside style={styles.sidebar}>
      {/* Top Branding */}
      <div style={styles.brandContainer}>
        <div style={styles.logoRow}>
          <div style={styles.logoIconBox}>
            <Building2 size={16} color="#FFFFFF" />
          </div>
          <div>
            <div style={styles.logoTitleRow}>
              <span style={styles.brandName}>ANCESTRA</span>
              <span className="version-pill">v0.1</span>
            </div>
            <div style={styles.brandSubtitle}>STRUCTURAL INTELLIGENCE</div>
          </div>
        </div>
      </div>

      {/* Module Navigation */}
      <div style={styles.navSection}>
        <div style={styles.sectionHeader}>CONSERVATION MODULES</div>
        <nav style={styles.navList}>
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                style={({ isActive }) => ({
                  ...styles.navItem,
                  ...(isActive ? styles.navItemActive : {})
                })}
              >
                {({ isActive }) => (
                  <>
                    {isActive && <div style={styles.activeIndicator} />}
                    <Icon size={15} color={isActive ? "#A04022" : "#78716C"} style={{ flexShrink: 0 }} />
                    <span style={{ ...styles.navLabel, color: isActive ? "#1C1917" : "#57534E", fontWeight: isActive ? 600 : 500 }}>
                      {item.label}
                    </span>
                    {item.badge ? (
                      <span style={styles.navBadge}>{item.badge}</span>
                    ) : (
                      <span style={styles.navNum}>{item.num}</span>
                    )}
                  </>
                )}
              </NavLink>
            );
          })}
        </nav>
      </div>

      {/* System Status Card with Administrator-Only Edit Icon */}
      <div style={styles.statusCard}>
        <div style={styles.statusHeader}>
          <span>AI ASSESSMENT ENGINE</span>
          {isAdmin && (
            <button
              onClick={() => setIsEngineModalOpen(true)}
              style={styles.editEngineBtn}
              title="Edit AI Engine Status (Admin Only)"
            >
              <Edit3 size={11} color="#A04022" />
              <span>EDIT</span>
            </button>
          )}
        </div>
        <div style={styles.onlineRow}>
          <span
            style={{
              ...styles.onlineDot,
              backgroundColor: aiEngineStatus.online ? "var(--status-green)" : "#DC2626"
            }}
          />
          <span
            style={{
              ...styles.onlineText,
              color: aiEngineStatus.online ? "var(--status-green)" : "#DC2626"
            }}
          >
            {aiEngineStatus.online ? "ONLINE" : "OFFLINE"}
          </span>
        </div>
        <div style={styles.modelStateRow}>
          <span style={styles.modelLabel}>MODEL STATE:</span>
          <span style={styles.modelValue}>{aiEngineStatus.modelState}</span>
        </div>
      </div>

      {/* User Profile Footer with Log Out Button for BOTH Users */}
      <div style={styles.profileSection}>
        <div style={styles.profileInfo}>
          <div style={styles.avatarCircle}>
            <UserCheck size={14} color="#A04022" />
          </div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={styles.userName}>{currentUser?.name || "Dr. A. Sharma"}</div>
            <div style={styles.userTitle}>{currentUser?.title || "Lead Conservator (ASI)"}</div>
          </div>
        </div>

        <div style={styles.roleStaticRow}>
          <span style={styles.roleStaticValue}>
            {isExpert ? "CONSERVATION EXPERT" : "ADMINISTRATOR"}
          </span>
          <button
            onClick={() => setIsLogoutModalOpen(true)}
            className="btn-secondary"
            style={styles.logoutBtn}
            title="Log out of session"
          >
            <LogOut size={12} color="#DC2626" />
            <span style={{ color: "#DC2626" }}>LOG OUT</span>
          </button>
        </div>
      </div>

      {/* Logout Confirmation Modal */}
      <Modal
        isOpen={isLogoutModalOpen}
        onClose={() => setIsLogoutModalOpen(false)}
        title="LOG OUT OF ANCESTRA"
        width="400px"
      >
        <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          <p style={{ fontSize: "13px", color: "var(--text-primary)" }}>
            ARE YOU SURE YOU WANT TO LOG OUT?
          </p>
          <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px" }}>
            <button onClick={() => setIsLogoutModalOpen(false)} className="btn-secondary">
              Cancel
            </button>
            <button onClick={handleConfirmLogout} className="btn-primary" style={{ backgroundColor: "#DC2626", borderColor: "#DC2626" }}>
              Log Out
            </button>
          </div>
        </div>
      </Modal>

      {/* Engine Status Modal for Admin */}
      {isAdmin && (
        <EngineStatusModal
          isOpen={isEngineModalOpen}
          onClose={() => setIsEngineModalOpen(false)}
        />
      )}
    </aside>
  );
}

const styles = {
  sidebar: {
    width: "var(--sidebar-width)",
    minWidth: "var(--sidebar-width)",
    height: "100vh",
    backgroundColor: "var(--bg-sidebar)",
    borderRight: "1px solid var(--border-sidebar)",
    display: "flex",
    flexDirection: "column",
    position: "fixed",
    top: 0,
    left: 0,
    zIndex: 40,
    userSelect: "none"
  },
  brandContainer: {
    padding: "16px 16px 14px 16px",
    borderBottom: "1px solid var(--border-light)"
  },
  logoRow: {
    display: "flex",
    alignItems: "center",
    gap: "10px"
  },
  logoIconBox: {
    width: "28px",
    height: "28px",
    backgroundColor: "var(--accent-primary)",
    borderRadius: "4px",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    flexShrink: 0
  },
  logoTitleRow: {
    display: "flex",
    alignItems: "center",
    gap: "6px"
  },
  brandName: {
    fontFamily: "var(--font-serif)",
    fontWeight: "700",
    fontSize: "15px",
    letterSpacing: "0.06em",
    color: "var(--text-primary)"
  },
  brandSubtitle: {
    fontSize: "9px",
    fontFamily: "var(--font-sans)",
    fontWeight: "600",
    letterSpacing: "0.08em",
    color: "var(--text-muted)",
    marginTop: "-1px"
  },
  navSection: {
    padding: "16px 10px 12px 10px",
    flex: 1,
    overflowY: "auto"
  },
  sectionHeader: {
    fontSize: "10px",
    fontFamily: "var(--font-sans)",
    fontWeight: "700",
    letterSpacing: "0.09em",
    color: "#8E857B",
    padding: "0 8px 10px 8px"
  },
  navList: {
    display: "flex",
    flexDirection: "column",
    gap: "2px"
  },
  navItem: {
    position: "relative",
    display: "flex",
    alignItems: "center",
    gap: "9px",
    padding: "8px 10px",
    borderRadius: "4px",
    textDecoration: "none",
    fontSize: "12.5px",
    transition: "background-color 0.12s ease"
  },
  navItemActive: {
    backgroundColor: "#EAE4DA"
  },
  activeIndicator: {
    position: "absolute",
    left: 0,
    top: "4px",
    bottom: "4px",
    width: "3px",
    backgroundColor: "var(--accent-primary)",
    borderRadius: "0 2px 2px 0"
  },
  navLabel: {
    flex: 1,
    whiteSpace: "nowrap",
    overflow: "hidden",
    textOverflow: "ellipsis"
  },
  navNum: {
    fontFamily: "var(--font-mono)",
    fontSize: "10px",
    color: "#A0988E"
  },
  navBadge: {
    backgroundColor: "var(--accent-primary)",
    color: "#FFFFFF",
    fontSize: "10px",
    fontWeight: "700",
    borderRadius: "8px",
    padding: "1px 6px"
  },
  statusCard: {
    margin: "12px 12px 10px 12px",
    padding: "10px 12px",
    backgroundColor: "#FAF7F2",
    border: "1px solid var(--border-color)",
    borderRadius: "6px"
  },
  statusHeader: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    fontSize: "10px",
    fontFamily: "var(--font-sans)",
    fontWeight: "700",
    letterSpacing: "0.07em",
    color: "var(--text-muted)",
    marginBottom: "4px"
  },
  editEngineBtn: {
    background: "none",
    border: "none",
    color: "var(--accent-primary)",
    fontSize: "9px",
    fontFamily: "var(--font-mono)",
    fontWeight: "700",
    cursor: "pointer",
    display: "flex",
    alignItems: "center",
    gap: "3px",
    padding: 0
  },
  onlineRow: {
    display: "flex",
    alignItems: "center",
    gap: "6px",
    marginBottom: "4px"
  },
  onlineDot: {
    width: "7px",
    height: "7px",
    borderRadius: "50%"
  },
  onlineText: {
    fontSize: "11px",
    fontFamily: "var(--font-mono)",
    fontWeight: "700"
  },
  modelStateRow: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    fontSize: "10px"
  },
  modelLabel: {
    color: "var(--text-muted)"
  },
  modelValue: {
    fontFamily: "var(--font-mono)",
    fontWeight: "600",
    color: "var(--text-primary)"
  },
  profileSection: {
    padding: "12px",
    borderTop: "1px solid var(--border-light)",
    backgroundColor: "#F4F0EA"
  },
  profileInfo: {
    display: "flex",
    alignItems: "center",
    gap: "8px"
  },
  avatarCircle: {
    width: "26px",
    height: "26px",
    borderRadius: "50%",
    backgroundColor: "var(--accent-primary-light)",
    border: "1px solid rgba(160, 64, 34, 0.3)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    flexShrink: 0
  },
  userName: {
    fontSize: "12px",
    fontWeight: "600",
    color: "var(--text-primary)",
    lineHeight: "1.2"
  },
  userTitle: {
    fontSize: "10px",
    color: "var(--text-muted)",
    whiteSpace: "nowrap",
    overflow: "hidden",
    textOverflow: "ellipsis"
  },
  roleStaticRow: {
    marginTop: "8px",
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    paddingTop: "6px",
    borderTop: "1px dashed var(--border-sidebar)"
  },
  roleStaticValue: {
    fontSize: "9px",
    fontFamily: "var(--font-mono)",
    fontWeight: "700",
    color: "var(--accent-primary)"
  },
  logoutBtn: {
    padding: "2px 6px",
    fontSize: "10px",
    fontFamily: "var(--font-mono)",
    display: "flex",
    alignItems: "center",
    gap: "4px"
  }
};
