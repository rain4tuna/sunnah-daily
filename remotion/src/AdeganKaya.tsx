import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { theme } from "./theme";
import { clamp } from "./Motion";
import { Ilustrasi, JENIS, JenisIlustrasi } from "./Ilustrasi";
import { KarakterKaya, POSE_KAYA, PoseKaya, VarianKarakter } from "./KarakterKaya";
import { JENIS_PROPERTI, JenisProperti, PropertiKaya } from "./PropertiKaya";

/**
 * AdeganKaya — Panggung visual berlapis (parallax + kamera organik + karakter berartikulasi + properti hidup).
 *
 * Mendukung 15 adegan eksisting + 6 adegan baru yang lebih kaya = 21 adegan total.
 * ATURAN SUNNAH: Semua karakter di sini memakai KarakterKaya (100% TANPA MATA, TANPA HIDUNG, TANPA MULUT).
 */

export const ADEGAN_BARU = [
  "doa_malam",
  "belajar_ilmu",
  "keluarga_hangat",
  "hijrah_perjalanan",
  "taman_berkah",
  "waktu_subuh",
] as const;

export type JenisAdeganBaru = (typeof ADEGAN_BARU)[number];
export type JenisAdeganKaya = JenisIlustrasi | JenisAdeganBaru;

export const SEMUA_ADEGAN_KAYA: readonly JenisAdeganKaya[] = [...JENIS, ...ADEGAN_BARU];

const L = 790;

const acak = (i: number, s = 1) => {
  const x = Math.sin(i * 127.1 * s + 311.7) * 43758.5453;
  return x - Math.floor(x);
};

/** Partikel cahaya lembut melayang (kedalaman atmosfer tanpa mengganggu teks). */
const DebuCahaya: React.FC<{ frame: number; h: number; n?: number }> = ({ frame, h, n = 14 }) => (
  <g>
    {Array.from({ length: n }).map((_, i) => {
      const t = ((frame * (0.4 + acak(i, 3) * 0.6) + acak(i) * 200) % 200) / 200;
      const cx = acak(i, 2) * L + Math.sin(frame / 28 + i) * 14;
      const cy = h - t * (h + 40);
      return (
        <circle
          key={i}
          cx={cx}
          cy={cy}
          r={2.2 + acak(i, 4) * 3.2}
          fill="#FFE8AE"
          opacity={Math.sin(t * Math.PI) * 0.55}
        />
      );
    })}
  </g>
);

const LangitBintang: React.FC<{ frame: number; h: number; n?: number }> = ({ frame, h, n = 24 }) => (
  <g>
    {Array.from({ length: n }).map((_, i) => (
      <circle
        key={i}
        cx={acak(i, 5) * L}
        cy={acak(i, 7) * h * 0.52}
        r={1.4 + acak(i, 9) * 2}
        fill="#FFF6DC"
        opacity={0.3 + 0.6 * Math.abs(Math.sin(frame / (12 + acak(i, 11) * 18) + i))}
      />
    ))}
  </g>
);

