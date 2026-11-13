import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { theme } from "./theme";
import { clamp } from "./Motion";

// Ilustrasi digambar dengan SVG dan bergerak mengikuti frame.
// ATURAN GAMBAR: manusia/hewan boleh, tetapi TANPA wajah (tidak ada mata dan mulut).
// Nabi, sahabat, dan malaikat tidak digambar sama sekali (dijaga di prompt storyboard_ikon.py).
// Daftar JENIS dan POSE harus sama dengan ILUSTRASI / TOKOH di storyboard_ikon.py.

export const JENIS = ["badai", "kota_malam", "quran", "kafilah", "kabah", "masjid", "gua", "majelis", "lentera", "fajar",
  "air", "hidangan", "pintu", "sedekah", "hati"] as const;
export type JenisIlustrasi = (typeof JENIS)[number];
export const POSE = ["panik", "takut", "berdiri", "berdoa"] as const;
export type Pose = (typeof POSE)[number];

const L = 912;
const C = {
  malamAtas: "#0A1524", malamBawah: "#1B3442", senjaAtas: "#1A2440", senjaBawah: "#C8763E", fajarBawah: "#E3A552",
  tanah: "#16262B", tanahDepan: "#0F1B1F", pasir: "#B8743C", pasirGelap: "#7E4A28", pasirDepan: "#4A2B1B",
  awan: "#33414F", awanGelap: "#232E3A", awanTepi: "#55677A", kilat: "#FFE9A6",
  kulit: "#D7A77B", jubah: "#7C3030", jubahGelap: "#5A2020", sorban: "#EADFCB",
  bangunan: "#22383F", bangunanGelap: "#182A30", jendela: "#F2C063", kertas: "#F4EBD8", hijau: "#1F6B5E",
  batu: "#243238", batuGelap: "#172126", kayu: "#6B4A2B", emas: theme.colors.hero, putih: "#F6F1E7",
};
const JUBAH = ["#7C3030", "#2F5D62", "#6A5A33", "#4C3F6B"];

const acak = (i: number, s = 1) => { const x = Math.sin(i * 127.1 * s + 311.7) * 43758.5453; return x - Math.floor(x); };
type P = { frame: number; h: number; fps: number };
const pegas = (frame: number, fps: number, delay = 0, config: { damping: number; stiffness: number; mass: number } = theme.spring.smooth) =>
  spring({ frame: frame - delay, fps, config });

const Bintang2: React.FC<{ frame: number; h: number; n?: number }> = ({ frame, h, n = 26 }) => (
  <>{Array.from({ length: n }).map((_, i) => (
    <circle key={i} cx={acak(i) * L} cy={acak(i, 2) * h * 0.55} r={1.6 + acak(i, 3) * 2.2} fill="#FFF7E0"
      opacity={0.35 + 0.55 * Math.abs(Math.sin(frame / (14 + acak(i, 4) * 20) + i))} />
  ))}</>
);

const Sabit: React.FC<{ x: number; y: number; r?: number; langit?: string }> = ({ x, y, r = 56, langit = C.malamAtas }) => (
  <g transform={`translate(${x} ${y})`}>
    <circle r={r * 1.55} fill={C.emas} opacity={0.14} />
    <circle r={r} fill={C.emas} />
    <circle cx={r * 0.4} cy={-r * 0.2} r={r * 0.9} fill={langit} />
  </g>
);

const Tanah: React.FC<{ h: number; a?: string; b?: string }> = ({ h, a = C.tanah, b = C.tanahDepan }) => (
  <>
    <path d={`M 0 ${h - 96} Q 240 ${h - 150} 470 ${h - 104} T ${L} ${h - 120} L ${L} ${h} L 0 ${h} Z`} fill={a} />
    <path d={`M 0 ${h - 50} Q 300 ${h - 92} 620 ${h - 54} T ${L} ${h - 66} L ${L} ${h} L 0 ${h} Z`} fill={b} />
  </>
);

const Awan: React.FC<{ x: number; y: number; s?: number; gelap?: boolean }> = ({ x, y, s = 1, gelap }) => (
  <g transform={`translate(${x} ${y}) scale(${s})`}>
    <g fill={C.awanTepi} opacity={0.55} transform="translate(0 -7)">
      <circle cx={-110} cy={8} r={62} /><circle cx={-30} cy={-34} r={86} /><circle cx={70} cy={-14} r={74} /><circle cx={150} cy={18} r={54} />
    </g>
    <g fill={gelap ? C.awanGelap : C.awan}>
      <circle cx={-110} cy={8} r={62} /><circle cx={-30} cy={-34} r={86} /><circle cx={70} cy={-14} r={74} /><circle cx={150} cy={18} r={54} />
      <rect x={-150} y={10} width={330} height={62} rx={31} />
    </g>
  </g>
);

/** Kilat menyambar tiap `jeda` frame, lalu meredup dan berkedip sekali lagi. Hasil 0..1. */
const kilatan = (frame: number, jeda: number, geser = 0) => {
  const t = (frame + geser) % jeda;
  if (t < 6) return 1;
  if (t < 10) return (10 - t) / 5;
  if (t >= 12 && t < 16) return 0.7;
  return 0;
};

const Petir: React.FC<{ x: number; y: number; kuat: number; cermin?: boolean; tinggi?: number }> = ({ x, y, kuat, cermin, tinggi = 300 }) => {
  if (kuat <= 0) return null;
  const k = tinggi / 300;
  const titik = `0,0 -34,${96 * k} 6,${104 * k} -44,${210 * k} 2,${216 * k} -30,${300 * k}`;
  return (
    <g transform={`translate(${x} ${y}) scale(${cermin ? -1 : 1} 1)`} opacity={kuat} fill="none" strokeLinejoin="round" strokeLinecap="round">
      <polyline points={titik} stroke={C.kilat} strokeOpacity={0.22} strokeWidth={46} />
      <polyline points={titik} stroke={C.kilat} strokeOpacity={0.4} strokeWidth={22} />
      <polyline points={titik} stroke="#FFFDF2" strokeWidth={8} />
    </g>
  );
};

