import React, { useState, useEffect } from "react";
import { Modal } from "../common/Modal";
import { useApp } from "../../context/AppContext";

export function RegionModal({ isOpen, onClose, regionToEdit = null }) {
  const { heritageSites, addArchitecturalRegion, updateArchitecturalRegion } = useApp();

  const [formData, setFormData] = useState({
    siteId: heritageSites[0]?.id || "site_01",
    code: "REG-NEW-01",
    name: "",
    type: "Wall",
    importance: "Load-Bearing Wall Course",
    riskLevel: "LOW"
  });

  useEffect(() => {
    if (regionToEdit) {
      setFormData({
        siteId: regionToEdit.siteId || heritageSites[0]?.id || "site_01",
        code: regionToEdit.code || "REG-NEW-01",
        name: regionToEdit.name || "",
        type: regionToEdit.type || "Wall",
        importance: regionToEdit.importance || "",
        riskLevel: regionToEdit.riskLevel || "LOW"
      });
    } else {
      setFormData({
        siteId: heritageSites[0]?.id || "site_01",
        code: "REG-NEW-01",
        name: "",
        type: "Wall",
        importance: "Load-Bearing Wall Course",
        riskLevel: "LOW"
      });
    }
  }, [regionToEdit, isOpen]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!formData.name) return;

    if (regionToEdit) {
      const site = heritageSites.find((s) => s.id === formData.siteId);
      updateArchitecturalRegion(regionToEdit.id, {
        ...formData,
        siteName: site ? site.name : regionToEdit.siteName
      });
    } else {
      addArchitecturalRegion(formData);
    }
    onClose();
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={regionToEdit ? "EDIT ARCHITECTURAL REGION" : "ADD ARCHITECTURAL REGION"}
      width="540px"
    >
      <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
        <div className="form-group">
          <label className="form-label">TARGET HERITAGE MONUMENT *</label>
          <select
            className="form-select"
            value={formData.siteId}
            onChange={(e) => setFormData({ ...formData, siteId: e.target.value })}
          >
            {heritageSites.map((site) => (
              <option key={site.id} value={site.id}>
                {site.name}
              </option>
            ))}
          </select>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
          <div className="form-group">
            <label className="form-label">REGION IDENTIFIER / CODE</label>
            <input
              type="text"
              className="form-input"
              value={formData.code}
              onChange={(e) => setFormData({ ...formData, code: e.target.value })}
            />
          </div>

          <div className="form-group">
            <label className="form-label">REGION TYPE</label>
            <select
              className="form-select"
              value={formData.type}
              onChange={(e) => setFormData({ ...formData, type: e.target.value })}
            >
              <option value="Wall">Wall</option>
              <option value="Pillar">Pillar</option>
              <option value="Arch">Arch</option>
              <option value="Dome">Dome</option>
              <option value="Roof">Roof</option>
              <option value="Sculpture">Sculpture</option>
              <option value="Inscription">Inscription</option>
              <option value="Other">Other</option>
            </select>
          </div>
        </div>

        <div className="form-group">
          <label className="form-label">ARCHITECTURAL REGION NAME *</label>
          <input
            type="text"
            className="form-input"
            placeholder="e.g. Southern Base Plinth Niche"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            required
          />
        </div>

        <div className="form-group">
          <label className="form-label">STRUCTURAL IMPORTANCE & DESCRIPTION</label>
          <input
            type="text"
            className="form-input"
            placeholder="e.g. Primary load distribution column"
            value={formData.importance}
            onChange={(e) => setFormData({ ...formData, importance: e.target.value })}
          />
        </div>

        <div className="form-group">
          <label className="form-label">RISK LEVEL SEVERITY</label>
          <select
            className="form-select"
            value={formData.riskLevel}
            onChange={(e) => setFormData({ ...formData, riskLevel: e.target.value })}
          >
            <option value="LOW">LOW</option>
            <option value="MEDIUM">MEDIUM</option>
            <option value="HIGH">HIGH</option>
          </select>
        </div>

        <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px", marginTop: "10px" }}>
          <button type="button" onClick={onClose} className="btn-secondary">
            Cancel
          </button>
          <button type="submit" className="btn-primary">
            {regionToEdit ? "Save Changes" : "Save Region"}
          </button>
        </div>
      </form>
    </Modal>
  );
}
