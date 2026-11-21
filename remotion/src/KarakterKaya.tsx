import React from "react";
import { theme } from "./theme";

/**
 * KarakterKaya — Karakter SVG artikulasi multi-bagian dengan gerakan alami.
 *
 * ATURAN SUNNAH WAJIB (TIDAK BOLEH DILANGGAR):
 * - SEMUA karakter 100% TANPA MATA, TANPA ALIS, TANPA HIDUNG, TANPA MULUT (wajah polos mulus).
 * - Tidak pernah dipakai untuk menggambarkan Nabi ﷺ, para nabi, sahabat, atau malaikat
 *   (dijaga oleh filter KATA_TANPA_TOKOH_RE di storyboard_ikon.py).
 */

export const POSE_KAYA = [
  "berdiri",
  "berjalan",
  "berdoa",
  "panik",
  "takut",
  "menunjuk",
  "duduk_membaca",
  "berbagi",
] as const;

export type PoseKaya = (typeof POSE_KAYA)[number];

export type VarianKarakter = "pria_sorban" | "pemuda" | "tetua_jubah" | "wanita_hijab";

type Props = {
  x: number;
  y: number;
  scale?: number;
  pose: PoseKaya;
  varian?: VarianKarakter;
  frame: number;
  hadap?: 1 | -1;
};

const PALET: Record<
  VarianKarakter,
  { jubah: string; jubahGelap: string; rompi: string; sorban: string; kulit: string; janggut?: string; hijab?: boolean }
> = {
  pria_sorban: {
    jubah: "#2C5E63",
    jubahGelap: "#1C4045",
    rompi: "#C98D3B",
    sorban: "#EFE6D5",
    kulit: "#D8A97E",
    janggut: "#3A2C24",
  },
  pemuda: {
    jubah: "#6B3A35",
    jubahGelap: "#4A2521",
    rompi: "#D4A359",
    sorban: "#E8DCC6",
    kulit: "#D5A47A",
  },
  tetua_jubah: {
    jubah: "#4B445E",
    jubahGelap: "#332E42",
    rompi: "#B79B63",
    sorban: "#F2ECE0",
    kulit: "#CFA078",
    janggut: "#B8B2A6",
  },
  wanita_hijab: {
    jubah: "#335B6B",
    jubahGelap: "#22404D",
    rompi: "#537C8A",
    sorban: "#E8DFCF",
    kulit: "#D8AA80",
    hijab: true,
  },
};

/** Lengan berartikulasi 2 segmen (bahu -> siku -> tangan) dengan lengan baju mengalir. */
const Lengan: React.FC<{
  bx: number;
  by: number;
  sudutAtas: number;
  sudutBawah: number;
  warna: string;
  warnaGelap: string;
  kulit: string;
  panjang1?: number;
  panjang2?: number;
}> = ({ bx, by, sudutAtas, sudutBawah, warna, warnaGelap, kulit, panjang1 = 62, panjang2 = 54 }) => (
  <g transform={`translate(${bx} ${by}) rotate(${sudutAtas})`}>
    {/* Lengan atas */}
    <path
      d={`M -14 0 Q -17 ${panjang1 * 0.55} -12 ${panjang1} L 12 ${panjang1} Q 16 ${panjang1 * 0.55} 14 0 Z`}
      fill={warna}
    />
    <path d={`M 4 4 L 10 ${panjang1 - 4}`} stroke={warnaGelap} strokeWidth={4} strokeLinecap="round" opacity={0.45} />
    {/* Siku -> lengan bawah */}
    <g transform={`translate(0 ${panjang1}) rotate(${sudutBawah})`}>
      <path
        d={`M -12 0 Q -15 ${panjang2 * 0.6} -11 ${panjang2} L 11 ${panjang2} Q 15 ${panjang2 * 0.6} 12 0 Z`}
        fill={warna}
      />
      {/* Manset halus */}
      <rect x={-12} y={panjang2 - 9} width={24} height={9} rx={4} fill={warnaGelap} opacity={0.55} />
      {/* Telapak tangan sederhana (tanpa wajah/jari rumit) */}
      <ellipse cx={0} cy={panjang2 + 10} rx={12} ry={13} fill={kulit} />
    </g>
  </g>
);