const Sinar: React.FC<{ frame: number; r1: number; r2: number; n?: number; op?: number; laju?: number }> = ({ frame, r1, r2, n = 14, op = 0.5, laju = 0.25 }) => (
  <g transform={`rotate(${frame * laju})`} opacity={op}>
    {Array.from({ length: n }).map((_, i) => (
      <path key={i} d={`M -16 ${-r1} L 0 ${-r2} L 16 ${-r1} Z`} fill={C.emas} opacity={i % 2 ? 0.35 : 0.6} transform={`rotate(${(360 / n) * i})`} />
    ))}
  </g>
);

const Percik: React.FC<{ frame: number; lebar: number; tinggi: number; n?: number; op?: number }> = ({ frame, lebar, tinggi, n = 12, op = 1 }) => (
  <>{Array.from({ length: n }).map((_, i) => {
    const t = ((frame + acak(i) * 90) % 90) / 90;
    return <circle key={i} cx={(acak(i, 2) - 0.5) * lebar} cy={-t * tinggi} r={4 + acak(i, 3) * 4} fill={C.kilat} opacity={(1 - t) * 0.9 * op} />;
  })}</>
);

/** Manusia tanpa wajah: kepala polos, sorban, jubah. Tidak ada mata dan mulut. */
export const Tokoh: React.FC<{ x: number; y: number; s?: number; pose: Pose; frame: number; warna?: string; duduk?: boolean }> = ({
  x, y, s = 1, pose, frame, warna = C.jubah, duduk,
}) => {
  const gelisah = pose === "panik" || pose === "takut";
  const getar = gelisah ? Math.sin(frame * 1.7) * 3.2 : 0;
  const condong = pose === "takut" ? 9 + Math.sin(frame / 9) * 1.5 : Math.sin(frame / 13 + x) * (gelisah ? 2 : 1.2);
  const naik = pose === "berdoa" ? Math.sin(frame / 16) * 4 : 0;
  const LENGAN: Record<Pose, [string, string, number[][]]> = {
    panik: ["M -46 -184 Q -118 -206 -58 -266", "M 46 -184 Q 118 -206 58 -266", [[-58, -266], [58, -266]]],
    takut: ["M -46 -184 Q -120 -196 -112 -262", "M 40 -184 Q -30 -214 -66 -282", [[-112, -262], [-66, -282]]],
    berdiri: ["M -48 -184 Q -80 -130 -66 -74", "M 48 -184 Q 80 -130 66 -74", [[-66, -74], [66, -74]]],
    berdoa: [`M -48 -184 Q -98 -150 -40 ${-150 + naik}`, `M 48 -184 Q 98 -150 40 ${-150 + naik}`, [[-40, -150 + naik], [40, -150 + naik]]],
  };
  const [l1, l2, tangan] = LENGAN[pose];
  const denyut = 0.6 + 0.4 * Math.abs(Math.sin(frame / 5));
  const gelap = "rgba(0,0,0,0.28)";
  const badan = duduk ? "M -96 0 Q -100 -70 -54 -192 Q 0 -222 54 -192 Q 100 -70 96 0 Z" : "M -78 0 L -54 -192 Q 0 -222 54 -192 L 78 0 Z";
  return (
    <g transform={`translate(${x + getar} ${y}) scale(${s}) rotate(${condong})`}>
      <ellipse cx={0} cy={4} rx={duduk ? 112 : 96} ry={14} fill="#000" opacity={0.28} />
      <g transform={duduk ? "translate(0 0) scale(1 0.62)" : undefined}>
        <path d={badan} fill={warna} />
        <path d="M 0 -208 L 14 0 L -14 0 Z" fill={gelap} />
      </g>
      <g transform={duduk ? "translate(0 73)" : undefined}>
        <path d="M -54 -192 Q 0 -160 54 -192 Q 0 -222 -54 -192 Z" fill={gelap} />
        <circle cx={0} cy={-246} r={42} fill={C.kulit} />
        <path d="M -50 -262 Q -44 -312 0 -314 Q 44 -312 50 -262 Q 0 -282 -50 -262 Z" fill={C.sorban} />
        <path d="M 36 -276 Q 70 -236 54 -176 L 38 -180 Q 50 -232 28 -262 Z" fill={C.sorban} opacity={0.92} />
        {!duduk ? [l1, l2].map((d, i) => <path key={i} d={d} fill="none" stroke={warna} strokeWidth={30} strokeLinecap="round" />) : null}
        {!duduk ? tangan.map(([cx, cy], i) => <circle key={i} cx={cx} cy={cy} r={15} fill={C.kulit} />) : null}
        {gelisah ? (
          <g stroke={C.emas} strokeWidth={7} strokeLinecap="round" opacity={denyut}>
            <line x1={-96} y1={-330} x2={-116} y2={-362} /><line x1={0} y1={-346} x2={0} y2={-384} /><line x1={96} y1={-330} x2={116} y2={-362} />
          </g>
        ) : null}
      </g>
    </g>
  );
};

/** Unta tanpa wajah (siluet): badan, punuk, leher, kepala polos, kaki melangkah. */
const Unta: React.FC<{ x: number; y: number; s?: number; frame: number; fase?: number }> = ({ x, y, s = 1, frame, fase = 0 }) => {
  const ayun = (k: number) => Math.sin(frame / 5 + fase + k) * 13;
  const angguk = Math.sin(frame / 5 + fase) * 3;
  return (
    <g transform={`translate(${x} ${y + angguk}) scale(${s})`} fill={C.pasirDepan}>
      {[[-46, 0], [-26, 1.6], [34, 3.1], [54, 4.7]].map(([kx, k], i) => (
        <rect key={i} x={kx - 6} y={-62} width={12} height={64} rx={6} transform={`rotate(${ayun(k)} ${kx} -62)`} />
      ))}
      <ellipse cx={4} cy={-84} rx={74} ry={32} />
      <path d="M -30 -104 Q 2 -160 36 -104 Z" />
      <path d="M 58 -92 Q 92 -120 90 -168 L 108 -170 Q 114 -110 74 -70 Z" />
      <ellipse cx={108} cy={-176} rx={26} ry={15} />
      <path d="M -66 -90 Q -92 -76 -88 -40 L -80 -40 Q -80 -70 -62 -80 Z" />
    </g>
  );
};

