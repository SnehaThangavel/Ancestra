import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useApp } from "../context/AppContext";
import { RegisterModal } from "../components/auth/RegisterModal";
import { Building2, Lock, Mail, ArrowRight, Eye, EyeOff, CheckCircle } from "lucide-react";

export function LoginPage() {
  const navigate = useNavigate();
  const { login } = useApp();

  const [emailOrPhone, setEmailOrPhone] = useState("a.sharma@asi.gov.in");
  const [password, setPassword] = useState("password123");
  const [showPassword, setShowPassword] = useState(false);

  const [isRegisterOpen, setIsRegisterOpen] = useState(false);
  const [successMsg, setSuccessMsg] = useState("");
  const [errorMsg, setErrorMsg] = useState("");

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

  const setDemoAccount = (email, pass) => {
    setEmailOrPhone(email);
    setPassword(pass);
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
              <span className="version-pill">v0.1</span>
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

        {/* Quick Demo Pre-fill Links for Testing */}
        <div style={styles.demoAccountsRow}>
          <span style={{ fontSize: "10px", color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
            DEMO PRESETS:
          </span>
          <button
            type="button"
            onClick={() => setDemoAccount("a.sharma@asi.gov.in", "password123")}
            style={styles.demoBtn}
          >
            EXPERT
          </button>
          <span style={{ color: "var(--border-color)" }}>|</span>
          <button
            type="button"
            onClick={() => setDemoAccount("s.ranganathan@ancestra.org", "password123")}
            style={styles.demoBtn}
          >
            ADMIN
          </button>
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
    pointerEvents: "none"
  },
  eyeBtn: {
    position: "absolute",
    right: "10px",
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
  demoAccountsRow: {
    marginTop: "12px",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    gap: "8px"
  },
  demoBtn: {
    background: "none",
    border: "none",
    color: "var(--accent-primary)",
    fontSize: "10px",
    fontFamily: "var(--font-mono)",
    fontWeight: "700",
    cursor: "pointer",
    padding: "2px 4px"
  },
  registerFooter: {
    marginTop: "20px",
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
