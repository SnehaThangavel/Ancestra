/**
 * ANCESTRA AI Perception Engine (Simulated Endpoint)
 * 
 * Simulates deep computer vision analysis on uploaded heritage structural imagery.
 * Designed as a mock service layer that can easily be swapped with a real Python FastAPI / PyTorch backend endpoint.
 */

export const DAMAGE_TYPES = [
  "No Significant Damage",
  "Structural Crack",
  "Salt Efflorescence & Erosion",
  "Surface Spalling",
  "Biological Growth & Lichen",
  "Mortar Dislodgement"
];

export const SEVERITY_LEVELS = ["Low", "Medium", "High"];
export const EMERGENCY_LEVELS = ["Normal", "Monitor", "Attention", "Urgent", "Critical"];

export async function analyzeHeritageImage({ siteId, siteName, regionId, regionName, imageFile, imagePreviewUrl }) {
  // Simulate 3-second backend computer vision processing
  await new Promise(resolve => setTimeout(resolve, 3000));

  // Determine output based on region or randomize realistic parameters
  const isHighRisk = regionName?.toLowerCase().includes("vimana") || regionName?.toLowerCase().includes("roof");
  
  const damageType = isHighRisk ? "Structural Crack" : "Salt Efflorescence & Erosion";
  const severity = isHighRisk ? "High" : "Medium";
  const confidence = isHighRisk ? 0.94 : 0.88;
  const damageTrend = isHighRisk ? "Increasing" : "Stable";
  const emergencyLevel = isHighRisk ? "Critical" : "Attention";
  const recommendation = isHighRisk
    ? "Immediate conservation inspection and structural shoring recommended. Execute micro-fracture salt extraction treatment within 7 days."
    : "Routine quarterly monitoring recommended. Apply non-invasive surface consolidation buffer.";

  const assessmentId = `ASM-2026-${Math.floor(100 + Math.random() * 900)}`;

  return {
    id: assessmentId,
    siteId: siteId || "site_01",
    siteName: siteName || "Shore Temple, Mahabalipuram",
    regionId: regionId || "reg_01",
    regionName: regionName || "East-Facing Rajasimhesvara Vimana",
    date: new Date().toISOString().split("T")[0],
    damageType,
    severity,
    confidence,
    damageTrend,
    emergencyLevel,
    recommendation,
    status: "Pending Review",
    imageUrl: imagePreviewUrl || "https://images.unsplash.com/photo-1582510003544-4d00b7f74220?auto=format&fit=crop&q=80&w=800",
    expertNotes: "AI model detected micro-shear propagation along the structural stone joints.",
    historicalData: [
      { date: "Jan 2026", score: 25 },
      { date: "Mar 2026", score: 38 },
      { date: "May 2026", score: 54 },
      { date: "Jul 2026", score: 72 },
      { date: "Aug 2026", score: Math.round(confidence * 90) }
    ]
  };
}
