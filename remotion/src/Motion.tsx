import React from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { theme } from "./theme";

const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
const SAW = "ﷺ";

/** Masuk: pudar + naik + skala, satu pegas. */
export const Entrance: React.FC<{ delay?: number; y?: number; children: React.ReactNode; style?: React.CSSProperties }> = ({
  delay = 0, y = 44, children, style,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const p = spring({ frame: frame - delay, fps, config: theme.spring.smooth });
  return (
    <div style={{
      opacity: p,
      transform: `translateY(${interpolate(p, [0, 1], [y, 0])}px) scale(${interpolate(p, [0, 1], [0.95, 1])})`,
      ...style,
    }}>{children}</div>
  );
};

/** Pembungkus adegan: keluar lebih cepat daripada masuk. */
export const Scene: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const o = interpolate(frame, [durationInFrames - 11, durationInFrames - 1], [1, 0], { ...clamp, easing: theme.ease.in });
  const y = interpolate(frame, [durationInFrames - 11, durationInFrames - 1], [0, -46], { ...clamp, easing: theme.ease.in });
  return <AbsoluteFill style={{ opacity: o, transform: `translateY(${y}px)` }}>{children}</AbsoluteFill>;
};

/** Simbol shalawat hanya ada di Amiri; kata lain memakai font induknya. */
const Kata: React.FC<{ k: string }> = ({ k }) =>
  k.includes(SAW) ? (
    <>
      {k.split(SAW)[0]}
      <span style={{ fontFamily: theme.font.arab, fontSize: "1.25em", lineHeight: 0 }}>{SAW}</span>
      {k.split(SAW)[1]}
    </>
  ) : <>{k}</>;

/** Judul: kata muncul bergiliran; satu kata disorot warna utama. */
export const WordReveal: React.FC<{ text: string; delay?: number; per?: number; sorot?: number; style?: React.CSSProperties }> = ({
  text, delay = 0, per = 3, sorot = -1, style,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  return (
    <div style={{ display: "flex", flexWrap: "wrap", columnGap: "0.24em", ...style }}>
      {text.split(" ").map((w, i) => {
        const p = spring({ frame: frame - delay - i * per, fps, config: theme.spring.snappy });
        return (
          <span key={i} style={{
            display: "inline-block", opacity: p,
            color: i === sorot ? theme.colors.hero : undefined,
            transform: `translateY(${interpolate(p, [0, 1], [34, 0])}px) scale(${interpolate(p, [0, 1], [0.92, 1])})`,
          }}><Kata k={w} /></span>
        );
      })}
    </div>
  );
};

/** Teks narasi yang menyala mengikuti suara: dari frame `dari` sampai `sampai` (relatif adegan). */
export const Karaoke: React.FC<{ text: string; dari: number; sampai: number; style?: React.CSSProperties }> = ({
  text, dari, sampai, style,
}) => {
  const frame = useCurrentFrame();
  const kata = text.split(" ");
  // bobot per kata = jumlah huruf, supaya kata panjang mendapat waktu lebih lama
  const bobot = kata.map((k) => (k.includes(SAW) ? 26 : k.length) + 2);
  const total = bobot.reduce((a, b) => a + b, 0);
  let lari = 0;
  const mulai = bobot.map((b) => { const m = lari / total; lari += b; return m; });
  const pos = interpolate(frame, [dari, sampai], [0, 1], clamp);
  return (
    <div style={{ display: "flex", flexWrap: "wrap", columnGap: "0.27em", ...style }}>
      {kata.map((k, i) => {
        const akhir = i + 1 < kata.length ? mulai[i + 1] : 1;
        const aktif = pos >= mulai[i] && pos < akhir && frame >= dari && frame <= sampai;
        const sudah = pos >= akhir || (frame > sampai);
        const nyala = interpolate(pos, [mulai[i] - 0.012, mulai[i] + 0.012], [0, 1], { ...clamp, easing: theme.ease.out });
        return (
          <span key={i} style={{
            display: "inline-block",
            color: aktif ? theme.colors.hero : theme.colors.text,
            opacity: sudah || aktif ? 1 : interpolate(nyala, [0, 1], [0.3, 1]),
            transform: `translateY(${aktif ? -3 : 0}px)`,
          }}><Kata k={k} /></span>
        );
      })}
    </div>
  );
};

/** Garis yang tumbuh dari kiri. */
export const Garis: React.FC<{ delay?: number; lebar: number; style?: React.CSSProperties }> = ({ delay = 0, lebar, style }) => {
  const frame = useCurrentFrame();
  const w = interpolate(frame, [delay, delay + 26], [0, lebar], { ...clamp, easing: theme.ease.out });
  return <div style={{ height: 5, width: w, borderRadius: 5, background: theme.colors.hero, ...style }} />;
};

/** Bintang delapan (dua persegi bertumpuk) yang menggambar dirinya, lalu bernapas. */
export const Bintang: React.FC<{ ukuran: number; delay?: number; warna?: string; tebal?: number; putar?: number }> = ({
  ukuran, delay = 0, warna = theme.colors.hero, tebal = 6, putar = 0.12,
}) => {
  const frame = useCurrentFrame();
  const gambar = interpolate(frame, [delay, delay + 38], [0, 1], { ...clamp, easing: theme.ease.inOut });
  const sisi = 100 * 4;
  const rot = frame * putar;
  const napas = 1 + Math.sin(frame / 22) * 0.02;
  const kotak = (r: number) => (
    <rect x={-50} y={-50} width={100} height={100} rx={6} transform={`rotate(${r})`} fill="none"
      stroke={warna} strokeWidth={tebal} strokeDasharray={sisi} strokeDashoffset={sisi * (1 - gambar)} strokeLinejoin="round" />
  );
  return (
    <svg width={ukuran} height={ukuran} viewBox="-80 -80 160 160" style={{ transform: `rotate(${rot}deg) scale(${napas})` }}>
      {kotak(0)}
      {kotak(45)}
      <circle r={interpolate(gambar, [0.5, 1], [0, 13], clamp)} fill={warna} />
    </svg>
  );
};

export { clamp };
