/**
 * Image Fallback Utility for Ancestra Heritage Sites & Architectural Regions
 * 
 * Uses authentic local high-resolution monument and region imagery stored in /monuments/
 * so that every heritage site and individual architectural region always displays
 * its authentic architectural image.
 */

export const DEFAULT_HERITAGE_IMAGE = "/monuments/brihadisvara_temple.jpg";

export const SITE_FALLBACK_IMAGES = {
  ajanta: "/monuments/ajanta_caves.jpg",
  brihadisvara: "/monuments/brihadisvara_temple.jpg",
  brihadeshvarar: "/monuments/brihadisvara_temple.jpg",
  thanjavur: "/monuments/brihadisvara_temple.jpg",
  hampi: "/monuments/hampi_complex.jpg",
  vittala: "/monuments/hampi_complex.jpg",
};

export const REGION_FALLBACK_IMAGES = {
  // Hampi Heritage Complex Regions
  "stone chariot": "/monuments/hampi_stone_chariot.jpg",
  "vittala": "/monuments/hampi_stone_chariot.jpg",
  "musical pillars": "/monuments/hampi_musical_pillars.jpg",
  "virupaksha": "/monuments/hampi_virupaksha_gopuram.jpg",
  "mahanavami": "/monuments/hampi_mahanavami_dibba.jpg",
  "dibba": "/monuments/hampi_mahanavami_dibba.jpg",
  "lotus mahal": "/monuments/hampi_lotus_mahal.jpg",

  // Brihadisvara Temple Regions
  "vimana": "/monuments/brihadisvara_vimana.jpg",
  "tower": "/monuments/brihadisvara_vimana.jpg",
  "nandi": "/monuments/brihadisvara_nandi_mandapa.jpg",
  "eastern gopuram": "/monuments/brihadisvara_gopuram.jpg",
  "inscriptions": "/monuments/brihadisvara_inscriptions.jpg",
  "adhisthana": "/monuments/brihadisvara_inscriptions.jpg",

  // Ajanta Rock-Cut Caves Regions
  "cave 19": "/monuments/ajanta_cave19_chaitya.jpg",
  "chaitya": "/monuments/ajanta_cave19_chaitya.jpg",
  "cave 26": "/monuments/ajanta_cave26_stupa.jpg",
  "stupa": "/monuments/ajanta_cave26_stupa.jpg",
  "cave 1": "/monuments/ajanta_cave1_verandah.jpg",
  "verandah": "/monuments/ajanta_cave1_verandah.jpg",
  "cave 2": "/monuments/ajanta_cave2_paintings.jpg",
  "ceiling": "/monuments/ajanta_cave2_paintings.jpg",
  "fresco": "/monuments/ajanta_cave2_paintings.jpg",
};

/**
 * Resolves the real authentic monument photo path for any site object.
 */
export function getMonumentImage(site) {
  if (!site) return DEFAULT_HERITAGE_IMAGE;

  const rawUrl = site.image || site.image_url;

  // If already pointing to a local /monuments/ file, use it directly
  if (rawUrl && typeof rawUrl === "string" && rawUrl.startsWith("/monuments/")) {
    return rawUrl;
  }

  // Name-based matching to local authentic monument image
  const nameLower = (site.name || site.location_name || "").toLowerCase();
  for (const [key, localPath] of Object.entries(SITE_FALLBACK_IMAGES)) {
    if (nameLower.includes(key)) {
      return localPath;
    }
  }

  if (rawUrl && typeof rawUrl === "string" && rawUrl.startsWith("http") && !rawUrl.includes("unsplash.com")) {
    return rawUrl;
  }

  return DEFAULT_HERITAGE_IMAGE;
}

/**
 * Resolves the authentic architectural image for a specific region within a monument.
 */
export function getRegionImage(region, site = null) {
  if (!region && !site) return DEFAULT_HERITAGE_IMAGE;

  const rawUrl = region?.image_url || region?.image;

  if (rawUrl && typeof rawUrl === "string" && rawUrl.startsWith("/monuments/")) {
    return rawUrl;
  }

  // Name-based matching for specific architectural region
  const regNameLower = (region?.name || "").toLowerCase();
  for (const [key, localPath] of Object.entries(REGION_FALLBACK_IMAGES)) {
    if (regNameLower.includes(key)) {
      return localPath;
    }
  }

  // Fallback to parent monument image
  if (site) {
    return getMonumentImage(site);
  }

  return DEFAULT_HERITAGE_IMAGE;
}

/**
 * Image onError handler to recover with the authentic local monument image.
 */
export function handleImageError(e, name = "") {
  e.currentTarget.onerror = null; // Prevent loop
  const nameLower = (name || "").toLowerCase();

  for (const [key, localPath] of Object.entries(REGION_FALLBACK_IMAGES)) {
    if (nameLower.includes(key)) {
      e.currentTarget.src = localPath;
      return;
    }
  }

  for (const [key, localPath] of Object.entries(SITE_FALLBACK_IMAGES)) {
    if (nameLower.includes(key)) {
      e.currentTarget.src = localPath;
      return;
    }
  }

  e.currentTarget.src = DEFAULT_HERITAGE_IMAGE;
}
