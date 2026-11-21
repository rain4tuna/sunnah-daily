import React from "react";
import { interpolate, spring, useVideoConfig } from "remotion";
import { theme } from "./theme";

/**
 * PropertiKaya — 12 properti animasi Islami & Sirah berlapis (depth, highlight, gerak organik).
 * 100% benda/properti (tanpa makhluk bernyawa, tanpa alat musik, tanpa simbol agama lain).
 */

export const JENIS_PROPERTI = [
  "mushaf_terbuka",
  "lentera_emas",
  "kendi_air",
  "kurma_piring",
  "koin_sedekah",
  "gulungan_surat",
  "jam_pasir",
  "pintu_cahaya",
  "pelita_malam",
  "kompas_kiblat",
  "timbangan_adil",
  "tasbih_kayu",
] as const;

export type JenisProperti = (typeof JENIS_PROPERTI)[number];

type Props = {
  jenis: JenisProperti;
  x: number;
  y: number;
  scale?: number;
  frame: number;
  delay?: number;
};

export const PropertiKaya: React.FC<Props> = ({ jenis, x, y, scale = 1, frame, delay = 8 }) => {
  const { fps } = useVideoConfig();
  const p = spring({ frame: frame - delay, fps, config: theme.spring.bouncy });
  if (frame < delay) return null;
  const apung = Math.sin((frame - delay) / 18) * 6;
  const ayun = Math.sin((frame - delay) / 24) * 3.2;
  const nyala = 0.78 + 0.22 * Math.sin(frame / 7);

  let isi: React.ReactNode = null;

  switch (jenis) {
    case "mushaf_terbuka":
      isi = (
        <g>
          <circle r={64} fill={theme.colors.hero} opacity={0.14 * nyala} />
          <path d="M -56 -14 Q -28 -30 0 -12 L 0 26 Q -28 8 -56 24 Z" fill="#1C5E53" />
          <path d="M 56 -14 Q 28 -30 0 -12 L 0 26 Q 28 8 56 24 Z" fill="#164A42" />
          <path d="M -50 -20 Q -25 -34 0 -18 L 0 18 Q -25 2 -50 16 Z" fill="#F5EDD9" />
          <path d="M 50 -20 Q 25 -34 0 -18 L 0 18 Q 25 2 50 16 Z" fill="#E8DEC6" />
          {[-10, -2, 6].map((ly) => (
            <g key={ly} stroke="#B9A682" strokeWidth={2.5} strokeLinecap="round">
              <line x1={-40} y1={ly} x2={-10} y2={ly + 3} />
              <line x1={10} y1={ly + 3} x2={40} y2={ly} />
            </g>
          ))}
        </g>
      );
      break;

    case "lentera_emas":
      isi = (
        <g transform={`rotate(${ayun * 1.4} 0 -54)`}>
          <circle cy={4} r={66} fill={theme.colors.hero} opacity={0.18 * nyala} />
          <line x1={0} y1={-66} x2={0} y2={-42} stroke={theme.colors.hero} strokeWidth={4} />
          <path d="M -18 -42 Q 0 -58 18 -42 Z" fill={theme.colors.hero} />
          <path d="M -26 -38 L -34 32 L 34 32 L 26 -38 Z" fill="#16282D" stroke={theme.colors.hero} strokeWidth={5} strokeLinejoin="round" />
          <path d="M -18 -30 L -24 24 L 24 24 L 18 -30 Z" fill="#FFE6A3" opacity={0.92 * nyala} />
          <rect x={-38} y={32} width={76} height={11} rx={5} fill={theme.colors.hero} />
        </g>
      );
      break;

    case "kendi_air":
      isi = (
        <g transform={`rotate(${-14 + Math.sin(frame / 16) * 5})`}>
          <ellipse cx={-6} cy={8} rx={36} ry={40} fill="#9A623F" />
          <ellipse cx={-16} cy={-2} rx={12} ry={22} fill="#BA7E57" opacity={0.55} />
          <rect x={-16} y={-44} width={22} height={22} rx={6} fill="#875232" />
          <path d="M 24 -18 Q 52 -16 42 14 Q 34 26 22 22" fill="none" stroke="#875232" strokeWidth={8} strokeLinecap="round" />
          <path d="M 38 -36 Q 52 -14 48 18" stroke="#9AD9EC" strokeWidth={6} strokeLinecap="round" fill="none" opacity={0.85} />
        </g>
      );
      break;

    case "kurma_piring":
      isi = (
        <g>
          <ellipse cy={20} rx={58} ry={16} fill="#E7DBC4" />
          <ellipse cy={16} rx={44} ry={10} fill="#D2C3A8" />
          {[[-22, 6], [0, 2], [22, 6], [-11, -10], [12, -10], [0, -22]].map(([cx, cy], i) => (
            <ellipse key={i} cx={cx} cy={cy} rx={13} ry={8} fill={i % 2 ? "#5F2E1E" : "#783B22"} transform={`rotate(${(i - 2) * 10} ${cx} ${cy})`} />
          ))}
        </g>
      );
      break;

    case "koin_sedekah":
      isi = (
        <g>
          {[0, 1, 2].map((i) => {
            const dy = ((frame + i * 12) % 36) / 36;
            return (
              <g key={i} transform={`translate(${(i - 1) * 20} ${-40 + dy * 48})`} opacity={1 - dy * 0.4}>
                <ellipse rx={14} ry={14 * Math.max(0.25, Math.abs(Math.cos(frame / 6 + i)))} fill={theme.colors.hero} />
                <ellipse rx={8} ry={8 * Math.max(0.25, Math.abs(Math.cos(frame / 6 + i)))} fill="#FCE1A2" />
              </g>
            );
          })}
          <path d="M -46 12 Q -46 44 0 46 Q 46 44 46 12 Z" fill="#8C5939" />
          <ellipse cy={12} rx={46} ry={10} fill="#5C3924" />
        </g>
      );
      break;

    case "gulungan_surat":
      isi = (
        <g>
          <rect x={-44} y={-34} width={88} height={68} rx={10} fill="#F2E6CC" stroke="#C8B185" strokeWidth={3} />
          <rect x={-52} y={-40} width={104} height={14} rx={7} fill="#B8874A" />
          <rect x={-52} y={26} width={104} height={14} rx={7} fill="#B8874A" />
          {[-14, -2, 10].map((ly) => (
            <line key={ly} x1={-28} y1={ly} x2={28} y2={ly} stroke="#8D7553" strokeWidth={4} strokeLinecap="round" />
          ))}
          <circle cx={22} cy={14} r={10} fill="#B83C34" />
        </g>
      );
      break;

    case "jam_pasir": {
      const pasir = (frame % 60) / 60;
      isi = (
        <g>
          <rect x={-34} y={-48} width={68} height={10} rx={5} fill={theme.colors.hero} />
          <rect x={-34} y={38} width={68} height={10} rx={5} fill={theme.colors.hero} />
          <path d="M -26 -38 L 26 -38 L 4 0 L 26 38 L -26 38 L -4 0 Z" fill="rgba(220,242,248,0.22)" stroke="#D9ECEF" strokeWidth={3} />
          <path d={`M ${-20 * (1 - pasir * 0.6)} ${-30 + pasir * 20} L ${20 * (1 - pasir * 0.6)} ${-30 + pasir * 20} L 0 -2 Z`} fill={theme.colors.hero} />
          <path d={`M -20 34 L 20 34 L ${6 * (1 - pasir)} ${34 - pasir * 28} L ${-6 * (1 - pasir)} ${34 - pasir * 28} Z`} fill={theme.colors.hero} />
          <line x1={0} y1={-2} x2={0} y2={32} stroke={theme.colors.hero} strokeWidth={2.5} strokeDasharray="4 4" />
        </g>
      );
      break;
    }

    case "pintu_cahaya":
      isi = (
        <g>
          <path d="M -36 44 L -36 -18 Q 0 -54 36 -18 L 36 44 Z" fill="#1C3036" stroke={theme.colors.hero} strokeWidth={4} />
          <path d="M -28 40 L -28 -14 Q 0 -42 28 -14 L 28 40 Z" fill="#FFE6A8" opacity={0.85 * nyala} />
          <path d="M -28 40 L -28 -14 Q -10 -32 -4 -18 L -4 40 Z" fill="#7D5230" />
        </g>
      );
      break;

    case "pelita_malam":
      isi = (
        <g>
          <circle cy={-18} r={46} fill={theme.colors.hero} opacity={0.2 * nyala} />
          <path d="M -38 22 Q 0 42 38 22 L 46 8 L -46 8 Z" fill="#B88342" />
          <path d={`M 0 -4 Q -14 -24 0 ${-48 * nyala} Q 14 -24 0 -4 Z`} fill={theme.colors.hero} />
          <path d={`M 0 -4 Q -7 -16 0 ${-30 * nyala} Q 7 -16 0 -4 Z`} fill="#FFF5D4" />
        </g>
      );
      break;

    case "kompas_kiblat":
      isi = (
        <g>
          <circle r={44} fill="#172A30" stroke={theme.colors.hero} strokeWidth={6} />
          <circle r={34} fill="none" stroke="rgba(246,241,231,0.28)" strokeWidth={2} />
          <g transform={`rotate(${Math.sin(frame / 16) * 14 - 28})`}>
            <polygon points="0,-28 9,0 0,6 -9,0" fill={theme.colors.hero} />
            <polygon points="0,28 9,0 0,-6 -9,0" fill="#E8E1D3" opacity={0.75} />
          </g>
          <circle r={5} fill="#FFF7DF" />
        </g>
      );
      break;

    case "timbangan_adil": {
      const miring = Math.sin(frame / 20) * 8;
      isi = (
        <g>
          <rect x={-5} y={-40} width={10} height={80} rx={5} fill={theme.colors.hero} />
          <rect x={-30} y={36} width={60} height={10} rx={5} fill={theme.colors.hero} />
          <g transform={`translate(0 -32) rotate(${miring})`}>
            <rect x={-46} y={-4} width={92} height={8} rx={4} fill={theme.colors.hero} />
            <line x1={-38} y1={4} x2={-38} y2={30} stroke="#E9DFCA" strokeWidth={2.5} />
            <line x1={38} y1={4} x2={38} y2={30} stroke="#E9DFCA" strokeWidth={2.5} />
            <path d="M -54 30 Q -38 46 -22 30 Z" fill={theme.colors.hero} />
            <path d="M 22 30 Q 38 46 54 30 Z" fill={theme.colors.hero} />
          </g>
        </g>
      );
      break;
    }

    case "tasbih_kayu":
      isi = (
        <g transform={`rotate(${ayun})`}>
          {Array.from({ length: 12 }).map((_, i) => {
            const a = (i / 12) * Math.PI * 2;
            return <circle key={i} cx={Math.cos(a) * 32} cy={Math.sin(a) * 36} r={7.5} fill={i === 0 ? theme.colors.hero : "#A46F44"} stroke="#5D3A21" strokeWidth={2} />;
          })}
          <path d="M 32 0 L 48 16 M 32 0 L 52 8 M 32 0 L 46 24" stroke={theme.colors.hero} strokeWidth={3} strokeLinecap="round" />
        </g>
      );
      break;
  }

  return (
    <g
      transform={`translate(${x} ${y + apung}) scale(${scale * p}) rotate(${interpolate(p, [0, 1], [-18, 0])})`}
      opacity={p}
    >
      {isi}
    </g>
  );
};