const Badai: React.FC<P> = ({ frame, h, fps }) => {
  const k1 = kilatan(frame, 38, 40), k2 = kilatan(frame, 53, 12);
  const kilau = Math.max(k1, k2);
  const yAwan = interpolate(pegas(frame, fps, 4), [0, 1], [-150, 0]);
  const guncang = kilau > 0 ? Math.sin(frame * 9) * 5 * kilau : 0;
  return (
    <g transform={`translate(${guncang} ${-guncang * 0.5})`}>
      <rect width={L} height={h} fill="#DCEBFF" opacity={kilau * 0.2} />
      <Tanah h={h} />
      <Petir x={300} y={170 + yAwan} kuat={k1} tinggi={h - 290} />
      <Petir x={170} y={150 + yAwan} kuat={k2} cermin tinggi={h - 300} />
      <g transform={`translate(${Math.sin(frame / 40) * 14} ${yAwan})`}>
        <Awan x={270} y={120} s={1.15} gelap /><Awan x={640} y={96} s={0.95} /><Awan x={90} y={70} s={0.7} />
      </g>
      <g stroke="#9FB6C6" strokeWidth={3} strokeLinecap="round" opacity={0.45}>
        {Array.from({ length: 34 }).map((_, i) => {
          const x = acak(i) * (L + 120) - 40;
          const y = ((acak(i, 2) * h + frame * (16 + acak(i, 3) * 9)) % (h + 60)) - 30;
          return <line key={i} x1={x} y1={y} x2={x - 9} y2={y + 30} />;
        })}
      </g>
      <rect width={L} height={h} fill="#FFFFFF" opacity={kilau * 0.1} />
    </g>
  );
};

const KotaMalam: React.FC<P> = ({ frame, h, fps }) => {
  const dasar = h - 96;
  const geser = interpolate(frame, [0, 400], [0, -34], clamp);
  const bulan = pegas(frame, fps, 6);
  const rumah = [[40, 150, 120], [176, 120, 170], [330, 170, 130], [680, 150, 150], [820, 130, 110]];
  return (
    <g>
      <Bintang2 frame={frame} h={h} />
      <g opacity={bulan} transform={`translate(0 ${interpolate(bulan, [0, 1], [70, 0])})`}><Sabit x={700} y={120} /></g>
      <g transform={`translate(${geser * 0.5} 0)`}>
        {rumah.map(([x, w, t], i) => {
          const p = pegas(frame, fps, 10 + i * 4);
          const y = dasar - t * p;
          return (
            <g key={i}>
              <rect x={x} y={y} width={w} height={t * p + 10} fill={i % 2 ? C.bangunanGelap : C.bangunan} />
              <rect x={x - 6} y={y - 8} width={w + 12} height={12} fill={C.bangunanGelap} />
              <rect x={x + w * 0.3} y={y + 34} width={26} height={38} rx={13} fill={C.jendela} opacity={p * (0.7 + 0.3 * Math.sin(frame / 7 + i * 2))} />
            </g>
          );
        })}
        <g transform={`translate(520 ${dasar})`}>
          <rect x={-70} y={-150} width={140} height={150} fill={C.bangunan} />
          <path d="M -58 -150 Q 0 -250 58 -150 Z" fill={C.bangunanGelap} />
          <rect x={84} y={-270} width={30} height={270} fill={C.bangunan} />
          <path d="M 80 -270 L 99 -312 L 118 -270 Z" fill={C.bangunanGelap} />
          <rect x={-16} y={-70} width={32} height={70} rx={16} fill={C.jendela} opacity={0.85 + 0.15 * Math.sin(frame / 9)} />
        </g>
      </g>
      <Kurma x={130 + geser} y={dasar + 30} frame={frame} /><Kurma x={870 + geser} y={dasar + 30} frame={frame + 40} />
      <Tanah h={h} />
    </g>
  );
};

const Kurma: React.FC<{ x: number; y: number; frame: number; s?: number; warna?: string }> = ({ x, y, frame, s = 1, warna = "#1E4A45" }) => (
  <g transform={`translate(${x} ${y}) scale(${s}) rotate(${Math.sin(frame / 26) * 2.4})`}>
    <path d="M -7 0 Q 6 -110 0 -210 L 12 -210 Q 20 -110 9 0 Z" fill={C.bangunanGelap} />
    {[-70, -35, 0, 35, 70].map((a) => <path key={a} d="M 6 -210 Q 60 -250 104 -206 Q 56 -226 6 -200 Z" fill={warna} transform={`rotate(${a - 20} 6 -210)`} />)}
  </g>
);

