// ANCESTRA Mock Heritage Data Repository

export const USERS = {
  expert: {
    id: "usr_exp_01",
    name: "Dr. A. Sharma",
    title: "Lead Conservator (ASI)",
    emailOrPhone: "a.sharma@asi.gov.in",
    role: "CONSERVATION_EXPERT",
    avatar: "https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&q=80&w=150"
  },
  admin: {
    id: "usr_adm_01",
    name: "S. Ranganathan",
    title: "Director General (ASI)",
    emailOrPhone: "s.ranganathan@ancestra.org",
    role: "ADMINISTRATOR",
    avatar: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&q=80&w=150"
  }
};

export const mockHeritageSites = [
  {
    id: "site_01",
    code: "HST-01",
    name: "Shore Temple, Mahabalipuram",
    location: "Mahabalipuram, Tamil Nadu",
    period: "Pallava Dynasty • 700–728 CE",
    category: "UNESCO World Heritage Site",
    material: "Granite & Dressed Freestone Blocks",
    circle: "ASI Chennai Circle",
    regionsCount: 4,
    lastAssessment: "2026-08-26",
    status: "CRITICAL",
    image: "https://images.unsplash.com/photo-1582510003544-4d00b7f74220?auto=format&fit=crop&q=80&w=800",
    description: "Three-shrine complex built from dressed blocks of coastal granitic freestone. Highly exposed to Bay of Bengal maritime weathering and salt efflorescence."
  },
  {
    id: "site_02",
    code: "HST-02",
    name: "Brihadisvara Temple, Thanjavur",
    location: "Thanjavur, Tamil Nadu",
    period: "Chola Dynasty • 1010 CE",
    category: "UNESCO World Heritage Site",
    material: "Interlocking Dry-Stone Granite",
    circle: "ASI Tiruchirappalli Circle",
    regionsCount: 6,
    lastAssessment: "2026-08-20",
    status: "MONITOR",
    image: "https://images.unsplash.com/photo-1600100397608-f090742f4949?auto=format&fit=crop&q=80&w=800",
    description: "Massive monolithic granite Dravidian vimana (66m tall) resting on a square adhisthana plinth. Notable for interlocking dry-stone masonry."
  },
  {
    id: "site_03",
    code: "HST-03",
    name: "Hampi Heritage Complex",
    location: "Hampi, Karnataka",
    period: "Vijayanagara Empire • 1513 CE",
    category: "UNESCO World Heritage Site",
    material: "Porphyritic Granite & Mortarless Lintels",
    circle: "ASI Hampi Circle",
    regionsCount: 5,
    lastAssessment: "2026-08-15",
    status: "MONITOR",
    image: "https://images.unsplash.com/photo-1627894099419-f5ebba5e3f42?auto=format&fit=crop&q=80&w=800",
    description: "Vast megalithic dry-stone architecture with massive granite lintels, sculpted musical pillars, monolithic shrines, and multi-tiered mandapas."
  },
  {
    id: "site_04",
    code: "HST-04",
    name: "Konark Sun Temple",
    location: "Konark, Odisha",
    period: "Eastern Ganga Dynasty • 1250 CE",
    category: "UNESCO World Heritage Site",
    material: "Khondalite & Chlorite Sandstone",
    circle: "ASI Bhubaneswar Circle",
    regionsCount: 8,
    lastAssessment: "2026-08-18",
    status: "CRITICAL",
    image: "https://images.unsplash.com/photo-1596402184320-417e7178b2cd?auto=format&fit=crop&q=80&w=800",
    description: "Colossal 24-wheeled stone chariot sanctuary constructed from ferruginous khondalite sandstone, subject to severe moisture micro-cracking and salt spalling."
  }
];

