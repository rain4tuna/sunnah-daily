import { Easing } from "remotion";

// Satu sumber untuk warna, easing, dan pegas. Jangan menulis hex atau easing di komponen.
export const theme = {
  colors: {
    bg: "#0C1A1D",
    surface: "rgba(244,233,218,0.055)",
    line: "rgba(232,176,74,0.28)",
    hero: "#E8B04A",
    teal: "#2E8C85",
    text: "#F6F1E7",
    dim: "rgba(246,241,231,0.30)",
    soft: "rgba(246,241,231,0.62)",
  },
  font: {
    display: "Fraunces",
    body: "Poppins",
    arab: "Amiri",
  },
  ease: {
    out: Easing.bezier(0.16, 1, 0.3, 1),
    in: Easing.bezier(0.7, 0, 0.84, 0),
    inOut: Easing.bezier(0.65, 0, 0.35, 1),
  },
  spring: {
    smooth: { damping: 200, stiffness: 90, mass: 1 },
    snappy: { damping: 22, stiffness: 190, mass: 0.7 },
    bouncy: { damping: 11, stiffness: 140, mass: 0.9 },
  },
  safe: { top: 280, bottom: 1570, side: 84 },
} as const;