const Quran: React.FC<P> = ({ frame, h, fps }) => {
  const p = pegas(frame, fps, 4, theme.spring.bouncy);
  return (
    <g transform={`translate(${L / 2} ${h * 0.6})`}>
      <Sinar frame={frame} r1={150} r2={470} op={0.5 * p} />
      <circle r={190 * p} fill={C.emas} opacity={0.16} />
      <g transform="translate(0 -60)"><Percik frame={frame} lebar={420} tinggi={260} op={p} /></g>
      <g transform={`scale(${p}) translate(0 ${Math.sin(frame / 24) * 5})`}>
        <path d="M -150 118 L -40 -10 L -18 4 L -120 124 Z M 150 118 L 40 -10 L 18 4 L 120 124 Z" fill={C.kayu} />
        <path d="M -210 -34 Q -110 -78 0 -30 L 0 44 Q -110 -2 -210 40 Z M 210 -34 Q 110 -78 0 -30 L 0 44 Q 110 -2 210 40 Z" fill={C.hijau} />
        <path d="M -196 -46 Q -104 -86 0 -42 L 0 30 Q -104 -12 -196 26 Z" fill={C.kertas} />
        <path d="M 196 -46 Q 104 -86 0 -42 L 0 30 Q 104 -12 196 26 Z" fill="#EADFC6" />
        {[0, 1, 2].map((i) => (
          <g key={i} stroke="#B9A77F" strokeWidth={5} strokeLinecap="round" fill="none">
            <path d={`M -172 ${-34 + i * 18} Q -100 ${-66 + i * 18} -22 ${-30 + i * 18}`} />
            <path d={`M 172 ${-34 + i * 18} Q 100 ${-66 + i * 18} 22 ${-30 + i * 18}`} />
          </g>
        ))}
      </g>
    </g>
  );
};

const Kafilah: React.FC<P> = ({ frame, h, fps }) => {
  const p = pegas(frame, fps, 4);
  const jalan = -180 + frame * 1.3;
  return (
    <g>
      <circle cx={690} cy={interpolate(p, [0, 1], [h, h - 250])} r={96} fill={C.emas} opacity={0.95} />
      <circle cx={690} cy={interpolate(p, [0, 1], [h, h - 250])} r={150} fill={C.emas} opacity={0.14} />
      <path d={`M 0 ${h - 170} Q 220 ${h - 250} 470 ${h - 180} T ${L} ${h - 210} L ${L} ${h} L 0 ${h} Z`} fill={C.pasir} />
      <path d={`M 0 ${h - 110} Q 300 ${h - 180} 600 ${h - 110} T ${L} ${h - 140} L ${L} ${h} L 0 ${h} Z`} fill={C.pasirGelap} />
      <g>
        {[0, 1, 2].map((i) => <Unta key={i} x={jalan + i * 210} y={h - 96} s={0.86} frame={frame} fase={i * 1.4} />)}
        {[0, 1].map((i) => <line key={i} x1={jalan + i * 210 + 66} y1={h - 190} x2={jalan + i * 210 + 150} y2={h - 176} stroke={C.pasirDepan} strokeWidth={3} />)}
      </g>
      <path d={`M 0 ${h - 56} Q 260 ${h - 100} 560 ${h - 60} T ${L} ${h - 74} L ${L} ${h} L 0 ${h} Z`} fill={C.pasirDepan} />
    </g>
  );
};

const Kabah: React.FC<P> = ({ frame, h, fps }) => {
  const p = pegas(frame, fps, 4, theme.spring.bouncy);
  const cy = h - 110;
  const orang = Array.from({ length: 16 }).map((_, i) => {
    const a = (i / 16) * Math.PI * 2 + frame / 70;
    return { x: L / 2 + Math.cos(a) * 330, y: cy + Math.sin(a) * 58, depan: Math.sin(a) > 0, i };
  });
  const Jamaah = ({ o }: { o: (typeof orang)[number] }) => (
    <g transform={`translate(${o.x} ${o.y}) scale(${0.8 + (o.y - cy + 58) / 400})`}>
      <path d="M -13 0 L -9 -34 Q 0 -40 9 -34 L 13 0 Z" fill={C.putih} /><circle cy={-44} r={9} fill={C.kulit} />
    </g>
  );
  return (
    <g>
      <Bintang2 frame={frame} h={h} n={18} />
      <ellipse cx={L / 2} cy={cy} rx={420} ry={84} fill="#22343A" /><ellipse cx={L / 2} cy={cy} rx={300} ry={56} fill="#2B4148" />
      {orang.filter((o) => !o.depan).map((o) => <Jamaah key={o.i} o={o} />)}
      <g transform={`translate(${L / 2} ${cy}) scale(${p})`}>
        <circle cy={-150} r={230} fill={C.emas} opacity={0.08 + 0.04 * Math.sin(frame / 18)} />
        <path d="M -120 0 L -120 -250 L 20 -276 L 20 -18 Z" fill="#14181B" /><path d="M 20 -18 L 20 -276 L 130 -244 L 130 0 Z" fill="#0C0F11" />
        <path d="M -120 -190 L 20 -214 L 20 -184 L -120 -160 Z M 20 -214 L 130 -184 L 130 -154 L 20 -184 Z" fill={C.emas} />
        <path d="M -70 -6 L -70 -104 L -24 -110 L -24 -12 Z" fill={C.emas} opacity={0.9} />
      </g>
      {orang.filter((o) => o.depan).map((o) => <Jamaah key={o.i} o={o} />)}
    </g>
  );
};

