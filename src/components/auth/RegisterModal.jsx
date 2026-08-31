import React, { useState } from "react";
import { Modal } from "../common/Modal";
import { useApp } from "../../context/AppContext";
import { Eye, EyeOff, UserPlus, CheckCircle } from "lucide-react";

export function RegisterModal({ isOpen, onClose, onSuccess }) {
  const { registerUser } = useApp();
  const [fullName, setFullName] = useState("");
  const [emailOrPhone, setEmailOrPhone] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [designation, setDesignation] = useState("");
  const [role, setRole] = useState("CONSERVATION_EXPERT");

  const [showPassword, setShowPassword] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    setErrorMsg("");

    if (!fullName || !emailOrPhone || !password || !confirmPassword) {
      setErrorMsg("Please fill in all required fields.");
      return;
    }

    if (password !== confirmPassword) {
      setErrorMsg("Passwords do not match.");
      return;
    }

    const res = registerUser({
      fullName,
      emailOrPhone,
      password,
      designation,
      role
    });

    if (res.success) {
      onSuccess(emailOrPhone);
      onClose();
    } else {
      setErrorMsg(res.message);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="CREATE ANCESTRA ACCOUNT" width="500px">
      <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
        {errorMsg && (
          <div style={styles.errorBanner}>
            <span>{errorMsg}</span>
          </div>
        )}

        <div className="form-group">
          <label className="form-label">FULL NAME *</label>
          <input
            type="text"
            className="form-input"
            placeholder="e.g. Dr. Rajesh Kumar"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            required
          />
        </div>

        <div className="form-group">
          <label className="form-label">EMAIL OR PHONE NUMBER *</label>
          <input
            type="text"
            className="form-input"
            placeholder="e.g. r.kumar@asi.gov.in or 9876543210"
            value={emailOrPhone}
            onChange={(e) => setEmailOrPhone(e.target.value)}
            required
          />
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
          <div className="form-group">
            <label className="form-label">PASSWORD *</label>
            <div style={{ position: "relative" }}>
              <input
                type={showPassword ? "text" : "password"}
                className="form-input"
                style={{ paddingRight: "32px" }}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
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

          <div className="form-group">
            <label className="form-label">CONFIRM PASSWORD *</label>
            <input
              type={showPassword ? "text" : "password"}
              className="form-input"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
            />
          </div>
        </div>

        <div className="form-group">
          <label className="form-label">OFFICIAL DESIGNATION / TITLE</label>
          <input
            type="text"
            className="form-input"
            placeholder="e.g. Senior Archaeologist / Conservator"
            value={designation}
            onChange={(e) => setDesignation(e.target.value)}
          />
        </div>

        <div className="form-group">
          <label className="form-label">ACCOUNT ROLE *</label>
          <select
            className="form-select"
            value={role}
            onChange={(e) => setRole(e.target.value)}
          >
            <option value="CONSERVATION_EXPERT">CONSERVATION EXPERT</option>
            <option value="ADMINISTRATOR">ADMINISTRATOR</option>
          </select>
        </div>

        <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px", marginTop: "10px" }}>
          <button type="button" onClick={onClose} className="btn-secondary">
            Cancel
          </button>
          <button type="submit" className="btn-primary">
            <UserPlus size={14} />
            <span>Create Account</span>
          </button>
        </div>
      </form>
    </Modal>
  );
}

const styles = {
  errorBanner: {
    padding: "8px 12px",
    backgroundColor: "#FEF2F2",
    border: "1px solid #FCA5A5",
    borderRadius: "4px",
    color: "#DC2626",
    fontSize: "11.5px"
  },
  eyeBtn: {
    position: "absolute",
    right: "8px",
    top: "50%",
    transform: "translateY(-50%)",
    background: "none",
    border: "none",
    cursor: "pointer",
    padding: 0
  }
};