/** 6 adegan baru dengan kedalaman parallax (far/mid/near). */
const AdeganBaruSvg: React.FC<{ jenis: JenisAdeganBaru; frame: number; h: number; fps: number }> = ({
  jenis,
  frame,
  h,
  fps,
}) => {
  const p = spring({ frame, fps, config: theme.spring.smooth });
  const pan = Math.sin(frame / 55) * 14;
  const nyala = 0.8 + 0.2 * Math.sin(frame / 9);

  if (jenis === "doa_malam") {
    return (
      <g>
        <LangitBintang frame={frame} h={h} n={30} />
        {/* Bulan sabit + berkas cahaya langit */}
        <g transform={`translate(${140 + pan * 0.3} ${104})`}>
          <circle r={68} fill={theme.colors.hero} opacity={0.13} />
          <circle r={42} fill={theme.colors.hero} />
          <circle cx={16} cy={-8} r={38} fill="#091522" />
        </g>
        <polygon points={`395,0 ${250 + pan * 0.4},${h} ${540 + pan * 0.4},${h}`} fill={theme.colors.hero} opacity={0.07 * nyala} />
        {/* Lengkungan mihrab masjid di belakang */}
        <g transform={`translate(${L / 2 + pan * 0.5} ${h - 56})`}>
          <path d="M -210 0 L -210 -240 Q 0 -390 210 -240 L 210 0 Z" fill="#13262E" stroke={theme.colors.line} strokeWidth={3} />
          <path d="M -150 0 L -150 -200 Q 0 -320 150 -200 L 150 0 Z" fill="#19333D" />
        </g>
        {/* Sajadah & lantai */}
        <rect x={0} y={h - 68} width={L} height={68} fill="#0D1B20" />
        <path d={`M 180 ${h - 14} L 260 ${h - 68} L 530 ${h - 68} L 610 ${h - 14} Z`} fill="#1E5F54" opacity={0.85} />
        <path d={`M 210 ${h - 22} L 274 ${h - 62} L 516 ${h - 62} L 580 ${h - 22} Z`} fill="none" stroke={theme.colors.hero} strokeWidth={2.5} opacity={0.65} />
        <DebuCahaya frame={frame} h={h} n={16} />
      </g>
    );
  }

  if (jenis === "belajar_ilmu") {
    return (
      <g>
        <LangitBintang frame={frame} h={h} n={12} />
        {/* Rak kitab + jendela lengkung */}
        <rect x={0} y={0} width={L} height={h - 66} fill="#162830" />
        {[150, 640].map((jx) => (
          <g key={jx} transform={`translate(${jx + pan * 0.35} ${h - 190})`}>
            <path d="M -64 90 L -64 -70 Q 0 -138 64 -70 L 64 90 Z" fill="#23414D" stroke={theme.colors.line} strokeWidth={3} />
            <circle cx={14} cy={-44} r={18} fill={theme.colors.hero} opacity={0.85} />
            <circle cx={22} cy={-48} r={16} fill="#23414D" />
          </g>
        ))}
        {/* Meja kayu rehal & gulungan ilmu */}
        <rect x={0} y={h - 72} width={L} height={72} fill="#101E24" />
        <g transform={`translate(${L / 2} ${h - 70}) scale(${p})`}>
          <ellipse cy={-70} rx={210} ry={130} fill={theme.colors.hero} opacity={0.11 * nyala} />
          <rect x={-190} y={-24} width={380} height={24} rx={8} fill="#6F4B2C" />
          <rect x={-150} y={0} width={22} height={46} fill="#52351E" />
          <rect x={128} y={0} width={22} height={46} fill="#52351E" />
        </g>
        <DebuCahaya frame={frame} h={h} n={12} />
      </g>
    );
  }

  if (jenis === "keluarga_hangat") {
    return (
      <g>
        <rect width={L} height={h} fill="#1B2A30" />
        <ellipse cx={L / 2} cy={h * 0.48} rx={360} ry={210} fill={theme.colors.hero} opacity={0.13 * nyala} />
        {/* Dinding ruang hangat & jendela senja */}
        <g transform={`translate(${L / 2 + pan * 0.3} ${150})`}>
          <path d="M -110 110 L -110 -30 Q 0 -116 110 -30 L 110 110 Z" fill="#C98746" opacity={0.78} />
          <path d="M -110 110 L -110 -30 Q 0 -116 110 -30 L 110 110 Z" fill="none" stroke="#6E4B2E" strokeWidth={8} />
          <line x1={0} y1={-90} x2={0} y2={110} stroke="#6E4B2E" strokeWidth={6} />
          <line x1={-110} y1={24} x2={110} y2={24} stroke="#6E4B2E" strokeWidth={6} />
        </g>
        {/* Permadani ruang keluarga */}
        <rect x={0} y={h - 76} width={L} height={76} fill="#142126" />
        <path d={`M 80 ${h - 10} L 160 ${h - 74} L 630 ${h - 74} L 710 ${h - 10} Z`} fill="#6C342E" />
        <path d={`M 110 ${h - 18} L 178 ${h - 66} L 612 ${h - 66} L 680 ${h - 18} Z`} fill="none" stroke={theme.colors.hero} strokeWidth={3} opacity={0.65} />
        <DebuCahaya frame={frame} h={h} n={10} />
      </g>
    );
  }

  if (jenis === "hijrah_perjalanan") {
    const geser = (frame * 1.4) % L;
    return (
      <g>
        <LangitBintang frame={frame} h={h} n={22} />
        <circle cx={620} cy={126} r={54} fill="#F2B857" opacity={0.92} />
        <circle cx={620} cy={126} r={96} fill="#F2B857" opacity={0.14} />
        {/* Bukit jauh (parallax pelan) */}
        <path
          d={`M ${-80 - geser * 0.15} ${h - 130} Q ${180 - geser * 0.15} ${h - 230} ${420 - geser * 0.15} ${h - 150} T ${L + 160} ${h - 170} L ${L + 160} ${h} L -80 ${h} Z`}
          fill="#8C5832"
        />
        {/* Bukit tengah */}
        <path
          d={`M ${-80 - pan} ${h - 86} Q 250 ${h - 160} 520 ${h - 92} T ${L + 80} ${h - 110} L ${L + 80} ${h} L -80 ${h} Z`}
          fill="#5E3921"
        />
        {/* Jalan jejak kaki di padang pasir */}
        <path d={`M 0 ${h - 46} Q 260 ${h - 80} 540 ${h - 52} T ${L} ${h - 60} L ${L} ${h} L 0 ${h} Z`} fill="#382216" />
        <DebuCahaya frame={frame} h={h} n={12} />
      </g>
    );
  }

  if (jenis === "taman_berkah") {
    const riak = Math.sin(frame / 14) * 6;
    return (
      <g>
        {/* Cahaya fajar lembut di balik pepohonan */}
        <circle cx={L / 2} cy={120} r={110} fill="#FFE2A3" opacity={0.22} />
        {/* Bukit hijau berlapis */}
        <path d={`M 0 ${h - 130} Q 220 ${h - 210} 440 ${h - 140} T ${L} ${h - 160} L ${L} ${h} L 0 ${h} Z`} fill="#1D594E" />
        {/* Pohon rindang kiri & kanan yang bergoyang lembut */}
        {[120, 670].map((tx, idx) => (
          <g key={tx} transform={`translate(${tx} ${h - 96}) rotate(${Math.sin(frame / 24 + idx * 2) * 2})`}>
            <rect x={-10} y={-140} width={20} height={140} rx={8} fill="#5C3D26" />
            <circle cx={0} cy={-166} r={66} fill="#256E5E" />
            <circle cx={-38} cy={-140} r={48} fill="#1F6052" />
            <circle cx={38} cy={-140} r={48} fill="#2C7E6C" />
          </g>
        ))}
        {/* Sungai jernih mengalir */}
        <path d={`M 0 ${h - 72} L ${L} ${h - 72} L ${L} ${h} L 0 ${h} Z`} fill="#174D57" />
        <path d={`M ${120 + riak} ${h - 44} Q ${360 + riak} ${h - 56} ${640 + riak} ${h - 40}`} stroke="#8FD8E8" strokeWidth={5} fill="none" strokeLinecap="round" opacity={0.55} />
        <DebuCahaya frame={frame} h={h} n={16} />
      </g>
    );
  }

  // waktu_subuh
  const naik = interpolate(p, [0, 1], [h - 40, h - 180], clamp);
  return (
    <g>
      <LangitBintang frame={frame} h={h} n={14} />
      <circle cx={L / 2} cy={naik} r={130} fill={theme.colors.hero} opacity={0.18} />
      <circle cx={L / 2} cy={naik} r={76} fill="#FFD98F" />
      {/* Siluet masjid subuh dengan kubah dan menara */}
      <g transform={`translate(${L / 2 + pan * 0.4} ${h - 56})`}>
        <rect x={-210} y={-110} width={420} height={110} fill="#162933" />
        <path d="M -126 -110 Q 0 -276 126 -110 Z" fill="#1F4A47" />
        <rect x={-236} y={-230} width={28} height={230} fill="#162933" />
        <path d="M -242 -230 L -222 -268 L -202 -230 Z" fill="#1F4A47" />
        <rect x={208} y={-230} width={28} height={230} fill="#162933" />
        <path d="M 202 -230 L 222 -268 L 242 -230 Z" fill="#1F4A47" />
        {[-120, -40, 40, 120].map((wx, i) => (
          <rect key={wx} x={wx - 14} y={-76} width={28} height={52} rx={14} fill="#F4C76A" opacity={0.75 + 0.25 * Math.sin(frame / 9 + i)} />
        ))}
      </g>
      <rect x={0} y={h - 58} width={L} height={58} fill="#0D1B22" />
      <DebuCahaya frame={frame} h={h} n={12} />
    </g>
  );
};

