import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useApp } from "../context/AppContext";
import { RegisterModal } from "../components/auth/RegisterModal";
import { Building2, Lock, Mail, ArrowRight, Eye, EyeOff, CheckCircle } from "lucide-react";

export function LoginPage() {
  const navigate = useNavigate();
  const { login, loginWithGoogle, isAuthenticated, isAuthLoading } = useApp();

  const [emailOrPhone, setEmailOrPhone] = useState("a.sharma@asi.gov.in");
  const [password, setPassword] = useState("password123");
  const [showPassword, setShowPassword] = useState(false);
  const [selectedRolePreset, setSelectedRolePreset] = useState("EXPERT"); // "EXPERT" or "ADMIN"

  const [isRegisterOpen, setIsRegisterOpen] = useState(false);
  const [successMsg, setSuccessMsg] = useState("");
  const [errorMsg, setErrorMsg] = useState("");

  // If already logged in, redirect directly to dashboard
  useEffect(() => {
    if (!isAuthLoading && isAuthenticated) {
      navigate("/dashboard", { replace: true });
    }
  }, [isAuthenticated, isAuthLoading, navigate]);

  const handleSubmit = (e) => {
    e.preventDefault();
    setErrorMsg("");
    setSuccessMsg("");

    const res = login(emailOrPhone, password);
    if (res.success) {
      navigate("/dashboard");
    } else {
      setErrorMsg(res.message);
    }
  };

  const handleRegisterSuccess = (registeredIdentifier) => {
    setEmailOrPhone(registeredIdentifier);
    setPassword("");
    setSuccessMsg("Account created successfully. Please sign in with your credentials.");
  };

  const handleRoleSelect = (roleType) => {
    setSelectedRolePreset(roleType);
    if (roleType === "EXPERT") {
      setEmailOrPhone("a.sharma@asi.gov.in");
      setPassword("password123");
    } else {
      setEmailOrPhone("s.ranganathan@ancestra.org");
      setPassword("password123");
    }
    setErrorMsg("");
  };

  return (
    <div style={styles.pageContainer} className="paper-grid">
      <div style={styles.loginCard} className="ancestra-card">
        {/* Header Logo */}
        <div style={styles.brandBox}>
          <div style={styles.logoIcon}>
            <Building2 size={22} color="#FFFFFF" />
          </div>
          <div>
            <div style={styles.brandTitleRow}>
              <span className="font-serif-heading" style={{ fontSize: "21px", letterSpacing: "0.06em" }}>
                ANCESTRA
              </span>
            </div>
            <div style={styles.brandSub}>STRUCTURAL INTELLIGENCE</div>
          </div>
        </div>

        <div style={styles.divider} />

        <div style={{ marginBottom: "16px" }}>
          <h2 className="font-serif-heading" style={{ fontSize: "16px", margin: 0 }}>
            WELCOME BACK
          </h2>
          <p style={{ fontSize: "12px", color: "var(--text-muted)", marginTop: "2px" }}>
            Sign in to access your heritage structural conservation workspace.
          </p>
        </div>

        {/* Success / Error Banners */}
        {successMsg && (
          <div style={styles.successBanner}>
            <CheckCircle size={14} color="#16A34A" />
            <span>{successMsg}</span>
          </div>
        )}

        {errorMsg && (
          <div style={styles.errorBanner}>
            <span>{errorMsg}</span>
          </div>
        )}

        {/* Google OAuth Login Button */}
        <div style={styles.googleSection}>
          <button
            type="button"
            onClick={loginWithGoogle}
            style={styles.googleBtn}
            id="google-signin-button"
            title="Sign in securely with your Google Workspace or Personal Account"
          >
            <svg style={styles.googleIcon} viewBox="0 0 24 24" width="18" height="18">
              <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
              <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
              <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z" />
              <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z" />
            </svg>
            <span>CONTINUE WITH GOOGLE</span>
          </button>
        </div>

        {/* Divider */}
        <div style={styles.orDivider}>
          <div style={styles.orLine} />
          <span style={styles.orText}>OR SIGN IN WITH CREDENTIALS</span>
          <div style={styles.orLine} />
        </div>

        {/* Login Form */}
        <form onSubmit={handleSubmit} style={styles.form}>
          <div className="form-group">
            <label className="form-label">EMAIL OR PHONE NUMBER</label>
            <div style={styles.inputWrapper}>
              <Mail size={15} color="#8E857B" style={styles.inputIcon} />
              <input
                type="text"
                className="form-input"
                style={{ paddingLeft: "34px" }}
                placeholder="Enter email or phone number"
                value={emailOrPhone}
                onChange={(e) => setEmailOrPhone(e.target.value)}
                required
              />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">PASSWORD</label>
            <div style={styles.inputWrapper}>
              <Lock size={15} color="#8E857B" style={styles.inputIcon} />
              <input
                type={showPassword ? "text" : "password"}
                className="form-input"
                style={{ paddingLeft: "34px", paddingRight: "34px" }}
                placeholder="Enter password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                style={styles.eyeBtn}
                title={showPassword ? "Hide Password" : "Show Password"}
              >
                {showPassword ? <EyeOff size={14} color="#8E857B" /> : <Eye size={14} color="#8E857B" />}
              </button>
            </div>
          </div>

          <div style={styles.optionsRow}>
            <a href="#forgot" onClick={(e) => e.preventDefault()} style={styles.forgotLink}>
              FORGOT PASSWORD?
            </a>
          </div>

          <button type="submit" className="btn-primary" style={{ width: "100%", padding: "10px", marginTop: "4px" }}>
            <span>SIGN IN</span>
            <ArrowRight size={14} />
          </button>
        </form>

        {/* Change 3: YOUR ROLE (Visually Highlighted Active Preset) */}
        <div style={styles.roleSelectionRow}>
          <span style={styles.yourRoleLabel}>YOUR ROLE:</span>
          <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
            <button
              type="button"
              onClick={() => handleRoleSelect("EXPERT")}
              style={{
                ...styles.roleTabBtn,
                color: selectedRolePreset === "EXPERT" ? "var(--accent-primary)" : "#8E857B",
                fontWeight: selectedRolePreset === "EXPERT" ? "700" : "500",
                borderBottom: selectedRolePreset === "EXPERT" ? "2px solid var(--accent-primary)" : "2px solid transparent",
                backgroundColor: selectedRolePreset === "EXPERT" ? "#F7EDE9" : "transparent"
              }}
            >
              EXPERT
            </button>
            <span style={{ color: "var(--border-color)", fontSize: "11px" }}>|</span>
            <button
              type="button"
              onClick={() => handleRoleSelect("ADMIN")}
              style={{
                ...styles.roleTabBtn,
                color: selectedRolePreset === "ADMIN" ? "var(--accent-primary)" : "#8E857B",
                fontWeight: selectedRolePreset === "ADMIN" ? "700" : "500",
                borderBottom: selectedRolePreset === "ADMIN" ? "2px solid var(--accent-primary)" : "2px solid transparent",
                backgroundColor: selectedRolePreset === "ADMIN" ? "#F7EDE9" : "transparent"
              }}
            >
              ADMIN
            </button>
          </div>
        </div>

        {/* Registration Footer */}
        <div style={styles.registerFooter}>
          <span style={{ color: "var(--text-secondary)" }}>NEW TO ANCESTRA?</span>
          <button
            type="button"
            onClick={() => setIsRegisterOpen(true)}
            style={styles.createAccountBtn}
          >
            CREATE ACCOUNT
          </button>
        </div>
      </div>

      {/* Registration Modal */}
      <RegisterModal
        isOpen={isRegisterOpen}
        onClose={() => setIsRegisterOpen(false)}
        onSuccess={handleRegisterSuccess}
      />
    </div>
  );
}