const Masjid: React.FC<P> = ({ frame, h, fps }) => {
  const dasar = h - 80;
  const p = pegas(frame, fps, 6);
  const naik = (d: number) => pegas(frame, fps, d);
  const Menara = ({ x, d }: { x: number; d: number }) => (
    <g transform={`translate(${x} ${dasar}) scale(1 ${naik(d)})`}>
      <rect x={-22} y={-330} width={44} height={330} fill={C.bangunan} /><rect x={-32} y={-250} width={64} height={16} fill={C.bangunanGelap} />
      <path d="M -26 -330 Q 0 -400 26 -330 Z" fill={C.hijau} /><circle cy={-398} r={7} fill={C.emas} />
      <rect x={-7} y={-300} width={14} height={30} rx={7} fill={C.jendela} opacity={0.9} />
    </g>
  );
  return (
    <g>
      <Bintang2 frame={frame} h={h} n={16} />
      <g opacity={p}><Sabit x={150} y={110} r={44} /></g>
      <g transform={`translate(${Math.sin(frame / 50) * 20} 0)`} opacity={0.55}><Awan x={700} y={130} s={0.5} /></g>
      <Menara x={210} d={10} /><Menara x={702} d={14} />
      <g transform={`translate(${L / 2} ${dasar}) scale(${naik(4)})`}>
        <rect x={-210} y={-170} width={420} height={170} fill={C.bangunan} />
        <path d="M -150 -170 Q 0 -400 150 -170 Z" fill={C.hijau} /><path d="M -150 -170 Q -60 -330 0 -372 Q -100 -300 -118 -170 Z" fill="#2A8474" opacity={0.6} />
        <rect x={-4} y={-410} width={8} height={40} fill={C.emas} /><circle cy={-416} r={10} fill={C.emas} />
        {[-140, -70, 70, 140].map((x, i) => <rect key={x} x={x - 20} y={-120} width={40} height={74} rx={20} fill={C.jendela} opacity={0.75 + 0.25 * Math.sin(frame / 8 + i)} />)}
        <path d="M -34 0 L -34 -96 Q 0 -140 34 -96 L 34 0 Z" fill={C.bangunanGelap} /><path d="M -22 0 L -22 -90 Q 0 -120 22 -90 L 22 0 Z" fill={C.jendela} opacity={0.9} />
      </g>
      <Kurma x={70} y={dasar + 10} frame={frame} s={0.8} /><Kurma x={850} y={dasar + 10} frame={frame + 30} s={0.8} />
      <path d={`M 0 ${dasar - 6} L ${L} ${dasar - 6} L ${L} ${h} L 0 ${h} Z`} fill={C.tanahDepan} />
    </g>
  );
};

const Gua: React.FC<P> = ({ frame, h, fps }) => {
  const p = pegas(frame, fps, 8);
  const nyala = 0.75 + 0.25 * Math.sin(frame / 10);
  return (
    <g>
      <Bintang2 frame={frame} h={h} />
      <g opacity={p}><Sabit x={130} y={100} r={38} /></g>
      <path d={`M -40 ${h} L 190 ${h - 300} L 330 ${h - 210} L 520 ${h - 430} L 720 ${h - 240} L 830 ${h - 320} L ${L + 40} ${h} Z`} fill={C.batu} />
      <path d={`M 520 ${h - 430} L 600 ${h - 250} L 470 ${h - 300} Z M 190 ${h - 300} L 250 ${h - 180} L 150 ${h - 200} Z`} fill="#31444B" />
      <g transform={`translate(520 ${h - 150})`}>
        <ellipse cy={10} rx={230 * p} ry={150 * p} fill={C.emas} opacity={0.14 * nyala} />
        <path d="M -92 60 Q -100 -90 0 -104 Q 100 -90 92 60 Z" fill={C.batuGelap} />
        <path d="M -66 60 Q -72 -64 0 -76 Q 72 -64 66 60 Z" fill={C.emas} opacity={0.85 * nyala * p} />
        <path d="M -40 60 Q -44 -36 0 -46 Q 44 -36 40 60 Z" fill="#FFF3CF" opacity={0.9 * nyala * p} />
        <g transform="translate(0 30)"><Percik frame={frame} lebar={150} tinggi={190} n={8} op={p} /></g>
      </g>
      <path d={`M 0 ${h - 40} Q 300 ${h - 96} 520 ${h - 84} T ${L} ${h - 50} L ${L} ${h} L 0 ${h} Z`} fill={C.batuGelap} />
    </g>
  );
};

const Majelis: React.FC<P> = ({ frame, h, fps }) => {
  const dasar = h - 70;
  const api = 0.8 + 0.2 * Math.sin(frame / 4);
  const kursi = [[150, 0.82, 16], [330, 0.94, 6], [582, 0.94, 10], [762, 0.82, 20]];
  return (
    <g>
      <Bintang2 frame={frame} h={h} n={18} />
      <rect x={0} y={dasar - 300} width={L} height={300} fill={C.bangunanGelap} opacity={0.55} />
      {[110, 456, 802].map((x) => <path key={x} d={`M ${x - 70} ${dasar - 300} L ${x - 70} ${dasar - 380} Q ${x} ${dasar - 470} ${x + 70} ${dasar - 380} L ${x + 70} ${dasar - 300} Z`} fill={C.malamBawah} opacity={0.9} />)}
      <ellipse cx={L / 2} cy={dasar + 6} rx={430} ry={46} fill="#3A2A22" /><ellipse cx={L / 2} cy={dasar + 6} rx={330} ry={32} fill="#4A3529" />
      <ellipse cx={L / 2} cy={dasar - 60} rx={300} ry={200} fill={C.emas} opacity={0.12 * api} />
      {kursi.map(([x, s, d], i) => (
        <g key={i} opacity={pegas(frame, fps, d)}><Tokoh x={x} y={dasar - 6} s={s} pose="berdiri" frame={frame + i * 17} warna={JUBAH[i % 4]} duduk /></g>
      ))}
      <g transform={`translate(${L / 2} ${dasar - 4})`}>
        <path d="M -26 0 L -18 -30 L 18 -30 L 26 0 Z" fill={C.kayu} />
        <path d={`M -16 -30 Q -24 -70 0 ${-104 * api} Q 24 -70 16 -30 Z`} fill={C.emas} /><path d={`M -8 -30 Q -12 -56 0 ${-74 * api} Q 12 -56 8 -30 Z`} fill="#FFF3CF" />
      </g>
    </g>
  );
};