export const KarakterKaya: React.FC<Props> = ({
  x,
  y,
  scale = 1,
  pose,
  varian = "pria_sorban",
  frame,
  hadap = 1,
}) => {
  const c = PALET[varian];
  const duduk = pose === "duduk_membaca";
  const berjalan = pose === "berjalan";
  const gelisah = pose === "panik" || pose === "takut";

  // Siklus napas organik & ayunan berat badan (overlapping action)
  const napas = Math.sin(frame / 18);
  const langkah = Math.sin(frame / 5.5);
  const langkah2 = Math.cos(frame / 5.5);
  const bob = berjalan ? -Math.abs(langkah) * 11 : napas * 3.2;
  const squashY = 1 + napas * 0.014 - (berjalan ? Math.abs(langkah) * 0.025 : 0);
  const squashX = 1 - napas * 0.01 + (berjalan ? Math.abs(langkah) * 0.02 : 0);

  // Getaran atau condong tubuh sesuai emosi/pose
  const getarX = gelisah ? Math.sin(frame * 1.6) * 2.8 : 0;
  let condongBadan = Math.sin(frame / 28) * 1.8;
  let anggukKepala = Math.sin(frame / 22 - 0.6) * 2.5; // fase tertunda dari badan -> gerak natural

  // Sudut sendi lengan kiri (k) dan kanan (r): [bahu, siku]
  let bahuK = 18 + Math.sin(frame / 24) * 4;
  let sikuK = -12 + Math.sin(frame / 24 - 0.7) * 5;
  let bahuR = -18 - Math.sin(frame / 24) * 4;
  let sikuR = 12 - Math.sin(frame / 24 - 0.7) * 5;

  if (berjalan) {
    condongBadan = 4.5 + langkah * 2.2;
    anggukKepala = -2 + langkah2 * 3;
    bahuK = langkah * 32;
    sikuK = -18 - Math.max(0, langkah) * 16;
    bahuR = -langkah * 32;
    sikuR = -18 - Math.max(0, -langkah) * 16;
  } else if (pose === "berdoa") {
    condongBadan = -2 + Math.sin(frame / 26) * 1.5;
    anggukKepala = -3 + Math.sin(frame / 26 - 0.5) * 2;
    const ayunDoa = Math.sin(frame / 16) * 5;
    bahuK = 30 + ayunDoa;
    sikuK = -132 - ayunDoa * 0.6;
    bahuR = -30 - ayunDoa;
    sikuR = 132 + ayunDoa * 0.6;
  } else if (pose === "panik") {
    condongBadan = Math.sin(frame / 6) * 4.5;
    anggukKepala = Math.sin(frame / 5) * 6;
    const gerak = Math.sin(frame / 5) * 12;
    bahuK = 128 + gerak;
    sikuK = -44 - gerak * 0.5;
    bahuR = -128 - gerak;
    sikuR = 44 + gerak * 0.5;
  } else if (pose === "takut") {
    condongBadan = -9 + Math.sin(frame / 9) * 2.2;
    anggukKepala = -6 + Math.sin(frame / 8) * 3;
    bahuK = 88 + Math.sin(frame / 7) * 6;
    sikuK = -72;
    bahuR = 48 + Math.sin(frame / 7) * 5;
    sikuR = -88;
  } else if (pose === "menunjuk") {
    condongBadan = 5 + Math.sin(frame / 20) * 1.8;
    anggukKepala = 3 + Math.sin(frame / 18 - 0.5) * 2.5;
    bahuK = 14 + Math.sin(frame / 20) * 4;
    sikuK = -16;
    bahuR = -82 + Math.sin(frame / 11) * 7;
    sikuR = -12 + Math.sin(frame / 11 - 0.6) * 6;
  } else if (pose === "duduk_membaca") {
    condongBadan = 6 + Math.sin(frame / 24) * 1.6;
    anggukKepala = 9 + Math.sin(frame / 24 - 0.8) * 2.5;
    bahuK = 36 + Math.sin(frame / 20) * 3;
    sikuK = -68;
    bahuR = -36 - Math.sin(frame / 20) * 3;
    sikuR = 68;
  } else if (pose === "berbagi") {
    condongBadan = 5 + Math.sin(frame / 18) * 2;
    anggukKepala = 2 + Math.sin(frame / 18 - 0.5) * 2;
    const ulur = Math.sin(frame / 15) * 6;
    bahuK = 22;
    sikuK = -25;
    bahuR = -58 + ulur;
    sikuR = -28 + ulur * 0.4;
  }

  // Ayunan kain bawah & ekor sorban (secondary motion)
  const kibasKain = berjalan ? langkah * 12 : Math.sin(frame / 24 - 0.9) * 5;
  const kibasSorban = Math.sin(frame / 19 - 1.1) * (berjalan ? 9 : 4);
  const denyut = 0.55 + 0.45 * Math.abs(Math.sin(frame / 6));

  return (
    <g transform={`translate(${x + getarX} ${y}) scale(${scale * hadap} ${scale})`}>
      {/* Bayangan lembut di tanah */}
      <ellipse cx={0} cy={4} rx={duduk ? 104 : 84} ry={14} fill="#000000" opacity={0.3} />

      {/* Kepulan debu kaki saat berjalan */}
      {berjalan ? (
        <g opacity={0.45}>
          {[0, 1, 2].map((i) => {
            const t = ((frame + i * 7) % 21) / 21;
            return (
              <circle
                key={i}
                cx={-26 - t * 65 - i * 8}
                cy={-4 - t * 18}
                r={7 + t * 11}
                fill="#D8B88C"
                opacity={(1 - t) * 0.7}
              />
            );
          })}
        </g>
      ) : null}

      {/* Kaki (saat berdiri/berjalan) */}
      {!duduk ? (
        <g>
          <g transform={`translate(-22 -46) rotate(${berjalan ? langkah * 24 : 0})`}>
            <rect x={-12} y={0} width={24} height={42} rx={10} fill={c.jubahGelap} />
            <ellipse cx={4} cy={44} rx={18} ry={8} fill="#3B291E" />
          </g>
          <g transform={`translate(22 -46) rotate(${berjalan ? -langkah * 24 : 0})`}>
            <rect x={-12} y={0} width={24} height={42} rx={10} fill={c.jubahGelap} />
            <ellipse cx={4} cy={44} rx={18} ry={8} fill="#4D3628" />
          </g>
        </g>
      ) : null}

      {/* Tubuh utama (bernapas & condong) */}
      <g
        transform={`translate(0 ${duduk ? 28 + bob * 0.5 : bob}) rotate(${condongBadan} 0 -80) scale(${squashX} ${squashY})`}
      >
        {/* Lengan belakang */}
        <Lengan
          bx={-44}
          by={duduk ? -156 : -196}
          sudutAtas={bahuK}
          sudutBawah={sikuK}
          warna={c.jubahGelap}
          warnaGelap="#0E1A1E"
          kulit={c.kulit}
        />

        {/* Jubah / gamis longgar */}
        {duduk ? (
          <g>
            <path d="M -94 -24 Q -102 -88 -52 -176 Q 0 -202 52 -176 Q 102 -88 94 -24 Z" fill={c.jubah} />
            <ellipse cx={0} cy={-26} rx={92} ry={22} fill={c.jubahGelap} />
          </g>
        ) : (
          <g>
            <path
              d={`M ${-74 + kibasKain} -18 L -52 -208 Q 0 -234 52 -208 L ${74 + kibasKain} -18 Q 0 -6 ${-74 + kibasKain} -18 Z`}
              fill={c.jubah}
            />
            {/* Lipatan kain dinamis */}
            <path
              d={`M -6 -212 Q ${4 + kibasKain * 0.4} -112 ${-10 + kibasKain * 0.8} -18 L ${16 + kibasKain * 0.8} -18 Q ${18 + kibasKain * 0.4} -112 10 -212 Z`}
              fill={c.jubahGelap}
              opacity={0.42}
            />
            {/* Rompi / selempang lembut */}
            <path d="M -46 -208 Q 0 -184 46 -208 L 38 -118 Q 0 -106 -38 -118 Z" fill={c.rompi} opacity={0.82} />
            <rect x={-48} y={-126} width={96} height={14} rx={7} fill={c.jubahGelap} opacity={0.55} />
          </g>
        )}

        {/* Buku / mushaf kecil di tangan saat duduk_membaca */}
        {duduk ? (
          <g transform={`translate(0 ${-104 + napas * 2})`}>
            <path d="M -46 -12 Q -22 -24 0 -10 Q 22 -24 46 -12 L 42 18 Q 20 8 0 18 Q -20 8 -42 18 Z" fill="#F4EBD8" stroke={theme.colors.hero} strokeWidth={3} />
            <line x1={0} y1={-10} x2={0} y2={18} stroke={c.jubahGelap} strokeWidth={2.5} />
          </g>
        ) : null}

        {/* Kepala & penutup kepala — 100% WAJAH POLOS (TANPA MATA, TANPA ALIS, TANPA HIDUNG, TANPA MULUT) */}
        <g transform={`translate(0 ${duduk ? -214 : -254}) rotate(${anggukKepala} 0 32)`}>
          {/* Leher */}
          <rect x={-13} y={24} width={26} height={26} rx={10} fill={c.kulit} />
          {/* Ekor sorban / ujung hijab di belakang kepala */}
          {!c.hijab ? (
            <path
              d={`M 26 -14 Q ${64 + kibasSorban} 24 ${50 + kibasSorban * 1.4} 76 L ${32 + kibasSorban * 1.2} 72 Q ${44 + kibasSorban * 0.7} 26 18 -6 Z`}
              fill={c.sorban}
              opacity={0.92}
            />
          ) : null}
          {/* Kontur hijab penuh (untuk varian wanita_hijab) */}
          {c.hijab ? (
            <path d="M -52 14 Q -58 -52 0 -58 Q 58 -52 52 14 Q 60 66 36 84 L -36 84 Q -60 66 -52 14 Z" fill={c.sorban} />
          ) : null}
          {/* Kepala polos mulus: STRICTLY ZERO EYES, ZERO NOSE, ZERO MOUTH */}
          <ellipse cx={0} cy={-2} rx={38} ry={42} fill={c.kulit} />
          {/* Bayangan halus pipi/dagu tanpa fitur wajah */}
          <path d="M -34 12 Q 0 42 34 12 Q 0 50 -34 12 Z" fill="rgba(0,0,0,0.08)" />
          {/* Janggut halus untuk pria dewasa/tetua (tetap tanpa mulut/hidung/mata) */}
          {c.janggut ? (
            <path d="M -30 14 Q -24 44 0 48 Q 24 44 30 14 Q 14 28 0 28 Q -14 28 -30 14 Z" fill={c.janggut} />
          ) : null}
          {/* Sorban / kerudung atas */}
          {c.hijab ? (
            <path d="M -44 -14 Q -36 -54 0 -56 Q 36 -54 44 -14 Q 0 -30 -44 -14 Z" fill={c.sorban} />
          ) : (
            <g>
              <path d="M -48 -14 Q -44 -64 0 -66 Q 44 -64 48 -14 Q 0 -34 -48 -14 Z" fill={c.sorban} />
              <path d="M -44 -28 Q 0 -46 44 -28" fill="none" stroke="rgba(0,0,0,0.12)" strokeWidth={4} strokeLinecap="round" />
              <path d="M -40 -42 Q 0 -56 40 -42" fill="none" stroke={theme.colors.hero} strokeWidth={3} opacity={0.55} strokeLinecap="round" />
            </g>
          )}
        </g>

        {/* Lengan depan */}
        <Lengan
          bx={44}
          by={duduk ? -156 : -196}
          sudutAtas={bahuR}
          sudutBawah={sikuR}
          warna={c.jubah}
          warnaGelap={c.jubahGelap}
          kulit={c.kulit}
        />

        {/* Kilau / aura halus untuk pose berbagi & berdoa */}
        {pose === "berdoa" ? (
          <g transform={`translate(0 ${-238 + napas * 4})`} opacity={0.55 + 0.35 * Math.sin(frame / 10)}>
            <circle r={18} fill={theme.colors.hero} opacity={0.22} />
            <path d="M 0 -16 L 4 -4 L 16 0 L 4 4 L 0 16 L -4 4 L -16 0 L -4 -4 Z" fill={theme.colors.hero} />
          </g>
        ) : null}

        {pose === "berbagi" ? (
          <g transform={`translate(94 ${-134 + Math.sin(frame / 10) * 5})`}>
            <circle r={16} fill={theme.colors.hero} opacity={0.24} />
            <circle r={9} fill={theme.colors.hero} />
          </g>
        ) : null}

        {/* Garis gerak ekspresif untuk pose panik/takut (bukan wajah) */}
        {gelisah ? (
          <g transform="translate(0 -322)" stroke={theme.colors.hero} strokeWidth={6} strokeLinecap="round" opacity={denyut}>
            <line x1={-66} y1={-4} x2={-84} y2={-30} />
            <line x1={0} y1={-16} x2={0} y2={-48} />
            <line x1={66} y1={-4} x2={84} y2={-30} />
          </g>
        ) : null}
      </g>
    </g>
  );
};