const styles = {
  pageContainer: {
    minHeight: "100vh",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    padding: "20px"
  },
  loginCard: {
    width: "100%",
    maxWidth: "430px",
    backgroundColor: "#FFFFFF",
    padding: "28px"
  },
  brandBox: {
    display: "flex",
    alignItems: "center",
    gap: "12px",
    marginBottom: "16px"
  },
  logoIcon: {
    width: "38px",
    height: "38px",
    backgroundColor: "var(--accent-primary)",
    borderRadius: "6px",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    flexShrink: 0
  },
  brandTitleRow: {
    display: "flex",
    alignItems: "center",
    gap: "8px"
  },
  brandSub: {
    fontSize: "9.5px",
    fontFamily: "var(--font-sans)",
    fontWeight: "700",
    letterSpacing: "0.08em",
    color: "var(--text-muted)",
    marginTop: "1px"
  },
  divider: {
    height: "1px",
    backgroundColor: "var(--border-color)",
    marginBottom: "18px"
  },
  successBanner: {
    display: "flex",
    alignItems: "center",
    gap: "6px",
    padding: "8px 10px",
    backgroundColor: "#F0FDF4",
    border: "1px solid #BBF7D0",
    borderRadius: "4px",
    color: "#16A34A",
    fontSize: "11.5px",
    marginBottom: "12px"
  },
  errorBanner: {
    padding: "8px 10px",
    backgroundColor: "#FEF2F2",
    border: "1px solid #FCA5A5",
    borderRadius: "4px",
    color: "#DC2626",
    fontSize: "11.5px",
    marginBottom: "12px"
  },
  googleSection: {
    marginBottom: "14px"
  },
  googleBtn: {
    width: "100%",
    height: "40px",
    backgroundColor: "#FFFFFF",
    border: "1.5px solid var(--border-color)",
    borderRadius: "4px",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    gap: "10px",
    cursor: "pointer",
    fontFamily: "var(--font-mono)",
    fontWeight: "700",
    fontSize: "11.5px",
    letterSpacing: "0.05em",
    color: "var(--text-primary)",
    transition: "all 0.15s ease",
    boxShadow: "0 1px 2px rgba(0,0,0,0.05)"
  },
  googleIcon: {
    flexShrink: 0
  },
  orDivider: {
    display: "flex",
    alignItems: "center",
    gap: "10px",
    margin: "12px 0 16px 0"
  },
  orLine: {
    flex: 1,
    height: "1px",
    backgroundColor: "var(--border-light)"
  },
  orText: {
    fontSize: "9.5px",
    fontFamily: "var(--font-mono)",
    fontWeight: "700",
    color: "var(--text-muted)",
    letterSpacing: "0.08em"
  },
  form: {
    display: "flex",
    flexDirection: "column",
    gap: "14px"
  },
  inputWrapper: {
    position: "relative",
    display: "flex",
    alignItems: "center"
  },
  inputIcon: {
    position: "absolute",
    left: "10px",
    top: "50%",
    transform: "translateY(-50%)",
    pointerEvents: "none"
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
  },
  optionsRow: {
    display: "flex",
    alignItems: "center",
    justifyContent: "flex-end",
    fontSize: "10.5px"
  },
  forgotLink: {
    color: "var(--accent-primary)",
    textDecoration: "none",
    fontWeight: "700",
    letterSpacing: "0.04em",
    fontFamily: "var(--font-mono)"
  },
  roleSelectionRow: {
    marginTop: "16px",
    paddingTop: "12px",
    borderTop: "1px solid var(--border-light)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    gap: "10px"
  },
  yourRoleLabel: {
    fontSize: "10.5px",
    fontFamily: "var(--font-mono)",
    fontWeight: "700",
    color: "#8E857B",
    letterSpacing: "0.06em"
  },
  roleTabBtn: {
    border: "none",
    padding: "3px 8px",
    borderRadius: "3px",
    fontSize: "10.5px",
    fontFamily: "var(--font-mono)",
    cursor: "pointer",
    transition: "all 0.12s ease"
  },
  registerFooter: {
    marginTop: "16px",
    paddingTop: "14px",
    borderTop: "1px dashed var(--border-color)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    gap: "8px",
    fontSize: "11.5px"
  },
  createAccountBtn: {
    background: "none",
    border: "none",
    color: "var(--accent-primary)",
    fontWeight: "700",
    fontFamily: "var(--font-mono)",
    fontSize: "11px",
    cursor: "pointer",
    letterSpacing: "0.04em"
  }
};