const Lentera: React.FC<P> = ({ frame, h, fps }) => {
  const p = pegas(frame, fps, 4, theme.spring.bouncy);
  const nyala = 0.8 + 0.2 * Math.sin(frame / 6);
  return (
    <g>
      <Bintang2 frame={frame} h={h} />
      <g opacity={p}><Sabit x={740} y={120} r={40} /></g>
      <g transform={`translate(${L / 2} 0) rotate(${Math.sin(frame / 28) * 4})`}>
        <line x1={0} y1={-10} x2={0} y2={h * 0.2} stroke={C.emas} strokeWidth={5} />
        <g transform={`translate(0 ${h * 0.2}) scale(${p})`}>
          <circle cy={130} r={230} fill={C.emas} opacity={0.14 * nyala} /><circle cy={130} r={130} fill={C.emas} opacity={0.16 * nyala} />
          <path d="M -34 0 Q 0 -44 34 0 Z" fill={C.emas} /><rect x={-58} y={0} width={116} height={22} rx={8} fill={C.emas} />
          <path d="M -58 22 L -78 210 L 78 210 L 58 22 Z" fill="#1A2C31" stroke={C.emas} strokeWidth={8} strokeLinejoin="round" />
          <path d="M -40 40 L -54 194 L 54 194 L 40 40 Z" fill="#FFE2A0" opacity={0.9 * nyala} />
          <line x1={0} y1={26} x2={0} y2={206} stroke={C.emas} strokeWidth={6} /><line x1={-66} y1={118} x2={66} y2={118} stroke={C.emas} strokeWidth={6} />
          <rect x={-86} y={210} width={172} height={24} rx={8} fill={C.emas} /><path d="M -30 234 L 0 268 L 30 234 Z" fill={C.emas} />
        </g>
      </g>
      <Tanah h={h} />
    </g>
  );
};

const Fajar: React.FC<P> = ({ frame, h, fps }) => {
  const p = pegas(frame, fps, 4);
  const y = interpolate(p, [0, 1], [h - 60, h - 200]);
  return (
    <g>
      <g transform={`translate(${L / 2} ${y})`}>
        <Sinar frame={frame} r1={130} r2={620} n={16} op={0.42 * p} laju={0.18} />
        <circle r={190} fill={C.emas} opacity={0.2} /><circle r={112} fill="#FFD98A" />
      </g>
      {[0, 1, 2].map((i) => {
        const x = ((frame * (1.1 + i * 0.3) + i * 260) % (L + 120)) - 60, yb = 110 + i * 46 + Math.sin(frame / 14 + i) * 10, k = Math.sin(frame / 4 + i) * 9;
        return <path key={i} d={`M ${x - 22} ${yb + k} Q ${x - 10} ${yb - 12} ${x} ${yb} Q ${x + 10} ${yb - 12} ${x + 22} ${yb + k}`} fill="none" stroke="#1A2440" strokeWidth={5} strokeLinecap="round" />;
      })}
      <path d={`M 0 ${h - 130} Q 200 ${h - 230} 430 ${h - 150} T ${L} ${h - 190} L ${L} ${h} L 0 ${h} Z`} fill="#3B3A4A" />
      <path d={`M 0 ${h - 80} Q 280 ${h - 150} 600 ${h - 86} T ${L} ${h - 110} L ${L} ${h} L 0 ${h} Z`} fill="#25273A" />
      <Kurma x={120} y={h - 60} frame={frame} s={0.9} warna="#1A2440" />
    </g>
  );
};

const Air: React.FC<P> = ({ frame, h, fps }) => {
  const p = pegas(frame, fps, 4);
  const muka = h - 130;
  const siklus = 46, t = frame % siklus;
  const yTetes = interpolate(t, [0, 22], [150, muka - 10], { ...clamp, easing: theme.ease.in });
  return (
    <g>
      <Bintang2 frame={frame} h={h} n={14} />
      <g transform={`translate(${L / 2 - 30} 150) rotate(${interpolate(p, [0, 1], [0, 24])})`}>
        <path d="M -150 -40 Q -210 -10 -150 40 Q -60 70 20 30 L 60 14 L 64 -6 L 18 -20 Q -60 -74 -150 -40 Z" fill="#8A5A3A" />
        <path d="M -150 -40 Q -110 -66 -50 -52 Q -110 -44 -140 -8 Z" fill="#A9724C" opacity={0.8} />
      </g>
      <path d={`M ${L / 2 + 28} 150 Q ${L / 2 + 34} ${(150 + muka) / 2} ${L / 2 + 30} ${muka}`} stroke="#9FD6E8" strokeWidth={10 * p} fill="none" strokeLinecap="round" opacity={0.55} />
      {t < 22 ? <path d={`M ${L / 2 + 30} ${yTetes - 22} Q ${L / 2 + 46} ${yTetes + 4} ${L / 2 + 30} ${yTetes + 12} Q ${L / 2 + 14} ${yTetes + 4} ${L / 2 + 30} ${yTetes - 22} Z`} fill="#BFE9F5" /> : null}
      <path d={`M 0 ${muka} L ${L} ${muka} L ${L} ${h} L 0 ${h} Z`} fill="#17414B" />
      <path d={`M 0 ${muka} L ${L} ${muka} L ${L} ${muka + 26} L 0 ${muka + 26} Z`} fill="#2A6B78" opacity={0.7} />
      {[0, 1, 2].map((i) => {
        const tr = ((frame + i * 15) % siklus) / siklus;
        return <ellipse key={i} cx={L / 2 + 30} cy={muka + 30} rx={30 + tr * 300} ry={8 + tr * 46} fill="none" stroke="#BFE9F5" strokeWidth={5} opacity={(1 - tr) * 0.8} />;
      })}
    </g>
  );
};

