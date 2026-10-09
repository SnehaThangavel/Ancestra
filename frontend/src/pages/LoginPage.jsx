import React, { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useApp } from "../context/AppContext";
import { Building2 } from "lucide-react";

export function LoginPage() {
  const navigate = useNavigate();
  const { login, loginWithGoogle, isAuthenticated, isAuthLoading } = useApp();

  // If already logged in, redirect directly to dashboard
  useEffect(() => {
    if (!isAuthLoading && isAuthenticated) {
      navigate("/dashboard", { replace: true });
    }
  }, [isAuthenticated, isAuthLoading, navigate]);

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

        <div style={{ marginBottom: "20px" }}>
          <h2 className="font-serif-heading" style={{ fontSize: "16px", margin: 0 }}>
            WELCOME TO ANCESTRA
          </h2>
          <p style={{ fontSize: "12px", color: "var(--text-muted)", marginTop: "4px" }}>
            Sign in with your verified organization account to access the heritage conservation workspace.
          </p>
        </div>

        {/* Google OAuth Login Button */}
        <div style={styles.googleSection}>
          <button
            type="button"
            onClick={loginWithGoogle}
            style={styles.googleBtn}
            id="google-signin-button"
            title="Sign in securely with Google SSO"
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

        {/* Development Mode Bypass (Strictly DEV Only) */}
        {import.meta.env.DEV && (
          <div style={styles.devBox}>
            <div style={styles.devHeader}>LOCAL DEVELOPMENT MODE</div>
            <p style={styles.devSub}>Simulate session without active Google OAuth credentials in local dev:</p>
            <div style={{ display: "flex", gap: "8px" }}>
              <button
                type="button"
                onClick={() => {
                  const res = login("expert@ancestra.org");
                  if (res.success) navigate("/dashboard");
                }}
                className="btn-secondary"
                style={{ flex: 1, padding: "8px 10px", fontSize: "11px" }}
              >
                Sign in as Expert (Dev)
              </button>
              <button
                type="button"
                onClick={() => {
                  const res = login("admin@ancestra.org");
                  if (res.success) navigate("/dashboard");
                }}
                className="btn-secondary"
                style={{ flex: 1, padding: "8px 10px", fontSize: "11px" }}
              >
                Sign in as Admin (Dev)
              </button>
            </div>
          </div>
        )}
      </div>
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
  googleSection: {
    marginBottom: "14px"
  },
  googleBtn: {
    width: "100%",
    height: "42px",
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
  devBox: {
    marginTop: "20px",
    padding: "14px",
    backgroundColor: "#FAF8F5",
    border: "1px dashed var(--border-color)",
    borderRadius: "6px"
  },
  devHeader: {
    fontSize: "10px",
    fontFamily: "var(--font-mono)",
    fontWeight: "700",
    color: "var(--accent-primary)",
    letterSpacing: "0.08em",
    marginBottom: "4px"
  },
  devSub: {
    fontSize: "11px",
    color: "var(--text-secondary)",
    margin: "0 0 10px 0"
  }
};
