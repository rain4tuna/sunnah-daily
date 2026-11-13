import React from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { theme } from "./theme";
import { clamp } from "./Motion";

/** Latar: dua cahaya kabur yang bergeser pelan + pola bintang samar. Tidak pernah polos. */
export const Latar: React.FC = () => {
  const frame = useCurrentFrame();
  const d1 = Math.sin(frame / 60) * 60, d2 = Math.cos(frame / 75) * 50;
  const geser = (frame * 0.35) % 180;
  return (
    <AbsoluteFill style={{ background: theme.colors.bg }}>
      <div style={{ position: "absolute", width: 1300, height: 1300, borderRadius: "50%", top: -520, left: -380 + d1,
        background: `radial-gradient(circle, ${theme.colors.teal}4d, ${theme.colors.teal}1f 38%, transparent 68%)` }} />
      <div style={{ position: "absolute", width: 1100, height: 1100, borderRadius: "50%", bottom: -420, right: -360 - d2,
        background: `radial-gradient(circle, ${theme.colors.hero}2b, ${theme.colors.hero}12 38%, transparent 68%)` }} />
      <svg width="100%" height="100%" style={{ position: "absolute", inset: 0, opacity: 0.07 }}>
        <defs>
          <pattern id="pola" width="180" height="180" patternUnits="userSpaceOnUse" patternTransform={`translate(${geser} ${-geser})`}>
            <g transform="translate(90 90)" fill="none" stroke={theme.colors.text} strokeWidth="2">
              <rect x="-42" y="-42" width="84" height="84" />
              <rect x="-42" y="-42" width="84" height="84" transform="rotate(45)" />
            </g>
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#pola)" />
      </svg>
    </AbsoluteFill>
  );
};

/** Label seri di kiri atas, handle akun di kanan atas, penanda babak di bawahnya. */
export const Kepala: React.FC<{ kicker: string; handle: string; batas: number[] }> = ({ kicker, handle, batas }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const p = spring({ frame: frame - 6, fps, config: theme.spring.smooth });
  return (
    <div style={{ position: "absolute", top: 150, left: theme.safe.side, right: theme.safe.side, opacity: p,
      transform: `translateY(${interpolate(p, [0, 1], [-24, 0])}px)` }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div style={{ fontFamily: theme.font.body, fontWeight: 600, fontSize: 28, letterSpacing: "0.16em", color: theme.colors.text,
          padding: "10px 24px", borderRadius: 999, border: `2px solid ${theme.colors.line}`, background: theme.colors.surface }}>
          {kicker}
        </div>
        <div style={{ fontFamily: theme.font.body, fontWeight: 600, fontSize: 32, color: theme.colors.soft }}>{handle}</div>
      </div>
      <div style={{ display: "flex", gap: 10, marginTop: 22 }}>
        {batas.map((mulai, i) => {
          const akhir = i + 1 < batas.length ? batas[i + 1] : durationInFrames;
          const isi = interpolate(frame, [mulai, akhir], [0, 1], clamp);
          return (
            <div key={i} style={{ flex: 1, height: 6, borderRadius: 6, background: "rgba(246,241,231,0.16)", overflow: "hidden" }}>
              <div style={{ width: `${isi * 100}%`, height: "100%", background: theme.colors.text, opacity: 0.85 }} />
            </div>
          );
        })}
      </div>
    </div>
  );
};

export const Grade: React.FC = () => (
  <AbsoluteFill style={{ pointerEvents: "none" }}>
    <AbsoluteFill style={{ backgroundColor: theme.colors.hero, mixBlendMode: "soft-light", opacity: 0.1 }} />
    <AbsoluteFill style={{ background: "linear-gradient(180deg, rgba(0,0,0,0.22), transparent 26%, transparent 70%, rgba(0,0,0,0.3))" }} />
  </AbsoluteFill>
);

export const Grain: React.FC = () => {
  const frame = useCurrentFrame();
  const noise = `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='220' height='220'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2'/%3E%3C/filter%3E%3Crect width='220' height='220' filter='url(%23n)' opacity='0.5'/%3E%3C/svg%3E")`;
  return <AbsoluteFill style={{ pointerEvents: "none", backgroundImage: noise, backgroundSize: "220px",
    backgroundPosition: `${(frame * 7) % 220}px ${(frame * 13) % 220}px`, opacity: 0.07, mixBlendMode: "overlay" }} />;
};

export const Vignette: React.FC = () => (
  <AbsoluteFill style={{ pointerEvents: "none", background: "radial-gradient(ellipse at center, transparent 55%, rgba(0,0,0,0.34) 100%)" }} />
);
