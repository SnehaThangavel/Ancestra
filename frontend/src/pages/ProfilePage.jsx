import React, { useState, useEffect } from "react";
import { useApp } from "../context/AppContext";
import { UserCheck, Save, KeyRound, Eye, EyeOff, ShieldCheck } from "lucide-react";

export function ProfilePage() {
  const { currentUser, updateUserProfile, resetUserPassword, showToast } = useApp();

  const [name, setName] = useState(currentUser?.name || "");
  const [email, setEmail] = useState(currentUser?.email || "");
  const [title, setTitle] = useState(currentUser?.title || "");

  // Password reset fields
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);

  useEffect(() => {
    if (currentUser) {
      setName(currentUser.name || "");
      setEmail(currentUser.email || "");
      setTitle(currentUser.title || "");
    }
  }, [currentUser]);

  const handleSaveProfile = (e) => {
    e.preventDefault();
    if (!name || !email) {
      showToast("Name and email are required.", "error");
      return;
    }
    updateUserProfile({ name, email, title });
  };

  const handleResetPasswordSubmit = (e) => {
    e.preventDefault();
    if (!currentPassword) {
      showToast("Please enter your current password.", "error");
      return;
    }
    if (!newPassword || newPassword.length < 6) {
      showToast("New password must be at least 6 characters.", "error");
      return;
    }
    if (newPassword !== confirmPassword) {
      showToast("New password and confirm password do not match.", "error");
      return;
    }

    const res = resetUserPassword(currentPassword, newPassword);
    if (res.success) {
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
    }
  };

  const isExpert = currentUser?.role === "CONSERVATION_EXPERT";

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "24px", maxWidth: "800px" }}>
      {/* Page Header */}
      <div>
        <h1 className="font-serif-heading" style={{ fontSize: "22px", margin: "0 0 4px 0" }}>
          USER PROFILE & ACCOUNT SETTINGS
        </h1>
        <p style={{ fontSize: "13px", color: "var(--text-secondary)" }}>
          Manage your personal conservator credentials, official title, contact details, and account security.
        </p>
      </div>

      {/* Profile Overview Card */}
      <div className="ancestra-card" style={styles.headerCard}>
        <div style={styles.avatarLarge}>
          <UserCheck size={28} color="#A04022" />
        </div>
        <div>
          <h2 className="font-serif-heading" style={{ fontSize: "18px", margin: "0 0 2px 0" }}>
            {currentUser?.name}
          </h2>
          <div style={{ fontSize: "12px", color: "var(--text-secondary)", marginBottom: "6px" }}>
            {currentUser?.title}
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <span style={styles.roleReadonlyBadge}>
              <ShieldCheck size={12} color="#A04022" />
              <span>ROLE: {isExpert ? "CONSERVATION EXPERT" : "ADMINISTRATOR"}</span>
            </span>
          </div>
        </div>
      </div>

      {/* Edit Profile Information Form */}
      <div className="ancestra-card">
        <h3 className="font-serif-heading" style={{ fontSize: "15px", marginBottom: "14px", paddingBottom: "10px", borderBottom: "1px solid var(--border-light)" }}>
          PERSONAL & OFFICIAL INFORMATION
        </h3>

        <form onSubmit={handleSaveProfile} style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
          <div className="form-group">
            <label className="form-label">FULL NAME *</label>
            <input
              type="text"
              className="form-input"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
            />
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
            <div className="form-group">
              <label className="form-label">EMAIL ADDRESS / PHONE *</label>
              <input
                type="text"
                className="form-input"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">OFFICIAL DESIGNATION / TITLE</label>
              <input
                type="text"
                className="form-input"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
              />
            </div>
          </div>

          {/* Read-Only Role Field */}
          <div className="form-group">
            <label className="form-label">ACCOUNT ROLE (READ-ONLY)</label>
            <input
              type="text"
              className="form-input"
              style={{ backgroundColor: "#F0EBE1", color: "#78716C", fontFamily: "var(--font-mono)", fontWeight: 700, cursor: "not-allowed" }}
              value={isExpert ? "CONSERVATION EXPERT" : "ADMINISTRATOR"}
              readOnly
              disabled
            />
            <span style={{ fontSize: "9.5px", color: "var(--text-muted)", marginTop: "2px" }}>
              Account role permissions are controlled by system administration and cannot be edited.
            </span>
          </div>

          <div style={{ display: "flex", justifyContent: "flex-end", marginTop: "8px" }}>
            <button type="submit" className="btn-primary" style={{ padding: "8px 18px" }}>
              <Save size={14} />
              <span>SAVE CHANGES</span>
            </button>
          </div>
        </form>
      </div>

      {/* Reset Password Form */}
      <div className="ancestra-card">
        <div style={{ display: "flex", alignItems: "center", gap: "8px", paddingBottom: "10px", borderBottom: "1px solid var(--border-light)", marginBottom: "14px" }}>
          <KeyRound size={16} color="#A04022" />
          <h3 className="font-serif-heading" style={{ fontSize: "15px", margin: 0 }}>
            RESET PASSWORD & SECURITY
          </h3>
        </div>

        <form onSubmit={handleResetPasswordSubmit} style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
          <div className="form-group">
            <label className="form-label">CURRENT PASSWORD *</label>
            <div style={styles.inputWrapper}>
              <input
                type={showPassword ? "text" : "password"}
                className="form-input"
                style={{ paddingRight: "34px" }}
                placeholder="Enter current password"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                required
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                style={styles.eyeBtn}
              >
                {showPassword ? <EyeOff size={14} color="#8E857B" /> : <Eye size={14} color="#8E857B" />}
              </button>
            </div>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
            <div className="form-group">
              <label className="form-label">NEW PASSWORD *</label>
              <input
                type={showPassword ? "text" : "password"}
                className="form-input"
                placeholder="Minimum 6 characters"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">CONFIRM NEW PASSWORD *</label>
              <input
                type={showPassword ? "text" : "password"}
                className="form-input"
                placeholder="Re-enter new password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
              />
            </div>
          </div>

          <div style={{ display: "flex", justifyContent: "flex-end", marginTop: "8px" }}>
            <button type="submit" className="btn-secondary" style={{ padding: "8px 18px", borderColor: "rgba(160, 64, 34, 0.4)" }}>
              <KeyRound size={14} color="#A04022" />
              <span>RESET PASSWORD</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

const styles = {
  headerCard: {
    display: "flex",
    alignItems: "center",
    gap: "16px",
    padding: "18px 20px"
  },
  avatarLarge: {
    width: "54px",
    height: "54px",
    borderRadius: "50%",
    backgroundColor: "#F7EDE9",
    border: "1.5px solid rgba(160, 64, 34, 0.3)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    flexShrink: 0
  },
  roleReadonlyBadge: {
    display: "inline-flex",
    alignItems: "center",
    gap: "6px",
    padding: "3px 8px",
    backgroundColor: "#F7EDE9",
    border: "1px solid rgba(160, 64, 34, 0.25)",
    borderRadius: "4px",
    fontSize: "10px",
    fontFamily: "var(--font-mono)",
    fontWeight: "700",
    color: "#A04022"
  },
  inputWrapper: {
    position: "relative",
    display: "flex",
    alignItems: "center"
  },
  eyeBtn: {
    position: "absolute",
    right: "10px",
    top: "50%",
    transform: "translateY(-50%)",
    background: "none",
    border: "none",
    cursor: "pointer",
    padding: 0,
    display: "flex",
    alignItems: "center"
  }
};
