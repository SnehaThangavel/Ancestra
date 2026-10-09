import React, { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useApp } from "../context/AppContext";
import { Building2, Loader2, AlertCircle } from "lucide-react";

export function AuthCallback() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { handleAuthCallback } = useApp();
  const [error, setError] = useState(null);

  useEffect(() => {
    let isMounted = true;

    async function processAuth() {
      // 1. Check for query parameters (?access_token=...&refresh_token=...)
      let accessToken = searchParams.get("access_token");
      let refreshToken = searchParams.get("refresh_token");
      const errorParam = searchParams.get("error") || searchParams.get("detail");

      // 2. Check for hash parameters (#access_token=...&refresh_token=...)
      if (!accessToken && window.location.hash) {
        const hashParams = new URLSearchParams(window.location.hash.substring(1));
        accessToken = hashParams.get("access_token");
        refreshToken = hashParams.get("refresh_token");
      }

      // 3. Check localStorage if already initialized
      if (!accessToken) {
        accessToken = localStorage.getItem("ancestra_access_token");
        refreshToken = localStorage.getItem("ancestra_refresh_token");
      }

      if (errorParam) {
        if (isMounted) setError(`Authentication Error: ${decodeURIComponent(errorParam)}`);
        return;
      }

      if (!accessToken) {
        if (isMounted) setError("Missing authentication token from OAuth provider.");
        return;
      }

      try {
        const result = await handleAuthCallback(accessToken, refreshToken);
        if (!isMounted) return;

        if (result.success) {
          window.history.replaceState({}, document.title, window.location.pathname);
          navigate("/dashboard", { replace: true });
        } else {
          setError(result.message || "Failed to authenticate session.");
        }
      } catch (err) {
        if (isMounted) {
          setError(err.message || "Failed to complete authentication handshake.");
        }
      }
    }

    processAuth();

    return () => {
      isMounted = false;
    };
  }, []);

  return (
    <div style={styles.container} className="paper-grid">
      <div style={styles.card} className="ancestra-card">
        {/* Logo */}
        <div style={styles.logoBox}>
          <div style={styles.logoIcon}>
            <Building2 size={24} color="#FFFFFF" />
          </div>
          <div>
            <div style={styles.brandTitle}>ANCESTRA</div>
            <div style={styles.brandSubtitle}>STRUCTURAL INTELLIGENCE</div>
          </div>
        </div>

        <div style={styles.divider} />

        {error ? (
          <div style={styles.errorContainer}>
            <AlertCircle size={28} color="#DC2626" />
            <h3 style={styles.errorHeading}>AUTHENTICATION FAILED</h3>
            <p style={styles.errorText}>{error}</p>
            <button
              onClick={() => navigate("/login")}
              className="btn-primary"
              style={{ marginTop: "12px", width: "100%" }}
            >
              RETURN TO SIGN IN
            </button>
          </div>
        ) : (
          <div style={styles.loadingContainer}>
            <Loader2 size={32} color="#A04022" className="animate-spin" style={styles.spinner} />
            <h3 style={styles.loadingHeading}>AUTHENTICATING SESSION</h3>
            <p style={styles.loadingText}>
              Verifying Google credentials and initializing your conservation workspace...
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

const styles = {
  container: {
    minHeight: "100vh",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    padding: "20px"
  },
  card: {
    width: "100%",
    maxWidth: "420px",
    backgroundColor: "#FFFFFF",
    padding: "32px",
    textAlign: "center"
  },
  logoBox: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    gap: "12px",
    marginBottom: "16px"
  },
  logoIcon: {
    width: "40px",
    height: "40px",
    backgroundColor: "var(--accent-primary)",
    borderRadius: "6px",
    display: "flex",
    alignItems: "center",
    justifyContent: "center"
  },
  brandTitle: {
    fontFamily: "var(--font-serif)",
    fontWeight: "700",
    fontSize: "20px",
    letterSpacing: "0.06em",
    color: "var(--text-primary)"
  },
  brandSubtitle: {
    fontSize: "9px",
    fontFamily: "var(--font-sans)",
    fontWeight: "700",
    letterSpacing: "0.08em",
    color: "var(--text-muted)"
  },
  divider: {
    height: "1px",
    backgroundColor: "var(--border-color)",
    margin: "16px 0 24px 0"
  },
  loadingContainer: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    gap: "12px"
  },
  spinner: {
    animation: "spin 1s linear infinite"
  },
  loadingHeading: {
    fontFamily: "var(--font-serif)",
    fontSize: "16px",
    fontWeight: "700",
    color: "var(--text-primary)",
    margin: 0
  },
  loadingText: {
    fontSize: "12px",
    color: "var(--text-secondary)",
    lineHeight: "1.4",
    margin: 0
  },
  errorContainer: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    gap: "10px"
  },
  errorHeading: {
    fontFamily: "var(--font-serif)",
    fontSize: "15px",
    fontWeight: "700",
    color: "#DC2626",
    margin: 0
  },
  errorText: {
    fontSize: "12px",
    color: "var(--text-secondary)",
    lineHeight: "1.4",
    margin: 0
  }
};