const Hidangan: React.FC<P> = ({ frame, h, fps }) => {
  const dasar = h - 90;
  const p = (d: number) => pegas(frame, fps, d, theme.spring.bouncy);
  return (
    <g>
      <Bintang2 frame={frame} h={h} n={12} />
      <ellipse cx={L / 2} cy={dasar - 110} rx={380} ry={230} fill={C.emas} opacity={0.08 + 0.03 * Math.sin(frame / 12)} />
      <path d={`M 60 ${dasar} L 852 ${dasar} L 800 ${h} L 112 ${h} Z`} fill="#6E2F2B" /><path d={`M 60 ${dasar} L 852 ${dasar} L 842 ${dasar + 16} L 70 ${dasar + 16} Z`} fill={C.emas} opacity={0.8} />
      <g transform={`translate(${L / 2 - 90} ${dasar}) scale(${p(4)})`}>
        <ellipse cy={-6} rx={190} ry={30} fill={C.sorban} /><ellipse cy={-12} rx={150} ry={20} fill="#D8CBB3" />
        {[[-80, -22], [-36, -28], [10, -24], [56, -28], [-56, -46], [-10, -50], [34, -46], [-30, -68], [12, -70]].map(([x, y], i) => (
          <ellipse key={i} cx={x} cy={y} rx={26} ry={15} fill={i % 2 ? "#5B2E1E" : "#74391F"} transform={`rotate(${(i % 3) * 14 - 14} ${x} ${y})`} />
        ))}
      </g>
      <g transform={`translate(${L / 2 + 210} ${dasar}) scale(${p(12)})`}>
        <path d="M -44 0 L -54 -110 L 54 -110 L 44 0 Z" fill="#B9D7DF" opacity={0.35} /><path d="M -46 -8 L -52 -84 L 52 -84 L 46 -8 Z" fill="#8FD0E2" opacity={0.7} />
        <path d="M -54 -110 L 54 -110" stroke={C.putih} strokeWidth={5} />
      </g>
      <g transform={`translate(${L / 2 - 300} ${dasar}) scale(${p(18)})`}>
        <ellipse cy={-26} rx={70} ry={40} fill="#C98A4B" /><path d="M -50 -38 Q -20 -54 10 -40 M -10 -24 Q 20 -40 48 -26" stroke="#9A6230" strokeWidth={5} fill="none" strokeLinecap="round" />
      </g>
      {[0, 1].map((i) => {
        const t = ((frame + i * 34) % 68) / 68, x = L / 2 - 120 + i * 60;
        return <path key={i} d={`M ${x} ${dasar - 96 - t * 110} q 18 -22 0 -44 q -18 -22 0 -44`} stroke={C.putih} strokeWidth={5} fill="none" strokeLinecap="round" opacity={(1 - t) * 0.5} />;
      })}
    </g>
  );
};

const Pintu: React.FC<P> = ({ frame, h, fps }) => {
  const dasar = h - 70;
  const buka = pegas(frame, fps, 12);
  const nyala = 0.85 + 0.15 * Math.sin(frame / 9);
  return (
    <g>
      <Bintang2 frame={frame} h={h} n={12} />
      <rect x={150} y={dasar - 400} width={612} height={400} fill={C.bangunan} /><rect x={132} y={dasar - 416} width={648} height={24} fill={C.bangunanGelap} />
      {[230, 682].map((x, i) => <rect key={x} x={x - 26} y={dasar - 300} width={52} height={86} rx={26} fill={C.jendela} opacity={0.6 + 0.2 * Math.sin(frame / 8 + i)} />)}
      <path d={`M ${L / 2 - 90} ${dasar} L ${L / 2 - 250 * buka - 90} ${h + 40} L ${L / 2 + 250 * buka + 90} ${h + 40} L ${L / 2 + 90} ${dasar} Z`} fill={C.emas} opacity={0.28 * buka * nyala} />
      <path d={`M ${L / 2 - 96} ${dasar} L ${L / 2 - 96} ${dasar - 250} Q ${L / 2} ${dasar - 350} ${L / 2 + 96} ${dasar - 250} L ${L / 2 + 96} ${dasar} Z`} fill={C.bangunanGelap} />
      <path d={`M ${L / 2 - 80} ${dasar} L ${L / 2 - 80} ${dasar - 244} Q ${L / 2} ${dasar - 326} ${L / 2 + 80} ${dasar - 244} L ${L / 2 + 80} ${dasar} Z`} fill="#FFE2A0" opacity={nyala * buka} />
      <g transform={`translate(${L / 2 - 80} 0) scale(${1 - buka * 0.72} 1)`}>
        <path d={`M 0 ${dasar} L 0 ${dasar - 244} Q 80 ${dasar - 326} 160 ${dasar - 244} L 160 ${dasar} Z`} fill={C.kayu} />
        <circle cx={132} cy={dasar - 120} r={9} fill={C.emas} />
      </g>
      <path d={`M 0 ${dasar} L ${L} ${dasar} L ${L} ${h} L 0 ${h} Z`} fill={C.tanahDepan} opacity={0.9} />
      <Kurma x={84} y={dasar + 8} frame={frame} s={0.85} />
    </g>
  );
};

const Sedekah: React.FC<P> = ({ frame, h, fps }) => {
  const p = pegas(frame, fps, 4);
  const yTangan = interpolate(p, [0, 1], [-140, 150]);
  const mangkuk = h - 150;
  return (
    <g>
      <Bintang2 frame={frame} h={h} n={12} />
      <circle cx={L / 2} cy={mangkuk - 60} r={250} fill={C.emas} opacity={0.08 + 0.03 * Math.sin(frame / 12)} />
      <g transform={`translate(${L / 2} ${yTangan}) rotate(${Math.sin(frame / 20) * 3})`}>
        <path d="M 70 -190 L 250 -330 L 330 -240 L 130 -90 Z" fill={JUBAH[1]} />
        <path d="M -70 -40 Q -90 -110 -10 -130 L 110 -150 Q 150 -110 120 -60 L 20 -10 Q -40 4 -70 -40 Z" fill={C.kulit} />
      </g>
      {[0, 1, 2, 3].map((i) => {
        const t = ((frame + i * 14) % 56) / 56, y = interpolate(t, [0, 1], [yTangan, mangkuk - 30], { easing: theme.ease.in });
        return (
          <g key={i} transform={`translate(${L / 2 + (i - 1.5) * 26} ${y})`} opacity={p * (t > 0.92 ? 0 : 1)}>
            <ellipse rx={22} ry={22 * Math.abs(Math.cos(frame / 5 + i))} fill={C.emas} /><ellipse rx={13} ry={13 * Math.abs(Math.cos(frame / 5 + i))} fill="#F7D58A" />
          </g>
        );
      })}
      <g transform={`translate(${L / 2} ${mangkuk})`}>
        <path d="M -150 0 Q -150 110 0 120 Q 150 110 150 0 Z" fill="#8A5A3A" /><ellipse rx={150} ry={26} fill="#5E3B25" />
        {[-70, -24, 24, 70].map((x, i) => <ellipse key={x} cx={x} cy={-4 - (i % 2) * 8} rx={26} ry={10} fill={C.emas} />)}
        <g transform="translate(0 -20)"><Percik frame={frame} lebar={260} tinggi={150} n={8} op={p} /></g>
      </g>
      <path d={`M 0 ${h - 34} L ${L} ${h - 34} L ${L} ${h} L 0 ${h} Z`} fill={C.tanahDepan} />
    </g>
  );
};

