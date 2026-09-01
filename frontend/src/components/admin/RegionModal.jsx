import React, { useState, useEffect } from "react";
import { useApp } from "../../context/AppContext";
import { Modal } from "../common/Modal";

export function RegionModal({ isOpen, onClose, regionToEdit = null }) {
  const { heritageSites, architecturalRegions, addArchitecturalRegion, updateArchitecturalRegion } = useApp();

  const isEditing = Boolean(regionToEdit);

  // Generate a unique permanent Region ID for new regions
  const generateUniqueRegionId = () => {
    const existingCodes = architecturalRegions.map((r) => r.code);
    let nextNum = architecturalRegions.length + 1;
    let newCode = `REG-${String(nextNum).padStart(3, "0")}`;
    while (existingCodes.includes(newCode)) {
      nextNum++;
      newCode = `REG-${String(nextNum).padStart(3, "0")}`;
    }
    return newCode;
  };

  const [formData, setFormData] = useState({
    code: "",
    siteId: heritageSites[0]?.id || "site_01",
    siteName: heritageSites[0]?.name || "Shore Temple, Mahabalipuram",
    name: "",
    importance: "Primary Load-Bearing Course",
    riskLevel: "MEDIUM"
  });

  useEffect(() => {
    if (regionToEdit) {
      setFormData({
        code: regionToEdit.code || "REG-001",
        siteId: regionToEdit.siteId || heritageSites[0]?.id,
        siteName: regionToEdit.siteName || heritageSites[0]?.name,
        name: regionToEdit.name || "",
        importance: regionToEdit.importance || "Primary Load-Bearing Course",
        riskLevel: regionToEdit.riskLevel || "MEDIUM"
      });
    } else {
      setFormData({
        code: generateUniqueRegionId(),
        siteId: heritageSites[0]?.id || "site_01",
        siteName: heritageSites[0]?.name || "Shore Temple, Mahabalipuram",
        name: "",
        importance: "Primary Load-Bearing Course",
        riskLevel: "MEDIUM"
      });
    }
  }, [regionToEdit, isOpen, architecturalRegions]);

  const handleSiteChange = (e) => {
    const sId = e.target.value;
    const siteObj = heritageSites.find((s) => s.id === sId);
    setFormData({
      ...formData,
      siteId: sId,
      siteName: siteObj ? siteObj.name : ""
    });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!formData.name) return;

    if (isEditing) {
      updateArchitecturalRegion(regionToEdit.id, formData);
    } else {
      addArchitecturalRegion(formData);
    }

    onClose();
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={isEditing ? "EDIT ARCHITECTURAL REGION" : "ADD ARCHITECTURAL REGION"}
      width="520px"
    >
      <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
          {/* Read-Only Auto-Generated Permanent Region ID */}
          <div className="form-group">
            <label className="form-label">REGION ID *</label>
            <input
              type="text"
              className="form-input"
              style={{
                backgroundColor: "#F0EBE1",
                color: "#78716C",
                fontFamily: "var(--font-mono)",
                fontWeight: "700",
                cursor: "not-allowed"
              }}
              value={formData.code}
              readOnly
              disabled
            />
            <span style={{ fontSize: "9.5px", color: "var(--text-muted)", marginTop: "2px" }}>
              Auto-generated unique region code
            </span>
          </div>

          <div className="form-group">
            <label className="form-label">HERITAGE MONUMENT *</label>
            <select className="form-select" value={formData.siteId} onChange={handleSiteChange}>
              {heritageSites.map((site) => (
                <option key={site.id} value={site.id}>
                  {site.name}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="form-group">
          <label className="form-label">ARCHITECTURAL REGION NAME *</label>
          <input
            type="text"
            className="form-input"
            placeholder="e.g. East-Facing Rajasimhesvara Vimana"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            required
          />
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
          <div className="form-group">
            <label className="form-label">STRUCTURAL IMPORTANCE</label>
            <select
              className="form-select"
              value={formData.importance}
              onChange={(e) => setFormData({ ...formData, importance: e.target.value })}
            >
              <option value="Primary Load-Bearing Course">Primary Load-Bearing Course</option>
              <option value="Secondary Structural Member">Secondary Structural Member</option>
              <option value="Architectural Facade / Carving">Architectural Facade / Carving</option>
              <option value="Foundation & Plinth Course">Foundation & Plinth Course</option>
            </select>
          </div>

          <div className="form-group">
            <label className="form-label">MONITORING RISK LEVEL</label>
            <select
              className="form-select"
              value={formData.riskLevel}
              onChange={(e) => setFormData({ ...formData, riskLevel: e.target.value })}
            >
              <option value="LOW">LOW RISK</option>
              <option value="MEDIUM">MEDIUM RISK</option>
              <option value="HIGH">HIGH RISK</option>
              <option value="CRITICAL">CRITICAL RISK</option>
            </select>
          </div>
        </div>

        <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px", marginTop: "10px" }}>
          <button type="button" onClick={onClose} className="btn-secondary">
            Cancel
          </button>
          <button type="submit" className="btn-primary">
            {isEditing ? "Save Changes" : "Add Region"}
          </button>
        </div>
      </form>
    </Modal>
  );
}
