/**
 * Converts snake_case or standard strings to Title Case (e.g., "structural_crack" -> "Structural Crack").
 * @param {string} str
 * @returns {string}
 */
export function toTitleCase(str) {
  if (!str || typeof str !== "string") return "";
  return str
    .replace(/_/g, " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());
}
