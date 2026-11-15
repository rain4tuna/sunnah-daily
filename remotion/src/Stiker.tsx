import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { theme } from "./theme";

// Stiker benda (Tabler Icons, MIT) yang ditempel di sudut ilustrasi. Dipilih di Python (stiker.py):
// hanya benda, tempat, dan alam; tidak ada makhluk bernyawa, wajah, atau simbol agama lain.
export type StikerData = { nama: string; svg: string; padat?: boolean; muncul: number };

type Sudut = "kiriAtas" | "kananAtas" | "kiriBawah" | "kananBawah";

const UKURAN = 176;
const KELUAR = 44; // seberapa jauh stiker menjorok keluar dari tepi ilustrasi
// Tiga gaya warna berganti-ganti supaya stiker berurutan tidak seragam.
const GAYA = [
  { bg: "#F4EBD8", ikon: "#1F6B5E" },
  { bg: theme.colors.hero, ikon: "#0C1A1D" },
  { bg: theme.colors.teal, ikon: "#F6F1E7" },
];

const Satu: React.FC<{ d: StikerData; sudut: Sudut; ke: number; delay: number }> = ({ d, sudut, ke, delay }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const mulai = Math.max(delay, Math.round(d.muncul * fps));
  const p = spring({ frame: frame - mulai, fps, config: theme.spring.bouncy });
  if (frame < mulai) return null;
  const gaya = GAYA[(ke + d.nama.length) % GAYA.length];
  const miring = ((d.nama.charCodeAt(0) + ke * 7) % 17) - 8;
  const apung = Math.sin((frame - mulai) / 22 + ke * 2) * 6;
  const atas = sudut.endsWith("Atas");
  const kiri = sudut.startsWith("kiri");
  return (
    <div style={{
      position: "absolute", width: UKURAN, height: UKURAN,
      [atas ? "top" : "bottom"]: -KELUAR, [kiri ? "left" : "right"]: -KELUAR,
      transform: `translateY(${apung}px) rotate(${interpolate(p, [0, 1], [miring - 30, miring])}deg) scale(${p})`,
      borderRadius: "50%", background: gaya.bg, border: "7px solid #F6F1E7",
      boxShadow: "0 18px 34px -10px rgba(0,0,0,0.65)", display: "flex", alignItems: "center", justifyContent: "center",
    }}>
      <svg width={UKURAN * 0.56} height={UKURAN * 0.56} viewBox="0 0 24 24" style={{ color: gaya.ikon }}
        fill={d.padat ? "currentColor" : "none"} stroke={d.padat ? "none" : "currentColor"} strokeWidth={1.8}
        strokeLinecap="round" strokeLinejoin="round">
        <g dangerouslySetInnerHTML={{ __html: d.svg }} />
      </svg>
    </div>
  );
};

/** Bungkus ilustrasi; stiker menempel di sudut yang tidak dipakai elemen lain (mis. nomor poin di kiri atas). */
export const DenganStiker: React.FC<{ stiker?: StikerData[]; sudut: Sudut[]; delay?: number; children: React.ReactNode }> = ({
  stiker, sudut, delay = 14, children,
}) => (
  <div style={{ position: "relative" }}>
    {children}
    {(stiker ?? []).slice(0, sudut.length).map((d, i) => (
      <Satu key={d.nama} d={d} sudut={sudut[i]} ke={i} delay={delay + i * 6} />
    ))}
  </div>
);
