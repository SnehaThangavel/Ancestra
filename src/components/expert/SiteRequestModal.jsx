import React, { useState } from "react";
import { useApp } from "../../context/AppContext";
import { Modal } from "../common/Modal";
import { ImageUploaderInput } from "../common/ImageUploaderInput";

export function SiteRequestModal({ isOpen, onClose }) {
  const { submitSiteRequest } = useApp();

  const [formData, setFormData] = useState({
    name: "",
    location: "",
    circle: "ASI Chennai Circle",
    material: "Sandstone & Mortar",
    category: "State Protected Structural Site",
    description: "",
    image: ""
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!formData.name || !formData.location || !formData.image) {
      alert("Please enter site name, location, and upload a photograph.");
      return;
    }

    submitSiteRequest(formData);
    setFormData({
      name: "",
      location: "",
      circle: "ASI Chennai Circle",
      material: "Sandstone & Mortar",
      category: "State Protected Structural Site",
      description: "",
      image: ""
    });
    onClose();
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="SUBMIT NEW HERITAGE SITE REQUEST"
      width="580px"
    >
      <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
        <div style={{ fontSize: "12px", color: "var(--text-secondary)", marginBottom: "4px" }}>
          Submit a proposal for a new heritage monument site to be registered into the ANCESTRA structural monitoring platform. Subject to Administrator review.
        </div>

        <div className="form-group">
          <label className="form-label">HERITAGE SITE NAME *</label>
          <input
            type="text"
            className="form-input"
            placeholder="e.g. Kailasanathar Temple, Kanchipuram"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            required
          />
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
          <div className="form-group">
            <label className="form-label">LOCATION & STATE *</label>
            <input
              type="text"
              className="form-input"
              placeholder="e.g. Kanchipuram, Tamil Nadu"
              value={formData.location}
              onChange={(e) => setFormData({ ...formData, location: e.target.value })}
              required
            />
          </div>

          <div className="form-group">
            <label className="form-label">ASI CIRCLE</label>
            <select
              className="form-select"
              value={formData.circle}
              onChange={(e) => setFormData({ ...formData, circle: e.target.value })}
            >
              <option value="ASI Chennai Circle">ASI Chennai Circle</option>
              <option value="ASI Bengaluru Circle">ASI Bengaluru Circle</option>
              <option value="ASI Bhubaneswar Circle">ASI Bhubaneswar Circle</option>
              <option value="ASI Agra Circle">ASI Agra Circle</option>
              <option value="ASI Delhi Circle">ASI Delhi Circle</option>
            </select>
          </div>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
          <div className="form-group">
            <label className="form-label">CONSTRUCTION MATERIAL</label>
            <input
              type="text"
              className="form-input"
              placeholder="e.g. Sandstone, Granite, Mortar"
              value={formData.material}
              onChange={(e) => setFormData({ ...formData, material: e.target.value })}
            />
          </div>

          <div className="form-group">
            <label className="form-label">HERITAGE CATEGORY</label>
            <select
              className="form-select"
              value={formData.category}
              onChange={(e) => setFormData({ ...formData, category: e.target.value })}
            >
              <option value="State Protected Structural Site">State Protected Structural Site</option>
              <option value="National Monument of Importance">National Monument of Importance</option>
              <option value="UNESCO World Heritage Site">UNESCO World Heritage Site</option>
            </select>
          </div>
        </div>

        {/* Drag & Drop File Upload Component */}
        <ImageUploaderInput
          value={formData.image}
          onChange={(imgData) => setFormData({ ...formData, image: imgData })}
          label="HERITAGE SITE PHOTOGRAPH *"
        />

        <div className="form-group">
          <label className="form-label">HISTORICAL ARCHITECTURAL DESCRIPTION</label>
          <textarea
            className="form-textarea"
            rows="3"
            placeholder="Brief architectural layout, key structural vulnerabilities..."
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
          />
        </div>

        <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px", marginTop: "10px" }}>
          <button type="button" onClick={onClose} className="btn-secondary">
            Cancel
          </button>
          <button type="submit" className="btn-primary">
            Submit Site Request
          </button>
        </div>
      </form>
    </Modal>
  );
}