const LANGIT_BARU: Record<JenisAdeganBaru, [string, string]> = {
  doa_malam: ["#081220", "#162C3B"],
  belajar_ilmu: ["#101F28", "#1E3843"],
  keluarga_hangat: ["#1A222B", "#3A2D2B"],
  hijrah_perjalanan: ["#1A223E", "#C6753E"],
  taman_berkah: ["#133540", "#3D7E6E"],
  waktu_subuh: ["#182342", "#D69452"],
};

const PROPERTI_DEFAULT: Partial<Record<JenisAdeganKaya, JenisProperti>> = {
  badai: "jam_pasir",
  kota_malam: "lentera_emas",
  quran: "mushaf_terbuka",
  kafilah: "kompas_kiblat",
  kabah: "kompas_kiblat",
  masjid: "pelita_malam",
  gua: "lentera_emas",
  majelis: "gulungan_surat",
  lentera: "lentera_emas",
  fajar: "jam_pasir",
  air: "kendi_air",
  hidangan: "kurma_piring",
  pintu: "pintu_cahaya",
  sedekah: "koin_sedekah",
  hati: "tasbih_kayu",
  doa_malam: "tasbih_kayu",
  belajar_ilmu: "mushaf_terbuka",
  keluarga_hangat: "kurma_piring",
  hijrah_perjalanan: "kompas_kiblat",
  taman_berkah: "kendi_air",
  waktu_subuh: "pelita_malam",
};

