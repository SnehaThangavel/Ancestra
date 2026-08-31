import React, { useState } from "react";
import { Modal } from "../common/Modal";
import { useApp } from "../../context/AppContext";
import { Cpu, CheckCircle } from "lucide-react";

export function EngineStatusModal({ isOpen, onClose }) {
  const { aiEngineStatus, updateAiEngineStatus } = useApp();
  const [online, setOnline] = useState(aiEngineStatus.online);
  const [modelState, setModelState] = useState(aiEngineStatus.modelState);

  const handleSubmit = (e) => {
    e.preventDefault();
    updateAiEngineStatus({
      online: Boolean(online),
      modelState
    });
    onClose();
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="EDIT AI ASSESSMENT ENGINE STATUS" width="460px">
      <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
        <div className="form-group">
          <label className="form-label">AI ENGINE SYSTEM STATUS *</label>
          <select
            className="form-select"
            value={online ? "ONLINE" : "OFFLINE"}
            onChange={(e) => setOnline(e.target.value === "ONLINE")}
          >
            <option value="ONLINE">● ONLINE (System Operational)</option>
            <option value="OFFLINE">● OFFLINE (System Suspended)</option>
          </select>
        </div>

        <div className="form-group">
          <label className="form-label">MODEL STATE / OPERATIONAL MODE *</label>
          <select
            className="form-select"
            value={modelState}
            onChange={(e) => setModelState(e.target.value)}
          >
            <option value="READY">READY (Operational & Listening)</option>
            <option value="TRAINING">TRAINING (Model Weights Fine-Tuning)</option>
            <option value="UPDATING">UPDATING (Deploying New Model Version)</option>
            <option value="MAINTENANCE">MAINTENANCE (Scheduled System Service)</option>
            <option value="ERROR">ERROR (Hardware/Pipeline Error)</option>
          </select>
        </div>

        <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px", marginTop: "10px" }}>
          <button type="button" onClick={onClose} className="btn-secondary">
            Cancel
          </button>
          <button type="submit" className="btn-primary">
            Save Status
          </button>
        </div>
      </form>
    </Modal>
  );
}
