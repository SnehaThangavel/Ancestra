import React, { createContext, useContext, useState } from "react";
import {
  USERS,
  INITIAL_HERITAGE_SITES,
  INITIAL_ARCHITECTURAL_REGIONS,
  INITIAL_ASSESSMENTS,
  INITIAL_REPORTS,
  INITIAL_NOTIFICATIONS
} from "../data/mockData";

const AppContext = createContext(null);

export function AppProvider({ children }) {
  // Registered Users Registry
  const [registeredUsers, setRegisteredUsers] = useState([
    {
      id: "usr_exp_01",
      name: "Dr. A. Sharma",
      emailOrPhone: "a.sharma@asi.gov.in",
      password: "password123",
      title: "Lead Conservator (ASI)",
      role: "CONSERVATION_EXPERT",
      avatar: "https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&q=80&w=150"
    },
    {
      id: "usr_adm_01",
      name: "Dr. S. Ranganathan",
      emailOrPhone: "s.ranganathan@ancestra.org",
      password: "password123",
      title: "System Administrator",
      role: "ADMINISTRATOR",
      avatar: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&q=80&w=150"
    }
  ]);

  // Auth & Role State
  const [currentUser, setCurrentUser] = useState(registeredUsers[0]);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  // Core Collections
  const [heritageSites, setHeritageSites] = useState(INITIAL_HERITAGE_SITES);
  const [architecturalRegions, setArchitecturalRegions] = useState(INITIAL_ARCHITECTURAL_REGIONS);
  const [assessments, setAssessments] = useState(INITIAL_ASSESSMENTS);
  const [reports, setReports] = useState(INITIAL_REPORTS);
  const [notifications, setNotifications] = useState(INITIAL_NOTIFICATIONS);

  // AI Assessment Engine System Status
  const [aiEngineStatus, setAiEngineStatus] = useState({
    online: true,
    modelState: "READY" // READY, TRAINING, UPDATING, MAINTENANCE, ERROR
  });

  // Global Context State
  const [activeSiteId, setActiveSiteId] = useState("site_01");
  const [pendingAnalysis, setPendingAnalysis] = useState(null);
  const [activeResult, setActiveResult] = useState(INITIAL_ASSESSMENTS[0]);
  const [toast, setToast] = useState(null);

  // Toast Helper
  const showToast = (message, type = "success") => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 4000);
  };

  // Login Authentication Handler
  const login = (emailOrPhone, password) => {
    const foundUser = registeredUsers.find(
      (u) =>
        (u.emailOrPhone.toLowerCase() === emailOrPhone.trim().toLowerCase() ||
          u.emailOrPhone === emailOrPhone.trim()) &&
        u.password === password
    );

    if (foundUser) {
      setCurrentUser(foundUser);
      setIsAuthenticated(true);
      return { success: true, role: foundUser.role };
    }

    return { success: false, message: "Invalid email/phone number or password." };
  };

  // Register User
  const registerUser = ({ fullName, emailOrPhone, password, designation, role }) => {
    const exists = registeredUsers.some(
      (u) => u.emailOrPhone.toLowerCase() === emailOrPhone.trim().toLowerCase()
    );

    if (exists) {
      return { success: false, message: "An account with this email/phone number already exists." };
    }

    const newUser = {
      id: `usr_${Date.now()}`,
      name: fullName,
      emailOrPhone: emailOrPhone.trim(),
      password: password,
      title: designation || (role === "ADMINISTRATOR" ? "System Administrator" : "Conservation Expert"),
      role: role === "ADMINISTRATOR" ? "ADMINISTRATOR" : "CONSERVATION_EXPERT",
      avatar: "https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&q=80&w=150"
    };

    setRegisteredUsers((prev) => [...prev, newUser]);
    return { success: true, user: newUser };
  };

  const logout = () => {
    setIsAuthenticated(false);
    setCurrentUser(null);
  };

  // AI Engine Status Updates (Admin Only)
  const updateAiEngineStatus = (newStatus) => {
    setAiEngineStatus(newStatus);
    showToast("AI ASSESSMENT ENGINE STATUS UPDATED.");
  };

  // Heritage Site CRUD
  const addHeritageSite = (siteData) => {
    const newSite = {
      ...siteData,
      id: `site_${Date.now()}`,
      code: siteData.code || `STE-${Math.floor(10 + Math.random() * 90)}`,
      healthScore: 80,
      regionsCount: 0,
      lastAssessment: new Date().toISOString().split("T")[0],
      status: "STABLE",
      image: siteData.image || "https://images.unsplash.com/photo-1582510003544-4d00b7f74220?auto=format&fit=crop&q=80&w=800"
    };
    setHeritageSites((prev) => [newSite, ...prev]);
    showToast("HERITAGE SITE REGISTERED SUCCESSFULLY.");
  };

  const updateHeritageSite = (siteId, updatedFields) => {
    setHeritageSites((prev) =>
      prev.map((s) => (s.id === siteId ? { ...s, ...updatedFields } : s))
    );
    showToast("HERITAGE SITE UPDATED SUCCESSFULLY.");
  };

  const deleteHeritageSite = (siteId) => {
    setHeritageSites((prev) => prev.filter((s) => s.id !== siteId));
    // Also remove associated architectural regions
    setArchitecturalRegions((prev) => prev.filter((r) => r.siteId !== siteId));
    showToast("HERITAGE SITE DELETED SUCCESSFULLY.");
  };

  // Architectural Region CRUD
  const addArchitecturalRegion = (regionData) => {
    const site = heritageSites.find((s) => s.id === regionData.siteId);
    const newRegion = {
      ...regionData,
      id: `reg_${Date.now()}`,
      siteName: site ? site.name : "Unknown Heritage Site",
      lastAssessment: new Date().toISOString().split("T")[0],
      damageScore: 30,
      condition: "STABLE",
      riskLevel: regionData.riskLevel || "LOW"
    };
    setArchitecturalRegions((prev) => [newRegion, ...prev]);
    setHeritageSites((prev) =>
      prev.map((s) => (s.id === regionData.siteId ? { ...s, regionsCount: (s.regionsCount || 0) + 1 } : s))
    );
    showToast("ARCHITECTURAL REGION ADDED SUCCESSFULLY.");
  };

  const updateArchitecturalRegion = (regionId, updatedFields) => {
    setArchitecturalRegions((prev) =>
      prev.map((r) => (r.id === regionId ? { ...r, ...updatedFields } : r))
    );
    showToast("ARCHITECTURAL REGION UPDATED SUCCESSFULLY.");
  };

  const deleteArchitecturalRegion = (regionId) => {
    setArchitecturalRegions((prev) => prev.filter((r) => r.id !== regionId));
    showToast("ARCHITECTURAL REGION DELETED SUCCESSFULLY.");
  };

  // Record AI Assessment Result
  const recordAssessmentResult = (resultObj) => {
    setAssessments((prev) => [resultObj, ...prev]);
    setActiveResult(resultObj);
    
    if (resultObj.emergencyLevel === "Critical" || resultObj.severity === "High") {
      addNotification({
        title: "CRITICAL STRUCTURAL DAMAGE DETECTED",
        description: `${resultObj.damageType} detected at ${resultObj.regionName} (${resultObj.siteName}). AI confidence: ${(resultObj.confidence * 100).toFixed(0)}%.`,
        priority: "Critical",
        link: "/expert/results"
      });
    }
  };

  // Expert Status Update
  const updateAssessmentStatus = (assessmentId, status, notes = "") => {
    setAssessments((prev) =>
      prev.map((asm) => (asm.id === assessmentId ? { ...asm, status, expertNotes: notes || asm.expertNotes } : asm))
    );
    if (activeResult && activeResult.id === assessmentId) {
      setActiveResult((prev) => ({ ...prev, status, expertNotes: notes || prev.expertNotes }));
    }
    showToast(`ASSESSMENT MARKED AS ${status.toUpperCase()}.`);
  };

  // Generate Report
  const generateReportFromAssessment = (assessmentObj) => {
    const asm = assessmentObj || activeResult;
    if (!asm) return;

    const newReport = {
      id: `REP-2026-${Math.floor(100 + Math.random() * 900)}`,
      assessmentId: asm.id,
      siteName: asm.siteName,
      regionName: asm.regionName,
      date: new Date().toISOString().split("T")[0],
      damageType: asm.damageType,
      severity: asm.severity,
      confidence: typeof asm.confidence === "number" ? `${(asm.confidence * 100).toFixed(0)}%` : asm.confidence,
      emergencyLevel: asm.emergencyLevel,
      status: "Generated",
      expertName: currentUser?.name || "Dr. A. Sharma",
      summary: asm.recommendation || "Conservation inspection and periodic monitoring advised."
    };

    setReports((prev) => [newReport, ...prev]);
    showToast("NEW CONSERVATION REPORT GENERATED.");
    return newReport;
  };

  // Notifications
  const addNotification = ({ title, description, priority = "Info", link = "/notifications" }) => {
    const newNotif = {
      id: `notif_${Date.now()}`,
      title,
      description,
      time: "Just now",
      priority,
      read: false,
      link
    };
    setNotifications((prev) => [newNotif, ...prev]);
  };

  const markNotificationAsRead = (id) => {
    setNotifications((prev) =>
      prev.map((n) => (n.id === id ? { ...n, read: true } : n))
    );
  };

  const activeSite = heritageSites.find((s) => s.id === activeSiteId) || heritageSites[0];

  return (
    <AppContext.Provider
      value={{
        currentUser,
        setCurrentUser,
        isAuthenticated,
        login,
        registerUser,
        logout,
        registeredUsers,
        heritageSites,
        addHeritageSite,
        updateHeritageSite,
        deleteHeritageSite,
        architecturalRegions,
        addArchitecturalRegion,
        updateArchitecturalRegion,
        deleteArchitecturalRegion,
        assessments,
        recordAssessmentResult,
        updateAssessmentStatus,
        activeResult,
        setActiveResult,
        pendingAnalysis,
        setPendingAnalysis,
        reports,
        generateReportFromAssessment,
        notifications,
        addNotification,
        markNotificationAsRead,
        aiEngineStatus,
        updateAiEngineStatus,
        activeSiteId,
        setActiveSiteId,
        activeSite,
        toast,
        showToast
      }}
    >
      {children}
    </AppContext.Provider>
  );
}

export function useApp() {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error("useApp must be used within an AppProvider");
  }
  return context;
}
