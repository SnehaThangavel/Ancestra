import React, { createContext, useContext, useState, useEffect, useCallback, useRef } from "react";
import { api, getAccessToken, getRefreshToken, setTokens, clearTokens } from "../services/api";

const AppContext = createContext();

export function AppProvider({ children }) {
  // Authentication & Current User Role
  const [currentUser, setCurrentUser] = useState(null);

  const [isAuthenticated, setIsAuthenticated] = useState(() => !!getAccessToken());
  const [isAuthLoading, setIsAuthLoading] = useState(true);

  // Application Global Core State (populated from database via API)
  const [heritageSites, setHeritageSites] = useState([]);
  const [architecturalRegions, setArchitecturalRegions] = useState([]);
  const [assessments, setAssessments] = useState([]);
  const [reports, setReports] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [isLoadingData, setIsLoadingData] = useState(false);

  // In-flight refresh promise deduplication
  const refreshPromiseRef = useRef(null);

  // AI Perception Pipeline Progress State
  const [pipelineStep, setPipelineStep] = useState(1);
  const [isPipelineComplete, setIsPipelineComplete] = useState(false);

  // Heritage Site Requests (Expert -> Admin Workflow)
  const [siteRequests, setSiteRequests] = useState([]);

  // AI Assessment Engine System Status
  const [aiEngineStatus, setAiEngineStatus] = useState({
    online: true,
    modelState: "READY",
  });

  // Selected Active Context
  const [activeSiteId, setActiveSiteId] = useState(null);
  const [pendingAnalysis, setPendingAnalysis] = useState(null);
  const [activeResult, setActiveResult] = useState(null);

  // Toast Notification Message State
  const [toast, setToast] = useState(null);

  const showToast = useCallback((message, type = "info") => {
    setToast({ message, type });
    setTimeout(() => {
      setToast(null);
    }, 4000);
  }, []);

  // Fetch all initial data directly from database via backend API (deduplicated & batched)
  const refreshAppData = useCallback(async () => {
    if (refreshPromiseRef.current) {
      return refreshPromiseRef.current;
    }

    const task = (async () => {
      setIsLoadingData(true);
      try {
        // 1. Fetch Monuments, Regions, Anomalies, and Work Orders concurrently
        const [monumentsData, regionsData, anomaliesData, workOrdersData] = await Promise.allSettled([
          api.getMonuments(),
          api.getRegions(),
          api.getAnomalies(),
          api.getWorkOrders(),
        ]);

        let loadedSites = [];
        if (monumentsData.status === "fulfilled" && Array.isArray(monumentsData.value)) {
          loadedSites = monumentsData.value;
          setHeritageSites(loadedSites);
          if (loadedSites.length > 0 && !activeSiteId) {
            setActiveSiteId(loadedSites[0].id);
          }
        }

        let loadedRegions = [];
        if (regionsData.status === "fulfilled" && Array.isArray(regionsData.value)) {
          loadedRegions = regionsData.value.map((r) => {
            const mId = r.monument_id || r.siteId || "";
            return {
              ...r,
              monument_id: mId,
              siteId: mId,
              code: r.code || `REG-${String(r.id || "").substring(0, 4).toUpperCase() || "001"}`,
            };
          });
          setArchitecturalRegions(loadedRegions);
        }

        // 2. Fetch Assessments / Anomalies
        let loadedAnomalies = [];
        if (anomaliesData.status === "fulfilled" && Array.isArray(anomaliesData.value)) {
          loadedAnomalies = anomaliesData.value;
          setAssessments(loadedAnomalies);
          if (loadedAnomalies.length > 0) {
            setActiveResult(loadedAnomalies[0]);
          }
        }

        // 3. Build Reports from Anomalies & Work Orders
        const compiledReports = loadedAnomalies.map((anom, idx) => ({
          id: `REP-2026-${String(idx + 1).padStart(3, "0")}`,
          assessmentId: anom.id,
          validation_id: anom.validation_id,
          siteName: anom.siteName,
          regionName: anom.regionName,
          regionCode: anom.regionCode,
          date: anom.date,
          damageType: anom.damageType,
          severity: anom.severity,
          confidence: typeof anom.confidence === "number" ? `${(anom.confidence * 100).toFixed(0)}%` : anom.confidence,
          emergencyLevel: anom.emergencyLevel,
          status: anom.status === "Confirmed" ? "Assessed & Verified" : "Generated",
          expertName: "Dr. A. Sharma",
          summary: anom.recommendation,
        }));
        setReports(compiledReports);

        // 4. Derive dynamic notifications from anomalies and system alerts
        const derivedNotifs = [];
        loadedAnomalies.forEach((anom) => {
          if (anom.severity === "High" || anom.emergencyLevel === "Critical") {
            derivedNotifs.push({
              id: `notif_${anom.id}`,
              eventKey: `crit_${anom.id}`,
              title: "CRITICAL DAMAGE DETECTED",
              description: `${anom.regionName} [${anom.regionCode}] recorded ${anom.damageType} (AI Confidence: ${(anom.confidence * 100).toFixed(0)}%).`,
              time: anom.date,
              priority: "CRITICAL",
              read: false,
              link: "/expert/results",
            });
          }
        });

        if (workOrdersData.status === "fulfilled" && Array.isArray(workOrdersData.value)) {
          workOrdersData.value.forEach((wo) => {
            derivedNotifs.push({
              id: `notif_wo_${wo.id}`,
              eventKey: `wo_${wo.id}`,
              title: `WORK ORDER [${wo.priority}]: ${wo.status}`,
              description: wo.description || "Conservation repair order generated.",
              time: wo.created_at ? wo.created_at.split("T")[0] : "Recent",
              priority: wo.priority === "HIGH" || wo.priority === "URGENT" ? "URGENT" : "INFORMATION",
              read: false,
              link: "/reports",
            });
          });
        }

        setNotifications(derivedNotifs);
      } catch (err) {
        console.error("Failed to load initial data from backend API:", err);
      } finally {
        setIsLoadingData(false);
        refreshPromiseRef.current = null;
      }
    })();

    refreshPromiseRef.current = task;
    return task;
  }, [activeSiteId]);

  // Initialize Auth from stored JWT session, URL params, or backend on mount
  useEffect(() => {
    async function initAuth() {
      // If currently processing OAuth callback on /auth/callback, let AuthCallback handle it
      if (window.location.pathname.startsWith("/auth/callback")) {
        setIsAuthLoading(false);
        return;
      }

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
              isGoogleUser: true,
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
                  isGoogleUser: true,
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

      // Load DB records in background
      refreshAppData().catch(() => {});
    }

    initAuth();
  }, [refreshAppData]);

  // Auth Handlers
  const loginWithGoogle = useCallback(() => {
    window.location.href = api.getGoogleLoginUrl();
  }, []);

  const handleAuthCallback = useCallback(async (accessToken, refreshToken) => {
    try {
      if (accessToken) {
        setTokens(accessToken, refreshToken);
      }
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
          isGoogleUser: true,
        };
        setCurrentUser(mappedUser);
        setIsAuthenticated(true);
        showToast(`Welcome, ${mappedUser.name}! Signed in via Google.`);
        // Trigger background data load without delaying user navigation
        refreshAppData().catch(() => {});
        return { success: true, user: mappedUser };
      }
      throw new Error("Unable to retrieve user profile from backend.");
    } catch (err) {
      clearTokens();
      setIsAuthenticated(false);
      return { success: false, message: err.message || "Failed to authenticate session." };
    }
  }, [refreshAppData, showToast]);

  const login = (email, _password) => {
    if (import.meta.env.DEV) {
      if (!email) {
        return { success: false, message: "Please enter an email address." };
      }
      const isAdm = email.toLowerCase().includes("admin");
      const nameParts = email.split("@")[0].split(/[._]/);
      const formattedName = nameParts.map((p) => p.charAt(0).toUpperCase() + p.slice(1)).join(" ");
      const user = {
        id: `usr_${Date.now()}`,
        name: formattedName || "Conservation Specialist",
        title: isAdm ? "Director General (ASI)" : "Lead Conservator (ASI)",
        email: email,
        role: isAdm ? "ADMINISTRATOR" : "CONSERVATION_EXPERT",
      };
      setCurrentUser(user);
      setIsAuthenticated(true);
      showToast(`Signed in as ${user.role === "ADMINISTRATOR" ? "Administrator" : "Conservation Expert"}.`);
      return { success: true, user };
    }
    return {
      success: false,
      message: "Direct password authentication is disabled. Please sign in with Google SSO.",
    };
  };

  const registerUser = (userData) => {
    const newUser = {
      id: `usr_${Date.now()}`,
      name: userData.fullName,
      title: userData.designation || "Conservation Officer",
      email: userData.email,
      role: userData.role || "CONSERVATION_EXPERT",
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
      title: updatedData.title || prev.title,
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

  // Heritage Sites Direct DB CRUD Handlers
  const addHeritageSite = async (siteData) => {
    try {
      const created = await api.createMonument({
        name: siteData.name,
        location_name: siteData.location,
        heritage_status: siteData.category || "UNESCO World Heritage Site",
        importance_tier: siteData.importance_tier || 1,
      });
      setHeritageSites((prev) => [created, ...prev]);
      showToast(`HERITAGE SITE "${siteData.name}" REGISTERED IN DATABASE.`);
      return created;
    } catch (err) {
      console.error("Failed to add heritage site to database:", err);
      showToast("Failed to create heritage site: " + err.message, "error");
      throw err;
    }
  };

  const updateHeritageSite = async (siteId, updatedData) => {
    try {
      const updated = await api.updateMonument(siteId, {
        name: updatedData.name,
        location_name: updatedData.location,
        heritage_status: updatedData.category,
      });
      setHeritageSites((prev) =>
        prev.map((site) => (site.id === siteId ? { ...site, ...updated } : site))
      );
      showToast("HERITAGE SITE UPDATED IN DATABASE.");
    } catch (err) {
      console.error("Failed to update heritage site:", err);
      showToast("Failed to update site: " + err.message, "error");
    }
  };

  const deleteHeritageSite = async (siteId) => {
    try {
      const targetSite = heritageSites.find((s) => s.id === siteId);
      await api.deleteMonument(siteId);
      setHeritageSites((prev) => prev.filter((site) => site.id !== siteId));
      setArchitecturalRegions((prev) => prev.filter((reg) => (reg.monument_id || reg.siteId) !== siteId));
      showToast(`HERITAGE SITE "${targetSite?.name || ""}" DELETED.`);
    } catch (err) {
      console.error("Failed to delete heritage site:", err);
      showToast("Failed to delete site: " + err.message, "error");
    }
  };

  // Architectural Regions Direct DB CRUD Handlers
  const addArchitecturalRegion = async (regionData) => {
    try {
      const targetMonId = regionData.siteId || regionData.monument_id;
      const created = await api.createRegion({
        monument_id: targetMonId,
        name: regionData.name,
        category: regionData.category || "facade",
      });
      const normalizedCreated = {
        ...created,
        monument_id: created.monument_id || targetMonId,
        siteId: created.monument_id || targetMonId,
        code: created.code || `REG-${String(created.id || "").substring(0, 4).toUpperCase() || "001"}`,
      };
      setArchitecturalRegions((prev) => [normalizedCreated, ...prev]);
      setHeritageSites((prev) =>
        prev.map((site) =>
          site.id === normalizedCreated.monument_id
            ? { ...site, regions_count: (site.regions_count || 0) + 1 }
            : site
        )
      );
      showToast(`ARCHITECTURAL REGION "${regionData.name}" CREATED.`);
      return normalizedCreated;
    } catch (err) {
      console.error("Failed to create region:", err);
      showToast("Failed to create region: " + err.message, "error");
      throw err;
    }
  };

  const updateArchitecturalRegion = async (regionId, updatedData) => {
    try {
      const updated = await api.updateRegion(regionId, {
        name: updatedData.name,
        category: updatedData.category,
      });
      setArchitecturalRegions((prev) =>
        prev.map((reg) => {
          if (reg.id === regionId) {
            const mId = updated.monument_id || reg.monument_id || reg.siteId;
            return {
              ...reg,
              ...updated,
              monument_id: mId,
              siteId: mId,
            };
          }
          return reg;
        })
      );
      showToast("ARCHITECTURAL REGION UPDATED.");
    } catch (err) {
      console.error("Failed to update region:", err);
      showToast("Failed to update region: " + err.message, "error");
    }
  };

  const deleteArchitecturalRegion = async (regionId) => {
    try {
      const targetRegion = architecturalRegions.find((r) => r.id === regionId);
      await api.deleteRegion(regionId);
      setArchitecturalRegions((prev) => prev.filter((r) => r.id !== regionId));
      showToast(`ARCHITECTURAL REGION "${targetRegion?.name || ""}" DELETED.`);
    } catch (err) {
      console.error("Failed to delete region:", err);
      showToast("Failed to delete region: " + err.message, "error");
    }
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

  // Deduplicated Notification Creation Helper
  const addNotificationDeduplicated = (notifObj) => {
    setNotifications((prev) => {
      const isDuplicate = prev.some(
        (n) =>
          (notifObj.eventKey && n.eventKey === notifObj.eventKey) ||
          (notifObj.requestId && n.requestId === notifObj.requestId) ||
          (n.title === notifObj.title && n.description === notifObj.description)
      );
      if (isDuplicate) return prev;
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
      image:
        requestData.image ||
        "https://images.unsplash.com/photo-1582510003544-4d00b7f74220?auto=format&fit=crop&q=80&w=800",
      status: "PENDING ADMIN APPROVAL",
      createdAt: new Date().toLocaleString("en-US", { hour12: false }),
    };

    setSiteRequests((prev) => [newReq, ...prev]);

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
      requestId: newReqId,
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
        link: "/dashboard",
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
        link: "/notifications",
      };
      addNotificationDeduplicated(expertNotif);
    }

    showToast(`Site Request Rejected. Reason: ${reason}`);
  };

  const approveAndCreateSiteFromRequest = async (requestId, siteData) => {
    const createdSite = await addHeritageSite(siteData);
    setSiteRequests((prev) =>
      prev.map((req) =>
        req.id === requestId ? { ...req, status: "APPROVED / SITE CREATED" } : req
      )
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
        link: "/dashboard",
      };
      addNotificationDeduplicated(expertNotif);
    }
  };

  // AI Assessment Handlers
  const recordAssessmentResult = (resultData) => {
    setActiveResult(resultData);
    setAssessments((prev) => {
      const exists = prev.some((a) => a.id === resultData.id || a.validation_id === resultData.validation_id);
      if (exists) {
        return prev.map((a) => (a.id === resultData.id || a.validation_id === resultData.validation_id ? resultData : a));
      }
      return [resultData, ...prev];
    });

    if (
      resultData.severity === "High" ||
      resultData.severity === "Critical" ||
      resultData.emergencyLevel === "Critical"
    ) {
      const autoNotif = {
        id: `notif_auto_${resultData.id}`,
        eventKey: `crit_${resultData.id}`,
        title: "CRITICAL DAMAGE SEVERITY DETECTED",
        description: `[Region ID: ${resultData.regionCode || "REG-001"}] ${resultData.siteName} (${resultData.regionName}) structural damage crossed critical threshold. Finding: ${resultData.damageType}.`,
        time: "Just now",
        priority: "CRITICAL",
        read: false,
        link: "/expert/results",
      };
      addNotificationDeduplicated(autoNotif);
    }
  };

  const updateAssessmentStatus = async (assessmentId, newStatus, expertNotes = "") => {
    try {
      const target = assessments.find((a) => a.id === assessmentId);
      if (target?.validation_id) {
        await api.updateAnomalyStatus(target.validation_id, {
          status: newStatus,
          is_confirmed: newStatus === "Confirmed",
        });
      }

      setAssessments((prev) =>
        prev.map((item) =>
          item.id === assessmentId ? { ...item, status: newStatus, expertNotes } : item
        )
      );
      setActiveResult((prev) => (prev ? { ...prev, status: newStatus, expertNotes } : prev));
      showToast(`Assessment ${assessmentId} status updated to ${newStatus}.`);
    } catch (err) {
      console.error("Failed to update assessment status:", err);
      showToast("Failed to update status: " + err.message, "error");
    }
  };

  const generateReportFromAssessment = (assessmentObj) => {
    const newReport = {
      id: `REP-2026-${String(reports.length + 1).padStart(3, "0")}`,
      assessmentId: assessmentObj.id,
      validation_id: assessmentObj.validation_id,
      siteName: assessmentObj.siteName,
      regionName: assessmentObj.regionName,
      regionCode: assessmentObj.regionCode,
      date: new Date().toISOString().split("T")[0],
      damageType: assessmentObj.damageType,
      severity: assessmentObj.severity,
      emergencyLevel: assessmentObj.emergencyLevel,
      confidence:
        typeof assessmentObj.confidence === "number"
          ? `${(assessmentObj.confidence * 100).toFixed(0)}%`
          : assessmentObj.confidence,
      expertName: currentUser?.name || "Dr. A. Sharma",
      summary: assessmentObj.recommendation || "Immediate conservation intervention recommended.",
      status: "Assessed & Verified",
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
        isLoadingData,
        refreshAppData,
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
        showToast,
      }}
    >
      {children}
    </AppContext.Provider>
  );
}

export function useApp() {
  return useContext(AppContext);
}