const Hati: React.FC<P> = ({ frame, h, fps }) => {
  const p = pegas(frame, fps, 4, theme.spring.bouncy);
  const t = (frame % 34) / 34;
  const denyut = 1 + (t < 0.16 ? Math.sin((t / 0.16) * Math.PI) * 0.09 : t < 0.36 && t > 0.2 ? Math.sin(((t - 0.2) / 0.16) * Math.PI) * 0.06 : 0);
  return (
    <g transform={`translate(${L / 2} ${h * 0.54})`}>
      <Sinar frame={frame} r1={170} r2={470} n={12} op={0.36 * p} laju={-0.16} />
      {[0, 1].map((i) => { const r = ((frame + i * 17) % 34) / 34; return <circle key={i} r={130 + r * 170} fill="none" stroke={C.emas} strokeWidth={5} opacity={(1 - r) * 0.45 * p} />; })}
      <g transform={`scale(${p * denyut})`}>
        <path d="M 0 110 C -190 -10 -150 -160 -70 -150 C -30 -146 -8 -120 0 -96 C 8 -120 30 -146 70 -150 C 150 -160 190 -10 0 110 Z" fill="#C8483F" />
        <path d="M -98 -92 C -86 -128 -50 -132 -34 -112" stroke="#F2A69B" strokeWidth={12} fill="none" strokeLinecap="round" />
      </g>
      <g transform="translate(0 -60)"><Percik frame={frame} lebar={440} tinggi={220} n={10} op={p} /></g>
    </g>
  );
};

const ADEGAN: Record<JenisIlustrasi, React.FC<P>> = {
  badai: Badai, kota_malam: KotaMalam, quran: Quran, kafilah: Kafilah, kabah: Kabah, masjid: Masjid, gua: Gua, majelis: Majelis,
  lentera: Lentera, fajar: Fajar, air: Air, hidangan: Hidangan, pintu: Pintu, sedekah: Sedekah, hati: Hati,
};
const LANGIT: Partial<Record<JenisIlustrasi, [string, string]>> = {
  kafilah: [C.senjaAtas, C.senjaBawah], fajar: [C.senjaAtas, C.fajarBawah], majelis: ["#101A24", "#243540"],
};
// Tempat tokoh berdiri (x, skala) per adegan; adegan yang sudah penuh tidak diberi tokoh.
const TEMPAT_TOKOH: Partial<Record<JenisIlustrasi, [number, number]>> = {
  badai: [650, 1.02], kota_malam: [700, 0.9], kabah: [735, 0.66], kafilah: [760, 0.82], masjid: [780, 0.62], gua: [250, 0.8], lentera: [730, 0.86],
  fajar: [700, 0.9], air: [730, 0.86], hidangan: [770, 0.8], pintu: [720, 0.82], quran: [760, 0.8], hati: [760, 0.8],
};

/** Panggung ilustrasi: jendela membulat dengan langit sendiri. tokoh = pose manusia tanpa wajah (opsional). */
export const Ilustrasi: React.FC<{ jenis?: JenisIlustrasi; tokoh?: Pose | ""; tinggi: number; delay?: number; lebar?: number }> = ({
  jenis, tokoh, tinggi, delay = 0, lebar = L,
}) => {
  const frameAsli = useCurrentFrame();
  const { fps } = useVideoConfig();
  if (!jenis || !ADEGAN[jenis]) return null;
  const frame = frameAsli - delay;
  const p = spring({ frame, fps, config: theme.spring.smooth });
  const Adegan = ADEGAN[jenis];
  const [atas, bawah] = LANGIT[jenis] ?? [C.malamAtas, C.malamBawah];
  const tempat = TEMPAT_TOKOH[jenis];
  const skala = lebar / L;
  return (
    <div style={{ width: lebar, height: tinggi * skala, opacity: p, transform: `translateY(${interpolate(p, [0, 1], [50, 0])}px) scale(${interpolate(p, [0, 1], [0.94, 1])})`,
      borderRadius: 44 * skala, overflow: "hidden", border: `2px solid ${theme.colors.line}`, boxShadow: "0 44px 80px -30px rgba(0,0,0,0.7)" }}>
      <svg width={lebar} height={tinggi * skala} viewBox={`0 0 ${L} ${tinggi}`}>
        <defs>
          <linearGradient id={`langit-${jenis}`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor={atas} /><stop offset="1" stopColor={bawah} />
          </linearGradient>
        </defs>
        <rect width={L} height={tinggi} fill={`url(#langit-${jenis})`} />
        <Adegan frame={frame} h={tinggi} fps={fps} />
        {tokoh && tempat ? (
          <g opacity={spring({ frame: frame - 12, fps, config: theme.spring.smooth })}>
            <Tokoh x={tempat[0]} y={tinggi - 62} s={tempat[1]} pose={tokoh} frame={frame} />
          </g>
        ) : null}
      </svg>
    </div>
  );
};