export const mockArchitecturalRegions = [
  {
    id: "reg_01",
    siteId: "site_01",
    siteName: "Shore Temple, Mahabalipuram",
    code: "REG-001",
    name: "East-Facing Rajasimhesvara Vimana",
    importance: "Primary Sanctum Superstructure",
    condition: "CRITICAL",
    riskLevel: "HIGH",
    lastAssessment: "2026-08-26",
    recentDamage: "Salt Efflorescence & Shear Crack",
    damageScore: 72
  },
  {
    id: "reg_02",
    siteId: "site_01",
    siteName: "Shore Temple, Mahabalipuram",
    code: "REG-002",
    name: "Southern Adhisthana Plinth",
    importance: "Load-Bearing Foundation",
    condition: "MONITOR",
    riskLevel: "MEDIUM",
    lastAssessment: "2026-08-22",
    recentDamage: "Surface Erosion",
    damageScore: 48
  },
  {
    id: "reg_03",
    siteId: "site_01",
    siteName: "Shore Temple, Mahabalipuram",
    code: "REG-003",
    name: "Western Small Shrine Mandapa",
    importance: "Secondary Enclosure",
    condition: "STABLE",
    riskLevel: "LOW",
    lastAssessment: "2026-07-30",
    recentDamage: "Minor Biological Crust",
    damageScore: 24
  },
  {
    id: "reg_04",
    siteId: "site_02",
    siteName: "Brihadisvara Temple, Thanjavur",
    code: "REG-004",
    name: "Main 13-Tiered Vimana Tower",
    importance: "Central Monument Spire",
    condition: "STABLE",
    riskLevel: "LOW",
    lastAssessment: "2026-08-20",
    recentDamage: "Sub-surface Lichen Growth",
    damageScore: 18
  },
  {
    id: "reg_05",
    siteId: "site_04",
    siteName: "Konark Sun Temple",
    code: "REG-005",
    name: "Jagamohana Pyramidal Roof Steps",
    importance: "Primary Assembly Hall Roof",
    condition: "CRITICAL",
    riskLevel: "HIGH",
    lastAssessment: "2026-08-18",
    recentDamage: "Deep Structural Fracture",
    damageScore: 86
  }
];

export const mockAssessments = [
  {
    id: "ASM-2026-089",
    siteId: "site_01",
    siteName: "Shore Temple, Mahabalipuram",
    regionId: "reg_01",
    regionCode: "REG-001",
    regionName: "East-Facing Rajasimhesvara Vimana",
    date: "2026-08-26",
    damageType: "Structural Crack",
    severity: "High",
    confidence: 0.94,
    damageTrend: "Increasing",
    emergencyLevel: "Critical",
    recommendation: "Immediate structural shoring & salt extraction desalting regimen required.",
    status: "Pending Review",
    imageUrl: "https://images.unsplash.com/photo-1582510003544-4d00b7f74220?auto=format&fit=crop&q=80&w=800",
    expertNotes: "Macro-crack extending 42cm along the eastern granite course.",
    historicalData: [
      { date: "Jan 2026", score: 28 },
      { date: "Mar 2026", score: 34 },
      { date: "May 2026", score: 52 },
      { date: "Jul 2026", score: 68 },
      { date: "Aug 2026", score: 86 }
    ]
  },
  {
    id: "ASM-2026-088",
    siteId: "site_04",
    siteName: "Konark Sun Temple",
    regionId: "reg_05",
    regionCode: "REG-005",
    regionName: "Jagamohana Pyramidal Roof Steps",
    date: "2026-08-18",
    damageType: "Erosion & Spalling",
    severity: "High",
    confidence: 0.91,
    damageTrend: "Increasing",
    emergencyLevel: "Urgent",
    recommendation: "Biocide application and silica micro-injection intervention.",
    status: "Confirmed",
    imageUrl: "https://images.unsplash.com/photo-1596402184320-417e7178b2cd?auto=format&fit=crop&q=80&w=800",
    expertNotes: "Khondalite sandstone degradation intensified by monsoon moisture.",
    historicalData: [
      { date: "Jan 2026", score: 40 },
      { date: "Mar 2026", score: 48 },
      { date: "May 2026", score: 60 },
      { date: "Jul 2026", score: 75 },
      { date: "Aug 2026", score: 82 }
    ]
  }
];

export const mockReports = [
  {
    id: "REP-2026-041",
    assessmentId: "ASM-2026-089",
    siteName: "Shore Temple, Mahabalipuram",
    regionName: "East-Facing Rajasimhesvara Vimana",
    regionCode: "REG-001",
    date: "2026-08-26",
    damageType: "Structural Crack",
    severity: "High",
    confidence: "94%",
    emergencyLevel: "Critical",
    status: "Generated",
    expertName: "Dr. A. Sharma",
    summary: "Immediate structural shoring & salt extraction desalting regimen required for East-Facing Rajasimhesvara Vimana."
  }
];

export const mockNotifications = [
  {
    id: "notif_01",
    title: "CRITICAL DAMAGE DETECTED",
    description: "East-Facing Rajasimhesvara Vimana [REG-001] recorded high-risk structural crack (94% AI confidence).",
    time: "10 mins ago",
    priority: "CRITICAL",
    read: false,
    link: "/expert/results"
  },
  {
    id: "notif_02",
    title: "EXPERT REVIEW REQUIRED",
    description: "Assessment ASM-2026-089 requires formal sign-off by Lead Conservator.",
    time: "45 mins ago",
    priority: "URGENT",
    read: false,
    link: "/expert/results"
  }
];