const isAdeganBaru = (j: string): j is JenisAdeganBaru =>
  (ADEGAN_BARU as readonly string[]).includes(j);

const toPoseKaya = (pose?: string): PoseKaya | "" => {
  if (!pose) return "";
  return (POSE_KAYA as readonly string[]).includes(pose) ? (pose as PoseKaya) : "berdiri";
};

/**
 * Panggung visual utama untuk SunnahMotion (9:16).
 * Menggabungkan: kamera zoom/pan halus + 21 adegan berlapis + KarakterKaya (wajah polos) + PropertiKaya.
 */
export const AdeganKaya: React.FC<{
  jenis?: string;
  tokoh?: string;
  varian?: VarianKarakter;
  properti?: JenisProperti;
  tinggi?: number;
  lebar?: number;
  delay?: number;
}> = ({ jenis = "lentera", tokoh = "", varian = "pria_sorban", properti, tinggi = 460, lebar = L, delay = 0 }) => {
  const frameAsli = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const frame = Math.max(0, frameAsli - delay);

  // Gerak kamera organik + micro pattern-interrupt tiap ~2.5 detik
  const zoom = interpolate(frame, [0, Math.max(30, durationInFrames)], [1.0, 1.075], clamp);
  const panX = Math.sin(frame / 42) * 8;
  const pose = toPoseKaya(tokoh);
  const propJenis = properti ?? PROPERTI_DEFAULT[jenis as JenisAdeganKaya] ?? "lentera_emas";
  const skala = lebar / L;
  const masuk = spring({ frame, fps, config: theme.spring.snappy });

  // Untuk 15 adegan eksisting, gunakan Ilustrasi sebagai latar belakang TANPA tokoh lama,
  // lalu lapisi KarakterKaya & PropertiKaya agar gerakan lebih kaya dan natural!
  const pakaiBaru = isAdeganBaru(jenis);
  const jenisLama: JenisIlustrasi = (JENIS as readonly string[]).includes(jenis)
    ? (jenis as JenisIlustrasi)
    : "lentera";

  return (
    <div
      style={{
        width: lebar,
        height: tinggi * skala,
        borderRadius: 36 * skala,
        overflow: "hidden",
        position: "relative",
        border: `2px solid ${theme.colors.line}`,
        boxShadow: "0 34px 70px -24px rgba(0,0,0,0.72)",
        transform: `scale(${interpolate(masuk, [0, 1], [0.96, 1])})`,
      }}
    >
      {/* Lapisan latar belakang dengan kamera push-in halus */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          transform: `scale(${zoom}) translateX(${panX}px)`,
          transformOrigin: "50% 60%",
        }}
      >
        {pakaiBaru ? (
          <svg width={lebar} height={tinggi * skala} viewBox={`0 0 ${L} ${tinggi}`}>
            <defs>
              <linearGradient id={`langit-kaya-${jenis}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="0" stopColor={LANGIT_BARU[jenis][0]} />
                <stop offset="1" stopColor={LANGIT_BARU[jenis][1]} />
              </linearGradient>
            </defs>
            <rect width={L} height={tinggi} fill={`url(#langit-kaya-${jenis})`} />
            <AdeganBaruSvg jenis={jenis} frame={frame} h={tinggi} fps={fps} />
          </svg>
        ) : (
          <Ilustrasi jenis={jenisLama} tokoh="" tinggi={tinggi} lebar={lebar} delay={0} />
        )}
      </div>

      {/* Lapisan depan: KarakterKaya (strictly faceless) + PropertiKaya (animasi spring + apung) */}
      <svg
        width={lebar}
        height={tinggi * skala}
        viewBox={`0 0 ${L} ${tinggi}`}
        style={{ position: "absolute", inset: 0, pointerEvents: "none" }}
      >
        {/* Properti animasi mengapung di sisi kiri atas / seimbang dengan karakter */}
        <PropertiKaya
          jenis={propJenis}
          x={pose ? 156 : 138}
          y={114}
          scale={0.86}
          frame={frame}
          delay={6}
        />

        {/* Karakter artikulasi tanpa mata & hidung bila diizinkan oleh filter Sunnah */}
        {pose ? (
          <g
            transform={`translate(${
              pose === "berjalan"
                ? interpolate(frame, [0, Math.max(45, durationInFrames)], [490, 625], clamp)
                : 600
            } ${tinggi - 42})`}
          >
            <KarakterKaya
              x={0}
              y={0}
              scale={Math.min(0.82, (tinggi / 420) * 0.82)}
              pose={pose}
              varian={varian}
              frame={frame}
              hadap={pose === "berjalan" ? 1 : -1}
            />
          </g>
        ) : null}
      </svg>

      {/* Vignette panggung halus untuk kontras */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          pointerEvents: "none",
          background:
            "linear-gradient(180deg, rgba(8,18,22,0.16), transparent 28%, transparent 72%, rgba(8,18,22,0.42))",
        }}
      />
    </div>
  );
};

export { JENIS_PROPERTI };
