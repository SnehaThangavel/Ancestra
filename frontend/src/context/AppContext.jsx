import React, { createContext, useContext, useState, useEffect } from "react";
import {
  mockHeritageSites,
  mockArchitecturalRegions,
  mockAssessments,
  mockReports,
  mockNotifications
} from "../data/mockData";
import { api, getAccessToken, getRefreshToken, setTokens, clearTokens } from "../services/api";

const AppContext = createContext();

export function AppProvider({ children }) {
  // Authentication & Current User Role
  const [currentUser, setCurrentUser] = useState({
    id: "exp_01",
    name: "Dr. A. Sharma",
    title: "Lead Conservator (ASI)",
    email: "a.sharma@asi.gov.in",
    role: "CONSERVATION_EXPERT" // "CONSERVATION_EXPERT" or "ADMINISTRATOR"
  });

  const [isAuthenticated, setIsAuthenticated] = useState(() => !!getAccessToken());
  const [isAuthLoading, setIsAuthLoading] = useState(true);

  // Initialize Auth from stored JWT session, URL params, or backend on mount
  useEffect(() => {
    async function initAuth() {
      // 1. Check if tokens arrived in URL search params (?access_token=...&refresh_token=...)
      const searchParams = new URLSearchParams(window.location.search);
      let incomingAccessToken = searchParams.get("access_token");
      let incomingRefreshToken = searchParams.get("refresh_token");

      // 2. Check if tokens arrived in URL hash (#access_token=...&refresh_token=...)
      if (!incomingAccessToken && window.location.hash) {
        const hashParams = new URLSearchParams(window.location.hash.substring(1));
        incomingAccessToken = hashParams.get("access_token");
        incomingRefreshToken = hashParams.get("refresh_token");
      }

      if (incomingAccessToken) {
        setTokens(incomingAccessToken, incomingRefreshToken);
        // Clean URL to prevent tokens from remaining visible in browser address bar
        const cleanUrl = window.location.pathname;
        window.history.replaceState({}, document.title, cleanUrl);
      }

      const token = getAccessToken();
      if (token) {
        try {
          const userProfile = await api.getMe();
          if (userProfile && userProfile.email) {
            const isAdm =
              userProfile.email.toLowerCase().includes("admin") ||
              userProfile.email.toLowerCase().includes("ranganathan");
            setCurrentUser({
              id: userProfile.id,
              name: userProfile.name || userProfile.email.split("@")[0],
              email: userProfile.email,
              picture_url: userProfile.picture_url,
              title: isAdm ? "Director General (ASI)" : "Lead Conservator (ASI)",
              role: isAdm ? "ADMINISTRATOR" : "CONSERVATION_EXPERT",
              is_active: userProfile.is_active,
              isGoogleUser: true
            });
            setIsAuthenticated(true);
          }
        } catch (err) {
          console.warn("Saved token verification failed, attempting refresh:", err);
          const refreshToken = getRefreshToken();
          if (refreshToken) {
            try {
              const refreshed = await api.refreshToken(refreshToken);
              if (refreshed && refreshed.access_token) {
                const userProfile = await api.getMe();
                const isAdm =
                  userProfile.email.toLowerCase().includes("admin") ||
                  userProfile.email.toLowerCase().includes("ranganathan");
                setCurrentUser({
                  id: userProfile.id,
                  name: userProfile.name || userProfile.email.split("@")[0],
                  email: userProfile.email,
                  picture_url: userProfile.picture_url,
                  title: isAdm ? "Director General (ASI)" : "Lead Conservator (ASI)",
                  role: isAdm ? "ADMINISTRATOR" : "CONSERVATION_EXPERT",
                  is_active: userProfile.is_active,
                  isGoogleUser: true
                });
                setIsAuthenticated(true);
              }
            } catch (refErr) {
              console.warn("Token refresh attempt failed:", refErr);
              clearTokens();
              setIsAuthenticated(false);
            }
          } else {
            clearTokens();
            setIsAuthenticated(false);
          }
        }
      } else {
        setIsAuthenticated(false);
      }
      setIsAuthLoading(false);
    }

    initAuth();
  }, []);

  // Application Global Core State
  const [heritageSites, setHeritageSites] = useState(mockHeritageSites);
  const [architecturalRegions, setArchitecturalRegions] = useState(mockArchitecturalRegions);
  const [assessments, setAssessments] = useState(mockAssessments);
  const [reports, setReports] = useState(mockReports);
  const [notifications, setNotifications] = useState(mockNotifications);

  // AI Perception Pipeline Progress State
  const [pipelineStep, setPipelineStep] = useState(1);
  const [isPipelineComplete, setIsPipelineComplete] = useState(false);

  // Heritage Site Requests (Expert -> Admin Workflow)
  const [siteRequests, setSiteRequests] = useState([
    {
      id: "REQ-2026-001",
      expertName: "Dr. A. Sharma",
      expertEmail: "a.sharma@asi.gov.in",
      siteName: "Kailasanathar Temple, Kanchipuram",
      location: "Kanchipuram, Tamil Nadu",
      circle: "ASI Chennai Circle",
      material: "Sandstone & Mortar",
      category: "State Protected Structural Site",
      description: "7th-century Pallava dynasty architectural monument with deteriorating sandstone carvings.",
      image: "https://images.unsplash.com/photo-1627894099419-f5ebba5e3f42?auto=format&fit=crop&q=80&w=800",
      status: "PENDING ADMIN APPROVAL",
      createdAt: "2026-09-01 09:30"
    }
  ]);

  // AI Assessment Engine System Status
  const [aiEngineStatus, setAiEngineStatus] = useState({
    online: true,
    modelState: "READY"
  });

  // Selected Active Context
  const [activeSiteId, setActiveSiteId] = useState("site_01");
  const [pendingAnalysis, setPendingAnalysis] = useState(null);
  const [activeResult, setActiveResult] = useState(mockAssessments[0]);

  // Toast Notification Message State
  const [toast, setToast] = useState(null);

  const showToast = (message, type = "info") => {
    setToast({ message, type });
    setTimeout(() => {
      setToast(null);
    }, 4000);
  };

  // Auth Handlers
  const loginWithGoogle = () => {
    window.location.href = api.getGoogleLoginUrl();
  };

  const handleAuthCallback = async (accessToken, refreshToken) => {
    try {
      setTokens(accessToken, refreshToken);
      const userProfile = await api.getMe();
      if (userProfile && userProfile.email) {
        const isAdm =
          userProfile.email.toLowerCase().includes("admin") ||
          userProfile.email.toLowerCase().includes("ranganathan");
        const mappedUser = {
          id: userProfile.id,
          name: userProfile.name || userProfile.email.split("@")[0],
          email: userProfile.email,
          picture_url: userProfile.picture_url,
          title: isAdm ? "Director General (ASI)" : "Lead Conservator (ASI)",
          role: isAdm ? "ADMINISTRATOR" : "CONSERVATION_EXPERT",
          is_active: userProfile.is_active,
          isGoogleUser: true
        };
        setCurrentUser(mappedUser);
        setIsAuthenticated(true);
        showToast(`Welcome, ${mappedUser.name}! Signed in via Google.`);
        return { success: true, user: mappedUser };
      }
      throw new Error("Unable to retrieve user profile from backend.");
    } catch (err) {
      clearTokens();
      setIsAuthenticated(false);
      return { success: false, message: err.message || "Failed to authenticate session." };
    }
  };

  const login = (email, password) => {
    if (email.includes("admin") || email.includes("ranganathan")) {
      const user = {
        id: "adm_01",
        name: "S. Ranganathan",
        title: "Director General (ASI)",
        email: email,
        role: "ADMINISTRATOR"
      };
      setCurrentUser(user);
      setIsAuthenticated(true);
      showToast("Signed in as Administrator.");
      return { success: true, user };
    } else {
      const user = {
        id: "exp_01",
        name: "Dr. A. Sharma",
        title: "Lead Conservator (ASI)",
        email: email,
        role: "CONSERVATION_EXPERT"
      };
      setCurrentUser(user);
      setIsAuthenticated(true);
      showToast("Signed in as Conservation Expert.");
      return { success: true, user };
    }
  };

  const registerUser = (userData) => {
    const newUser = {
      id: `usr_${Date.now()}`,
      name: userData.fullName,
      title: userData.designation || "Conservation Officer",
      email: userData.email,
      role: userData.role || "CONSERVATION_EXPERT"
    };
    setCurrentUser(newUser);
    setIsAuthenticated(true);
    showToast(`Account registered successfully for ${userData.fullName}.`);
    return { success: true, user: newUser };
  };

  const logout = async () => {
    try {
      await api.logout();
    } catch (e) {
      console.warn("Backend logout request notice:", e);
    } finally {
      clearTokens();
      setIsAuthenticated(false);
      setCurrentUser(null);
      showToast("Logged out successfully.");
    }
  };

  const updateUserProfile = (updatedData) => {
    setCurrentUser((prev) => ({
      ...prev,
      name: updatedData.name || prev.name,
      email: updatedData.email || prev.email,
      title: updatedData.title || prev.title
    }));
    showToast("USER PROFILE UPDATED SUCCESSFULLY.");
  };

  const resetUserPassword = (currentPassword, newPassword) => {
    if (!currentPassword) {
      showToast("Please enter your current password.", "error");
      return { success: false, message: "Please enter your current password." };
    }
    if (newPassword.length < 6) {
      showToast("New password must be at least 6 characters.", "error");
      return { success: false, message: "New password must be at least 6 characters." };
    }
    showToast("PASSWORD RESET SUCCESSFULLY.");
    return { success: true };
  };

  // Heritage Sites CRUD Handlers
  const addHeritageSite = (siteData) => {
    const newId = `site_${String(heritageSites.length + 1).padStart(2, "0")}`;
    const newCode = `HST-0${heritageSites.length + 1}`;
    const newSite = {
      id: newId,
      code: newCode,
      name: siteData.name,
      location: siteData.location,
      circle: siteData.circle || "ASI Directorate",
      material: siteData.material || "Granite & Freestone",
      category: siteData.category || "UNESCO World Heritage Site",
      description: siteData.description || "",
      image: siteData.image || "https://images.unsplash.com/photo-1582510003544-4d00b7f74220?auto=format&fit=crop&q=80&w=800",
      status: siteData.status || "MONITOR",
      regionsCount: 0,
      lastAssessment: new Date().toISOString().split("T")[0]
    };
    setHeritageSites([newSite, ...heritageSites]);
    showToast(`HERITAGE SITE "${siteData.name}" REGISTERED SUCCESSFULLY.`);
    return newSite;
  };

  const updateHeritageSite = (siteId, updatedData) => {
    setHeritageSites((prev) =>
      prev.map((site) => (site.id === siteId ? { ...site, ...updatedData } : site))
    );
    showToast("HERITAGE SITE UPDATED SUCCESSFULLY.");
  };

  const deleteHeritageSite = (siteId) => {
    const targetSite = heritageSites.find((s) => s.id === siteId);
    setHeritageSites((prev) => prev.filter((site) => site.id !== siteId));
    setArchitecturalRegions((prev) => prev.filter((reg) => reg.siteId !== siteId));
    showToast(`HERITAGE SITE "${targetSite?.name || ""}" DELETED SUCCESSFULLY.`);
  };

  // Architectural Regions CRUD Handlers
  const addArchitecturalRegion = (regionData) => {
    const newId = `reg_${String(architecturalRegions.length + 1).padStart(2, "0")}`;
    const newRegion = {
      id: newId,
      code: regionData.code || `REG-${String(architecturalRegions.length + 1).padStart(3, "0")}`,
      siteId: regionData.siteId,
      siteName: regionData.siteName,
      name: regionData.name,
      importance: regionData.importance || "Primary Load-Bearing Course",
      riskLevel: regionData.riskLevel || "MEDIUM",
      condition: regionData.riskLevel === "CRITICAL" ? "CRITICAL" : "MONITOR",
      lastAssessment: new Date().toISOString().split("T")[0]
    };
    setArchitecturalRegions([newRegion, ...architecturalRegions]);

    setHeritageSites((prev) =>
      prev.map((site) =>
        site.id === regionData.siteId
          ? { ...site, regionsCount: (site.regionsCount || 0) + 1 }
          : site
      )
    );

    showToast(`ARCHITECTURAL REGION "${regionData.name}" CREATED SUCCESSFULLY.`);
    return newRegion;
  };

  const updateArchitecturalRegion = (regionId, updatedData) => {
    setArchitecturalRegions((prev) =>
      prev.map((reg) => (reg.id === regionId ? { ...reg, ...updatedData } : reg))
    );
    showToast("ARCHITECTURAL REGION UPDATED SUCCESSFULLY.");
  };

  const deleteArchitecturalRegion = (regionId) => {
    const targetRegion = architecturalRegions.find((r) => r.id === regionId);
    setArchitecturalRegions((prev) => prev.filter((r) => r.id !== regionId));
    showToast(`ARCHITECTURAL REGION "${targetRegion?.name || ""}" DELETED SUCCESSFULLY.`);
  };

  // AI Pipeline Step Progression Handlers
  const advancePipelineStep = () => {
    if (pipelineStep < 9) {
      const nextStep = pipelineStep + 1;
      setPipelineStep(nextStep);
      if (nextStep === 9) {
        setIsPipelineComplete(true);
        showToast("All 9 AI Perception Pipeline steps completed. Results published!");
      }
    }
  };

  const completeAllPipelineSteps = () => {
    setPipelineStep(9);
    setIsPipelineComplete(true);
    showToast("AI Perception Pipeline analysis complete. Results published!");
  };

  const resetPipeline = () => {
    setPipelineStep(1);
    setIsPipelineComplete(false);
  };

  // Deduplicated Notification Creation Helper (Change 5)
  const addNotificationDeduplicated = (notifObj) => {
    setNotifications((prev) => {
      // Check if duplicate notification exists by eventKey or requestId or identical description
      const isDuplicate = prev.some(
        (n) =>
          (notifObj.eventKey && n.eventKey === notifObj.eventKey) ||
          (notifObj.requestId && n.requestId === notifObj.requestId) ||
          (n.title === notifObj.title && n.description === notifObj.description)
      );

      if (isDuplicate) {
        return prev;
      }
      return [notifObj, ...prev];
    });
  };

  // Heritage Site Request Workflow Handlers
  const submitSiteRequest = (requestData) => {
    const newReqId = `REQ-${Date.now()}`;
    const newReq = {
      id: newReqId,
      expertName: currentUser?.name || "Dr. A. Sharma",
      expertEmail: currentUser?.email || "a.sharma@asi.gov.in",
      siteName: requestData.name,
      location: requestData.location,
      circle: requestData.circle || "ASI Directorate",
      material: requestData.material || "Sandstone & Mortar",
      category: requestData.category || "State Protected Structural Site",
      description: requestData.description || "",
      image: requestData.image || "https://images.unsplash.com/photo-1582510003544-4d00b7f74220?auto=format&fit=crop&q=80&w=800",
      status: "PENDING ADMIN APPROVAL",
      createdAt: new Date().toLocaleString("en-US", { hour12: false })
    };

    setSiteRequests([newReq, ...siteRequests]);

    const adminNotif = {
      id: `notif_req_${newReqId}`,
      eventKey: `req_${newReqId}`,
      targetRole: "ADMINISTRATOR",
      title: "NEW HERITAGE SITE REQUEST",
      description: `Expert ${newReq.expertName} submitted request for monument "${newReq.siteName}" (${newReq.location}).`,
      time: "Just now",
      priority: "URGENT",
      read: false,
      link: "/admin/heritage-sites",
      requestId: newReqId
    };

    addNotificationDeduplicated(adminNotif);
    showToast(`Site Request for "${requestData.name}" submitted for Admin Approval.`);
    return newReq;
  };

  const acceptSiteRequest = (requestId) => {
    const targetReq = siteRequests.find((r) => r.id === requestId);
    setSiteRequests((prev) =>
      prev.map((req) => (req.id === requestId ? { ...req, status: "ACCEPTED" } : req))
    );

    if (targetReq) {
      const expertNotif = {
        id: `notif_acc_${requestId}`,
        eventKey: `acc_${requestId}`,
        targetEmail: targetReq.expertEmail,
        title: "HERITAGE SITE REQUEST ACCEPTED",
        description: `Your heritage site request for "${targetReq.siteName}" has been accepted by Administrator.`,
        time: "Just now",
        priority: "INFORMATION",
        read: false,
        link: "/dashboard"
      };
      addNotificationDeduplicated(expertNotif);
    }

    showToast("Heritage Site Request Accepted.");
  };

  const rejectSiteRequest = (requestId, reason) => {
    const targetReq = siteRequests.find((r) => r.id === requestId);
    setSiteRequests((prev) =>
      prev.map((req) =>
        req.id === requestId ? { ...req, status: "REJECTED", rejectionReason: reason } : req
      )
    );

    if (targetReq) {
      const expertNotif = {
        id: `notif_rej_${requestId}`,
        eventKey: `rej_${requestId}`,
        targetEmail: targetReq.expertEmail,
        title: "HERITAGE SITE REQUEST REJECTED",
        description: `Your site request for "${targetReq.siteName}" was rejected by Administrator. Reason: "${reason}".`,
        time: "Just now",
        priority: "CRITICAL",
        read: false,
        link: "/notifications"
      };
      addNotificationDeduplicated(expertNotif);
    }

    showToast(`Site Request Rejected. Reason: ${reason}`);
  };

  const approveAndCreateSiteFromRequest = (requestId, siteData) => {
    const createdSite = addHeritageSite(siteData);
    setSiteRequests((prev) =>
      prev.map((req) => (req.id === requestId ? { ...req, status: "APPROVED / SITE CREATED" } : req))
    );

    const targetReq = siteRequests.find((r) => r.id === requestId);
    if (targetReq) {
      const expertNotif = {
        id: `notif_app_${requestId}`,
        eventKey: `app_${requestId}`,
        targetEmail: targetReq.expertEmail,
        title: "HERITAGE SITE REQUEST APPROVED",
        description: `Administrator registered site "${createdSite.name}" from your request.`,
        time: "Just now",
        priority: "INFORMATION",
        read: false,
        link: "/dashboard"
      };
      addNotificationDeduplicated(expertNotif);
    }
  };

  // AI Assessment Handlers
  const recordAssessmentResult = (resultData) => {
    setActiveResult(resultData);
    setAssessments((prev) => {
      const exists = prev.some((a) => a.id === resultData.id);
      if (exists) return prev;
      return [resultData, ...prev];
    });

    if (resultData.severity === "High" || resultData.severity === "Critical" || resultData.emergencyLevel === "Critical") {
      const autoNotif = {
        id: `notif_auto_${resultData.id}`,
        eventKey: `crit_${resultData.id}`,
        title: "CRITICAL DAMAGE SEVERITY DETECTED",
        description: `[Region ID: ${resultData.regionCode || "REG-001"}] ${resultData.siteName} (${resultData.regionName}) structural damage crossed critical threshold. Finding: ${resultData.damageType}.`,
        time: "Just now",
        priority: "CRITICAL",
        read: false,
        link: "/expert/results"
      };
      addNotificationDeduplicated(autoNotif);
    }
  };

  const updateAssessmentStatus = (assessmentId, newStatus, expertNotes = "") => {
    setAssessments((prev) =>
      prev.map((item) =>
        item.id === assessmentId ? { ...item, status: newStatus, expertNotes } : item
      )
    );
    setActiveResult((prev) => (prev ? { ...prev, status: newStatus, expertNotes } : prev));
    showToast(`Assessment ${assessmentId} status updated to ${newStatus}.`);
  };

  const generateReportFromAssessment = (assessmentObj) => {
    const newReport = {
      id: `REP-2026-${String(reports.length + 1).padStart(3, "0")}`,
      assessmentId: assessmentObj.id,
      siteName: assessmentObj.siteName,
      regionName: assessmentObj.regionName,
      date: new Date().toISOString().split("T")[0],
      damageType: assessmentObj.damageType,
      severity: assessmentObj.severity,
      emergencyLevel: assessmentObj.emergencyLevel,
      confidence: typeof assessmentObj.confidence === "number" ? `${(assessmentObj.confidence * 100).toFixed(0)}%` : assessmentObj.confidence,
      expertName: currentUser?.name || "Dr. A. Sharma",
      summary: assessmentObj.recommendation || "Immediate conservation intervention recommended.",
      status: "Assessed & Verified"
    };

    setReports([newReport, ...reports]);
    return newReport;
  };

  const updateAiEngineStatus = (newStatus) => {
    setAiEngineStatus(newStatus);
    showToast("AI ASSESSMENT ENGINE STATUS UPDATED.");
  };

  const markNotificationAsRead = (notifId) => {
    setNotifications((prev) =>
      prev.map((n) => (n.id === notifId ? { ...n, read: true } : n))
    );
  };

  return (
    <AppContext.Provider
      value={{
        currentUser,
        isAuthenticated,
        isAuthLoading,
        loginWithGoogle,
        handleAuthCallback,
        login,
        registerUser,
        logout,
        updateUserProfile,
        resetUserPassword,

        heritageSites,
        addHeritageSite,
        updateHeritageSite,
        deleteHeritageSite,

        architecturalRegions,
        addArchitecturalRegion,
        updateArchitecturalRegion,
        deleteArchitecturalRegion,

        pipelineStep,
        isPipelineComplete,
        advancePipelineStep,
        completeAllPipelineSteps,
        resetPipeline,

        siteRequests,
        submitSiteRequest,
        acceptSiteRequest,
        rejectSiteRequest,
        approveAndCreateSiteFromRequest,

        assessments,
        recordAssessmentResult,
        updateAssessmentStatus,

        reports,
        generateReportFromAssessment,

        notifications,
        markNotificationAsRead,

        aiEngineStatus,
        updateAiEngineStatus,

        activeSiteId,
        setActiveSiteId,

        pendingAnalysis,
        setPendingAnalysis,

        activeResult,
        setActiveResult,

        toast,
        showToast
      }}
    >
      {children}
    </AppContext.Provider>
  );
}

export function useApp() {
  return useContext(AppContext);
}
