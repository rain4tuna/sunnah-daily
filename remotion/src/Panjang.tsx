import React from "react";
import { AbsoluteFill, Sequence, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { theme } from "./theme";
import { Bintang, Entrance, Garis, Karaoke, Scene, WordReveal, clamp } from "./Motion";
import { Ilustrasi } from "./Ilustrasi";
import { DenganStiker } from "./Stiker";
import { Grade, Grain, Latar, Vignette } from "./Layers";
import { Segmen } from "./Scenes";

// Video YouTube panjang 16:9 (1920x1080): satu episode Sirah utuh, tiap kisah jadi satu "pelajaran" (bab).
// Babak sama dengan Shorts (poin, dalil, faedah) ditambah pembuka episode dan pembatas bab.
// Aturan gambar sama: Nabi, sahabat, dan malaikat tidak pernah digambar (tokoh sudah dikosongkan di Python).

export const W = 1920, H = 1080;
const FPS = 30;
const SISI = 120;
const ATAS = 150, BAWAH = 110; // ruang kepala & bilah bab

export type SegmenPanjang = Omit<Segmen, "jenis"> & {
  jenis: Segmen["jenis"] | "pembuka" | "bab";
  bab?: number; kajian?: string;
};
export type DataPanjang = {
  kicker: string; handle?: string; durasi: number; frame?: number; judul: string;
  bab: { no: number; judul: string; mulai: number }[]; segmen: SegmenPanjang[];
};

const display: React.CSSProperties = { fontFamily: theme.font.display, fontWeight: 600, letterSpacing: "-0.02em", color: theme.colors.text };
const badan: React.CSSProperties = { fontFamily: theme.font.body, fontWeight: 500, color: theme.colors.text };
const area: React.CSSProperties = { position: "absolute", left: SISI, right: SISI, top: ATAS, bottom: BAWAH,
  display: "flex", alignItems: "center" };

const useUcap = (s: SegmenPanjang) => {
  const { fps } = useVideoConfig();
  return { dari: Math.round((s.ucapMulai - s.mulai) * fps), sampai: Math.round((s.ucapAkhir - s.mulai) * fps) };
};

/** Dua kolom: ilustrasi (dengan stiker) di satu sisi, teks di sisi lain. */
const DuaKolom: React.FC<{ s: SegmenPanjang; kanan?: boolean; children: React.ReactNode; nomor?: React.ReactNode }> = ({
  s, kanan, children, nomor,
}) => (
  <div style={{ ...area, flexDirection: kanan ? "row-reverse" : "row", gap: 96 }}>
    <div style={{ flex: "0 0 820px", display: "flex", justifyContent: "center" }}>
      {s.ilustrasi ? (
        <DenganStiker stiker={s.stiker} sudut={kanan ? ["kiriAtas", "kiriBawah", "kananBawah"] : ["kananAtas", "kananBawah", "kiriBawah"]}>
          <Ilustrasi jenis={s.ilustrasi} tokoh={s.tokoh} tinggi={640} lebar={820} delay={1} />
          {nomor}
        </DenganStiker>
      ) : <Bintang ukuran={420} delay={2} />}
    </div>
    <div style={{ flex: 1, display: "flex", flexDirection: "column", justifyContent: "center" }}>{children}</div>
  </div>
);

const Pembuka: React.FC<{ s: SegmenPanjang }> = ({ s }) => {
  const { dari, sampai } = useUcap(s);
  return (
    <Scene>
      <div style={{ ...area, flexDirection: "column", justifyContent: "center", textAlign: "center" }}>
        <Bintang ukuran={170} delay={2} />
        <WordReveal text={s.judul ?? ""} delay={10} per={4}
          style={{ ...display, fontSize: 92, lineHeight: 1.1, justifyContent: "center", marginTop: 40, maxWidth: 1500 }} />
        <Entrance delay={26} style={{ marginTop: 30 }}>
          <div style={{ ...badan, fontSize: 34, color: theme.colors.hero, letterSpacing: "0.04em" }}>{s.kajian}</div>
        </Entrance>
        <Entrance delay={36} style={{ marginTop: 46, maxWidth: 1380 }}>
          <Karaoke text={s.narasi ?? ""} dari={dari} sampai={sampai}
            style={{ ...badan, fontSize: 40, lineHeight: 1.5, justifyContent: "center" }} />
        </Entrance>
      </div>
    </Scene>
  );
};

const Bab: React.FC<{ s: SegmenPanjang }> = ({ s }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const { dari, sampai } = useUcap(s);
  const p = spring({ frame: frame - 4, fps, config: theme.spring.bouncy });
  return (
    <Scene>
      <DuaKolom s={s} kanan>
        <div style={{ ...display, fontSize: 210, lineHeight: 0.9, color: "transparent", WebkitTextStroke: `4px ${theme.colors.hero}`,
          opacity: p, fontVariantNumeric: "tabular-nums", transform: `translateX(${interpolate(p, [0, 1], [-60, 0])}px)` }}>
          {String(s.bab ?? 1).padStart(2, "0")}
        </div>
        <Entrance delay={8} style={{ marginTop: 18 }}>
          <div style={{ ...badan, fontWeight: 600, fontSize: 30, letterSpacing: "0.24em", color: theme.colors.soft }}>PELAJARAN KE-{s.bab}</div>
        </Entrance>
        <WordReveal text={s.judul ?? ""} delay={14} per={4} sorot={(s.judul ?? "").split(" ").length - 1}
          style={{ ...display, fontSize: 74, lineHeight: 1.1, marginTop: 26 }} />
        <Garis delay={26} lebar={200} style={{ marginTop: 34, marginBottom: 34 }} />
        <Entrance delay={30}>
          <Karaoke text={s.narasi ?? ""} dari={dari} sampai={sampai} style={{ ...badan, fontSize: 40, lineHeight: 1.5 }} />
        </Entrance>
      </DuaKolom>
    </Scene>
  );
};

const Poin: React.FC<{ s: SegmenPanjang }> = ({ s }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const { dari, sampai } = useUcap(s);
  const p = spring({ frame: frame - 8, fps, config: theme.spring.bouncy });
  const nomor = (
    <div style={{ ...display, position: "absolute", left: 30, top: 18, fontSize: 120, lineHeight: 1, color: "transparent",
      WebkitTextStroke: `3px ${theme.colors.hero}`, opacity: p, fontVariantNumeric: "tabular-nums",
      transform: `scale(${interpolate(p, [0, 1], [0.8, 1])})`, transformOrigin: "left top" }}>
      {String(s.no).padStart(2, "0")}
    </div>
  );
  return (
    <Scene>
      <DuaKolom s={s} kanan={(s.no ?? 1) % 2 === 0} nomor={nomor}>
        <WordReveal text={s.label ?? ""} delay={12} per={4} style={{ ...display, fontSize: 70, lineHeight: 1.12 }} />
        <Garis delay={22} lebar={180} style={{ marginTop: 32, marginBottom: 36 }} />
        <Entrance delay={26}>
          <Karaoke text={s.narasi ?? ""} dari={dari} sampai={sampai} style={{ ...badan, fontSize: 44, lineHeight: 1.5 }} />
        </Entrance>
      </DuaKolom>
    </Scene>
  );
};

const Dalil: React.FC<{ s: SegmenPanjang }> = ({ s }) => {
  const frame = useCurrentFrame();
  const { dari, sampai } = useUcap(s);
  const garis = interpolate(frame, [30, 62], [0, 1], { ...clamp, easing: theme.ease.out });
  const apung = Math.sin(frame / 30) * 4;
  return (
    <Scene>
      <div style={{ ...area, flexDirection: "column", justifyContent: "center" }}>
        <Entrance delay={2} y={60}>
          <div style={{ transform: `translateY(${apung}px)`, width: 1500, borderRadius: 40, padding: "48px 72px 46px",
            background: theme.colors.surface, border: `2px solid ${theme.colors.line}`, boxShadow: "0 50px 90px -30px rgba(0,0,0,0.6)" }}>
            <Entrance delay={8}>
              <div style={{ ...badan, fontWeight: 600, fontSize: 28, letterSpacing: "0.2em", color: theme.colors.soft, textAlign: "center" }}>
                {s.label}
              </div>
            </Entrance>
            <Entrance delay={14}>
              <div dir="rtl" lang="ar" style={{ fontFamily: theme.font.arab, fontSize: 60, lineHeight: 1.8, color: theme.colors.text,
                textAlign: "center", marginTop: 18 }}>
                {s.arab}
              </div>
            </Entrance>
            <div style={{ height: 3, margin: "26px auto 30px", width: `${garis * 40}%`, background: theme.colors.line, borderRadius: 3 }} />
            <Entrance delay={34}>
              <Karaoke text={s.terjemah ?? ""} dari={dari} sampai={sampai}
                style={{ ...badan, fontSize: 38, lineHeight: 1.5, justifyContent: "center", textAlign: "center" }} />
            </Entrance>
          </div>
        </Entrance>
        <Entrance delay={46} style={{ marginTop: 36 }}>
          <div style={{ ...badan, fontWeight: 600, fontSize: 32, color: theme.colors.bg, background: theme.colors.hero,
            padding: "12px 34px", borderRadius: 999, boxShadow: `0 0 60px ${theme.colors.hero}55` }}>
            {s.sumber}{s.derajat ? ` · ${s.derajat[0].toUpperCase()}${s.derajat.slice(1)}` : ""}
          </div>
        </Entrance>
      </div>
    </Scene>
  );
};

const Faedah: React.FC<{ s: SegmenPanjang }> = ({ s }) => {
  const { dari, sampai } = useUcap(s);
  return (
    <Scene>
      <DuaKolom s={s}>
        <Entrance delay={8}>
          <div style={{ display: "flex", alignItems: "center", gap: 24 }}>
            <Garis delay={14} lebar={80} />
            <div style={{ ...badan, fontWeight: 600, fontSize: 32, letterSpacing: "0.24em", color: theme.colors.soft }}>FAEDAH</div>
          </div>
        </Entrance>
        <Entrance delay={14} style={{ marginTop: 34 }}>
          <Karaoke text={s.narasi ?? ""} dari={dari} sampai={sampai} style={{ ...display, fontSize: 60, lineHeight: 1.24 }} />
        </Entrance>
      </DuaKolom>
    </Scene>
  );
};

const Penutup: React.FC<{ s: SegmenPanjang }> = ({ s }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const p = spring({ frame: frame - 4, fps, config: theme.spring.bouncy });
  return (
    <AbsoluteFill>
      <div style={{ ...area, flexDirection: "column", justifyContent: "center", textAlign: "center" }}>
        <div style={{ transform: `scale(${p})`, filter: `drop-shadow(0 0 50px ${theme.colors.hero}66)` }}>
          <Bintang ukuran={190} delay={0} />
        </div>
        <WordReveal text="Sunnah Daily" delay={12} per={5} style={{ ...display, fontSize: 120, lineHeight: 1, justifyContent: "center", marginTop: 34 }} />
        <Entrance delay={26} style={{ marginTop: 36 }}>
          <div style={{ ...badan, fontSize: 44, lineHeight: 1.4 }}>{s.ajakan}</div>
        </Entrance>
        <Entrance delay={38} style={{ marginTop: 60 }}>
          <div style={{ ...badan, fontSize: 30, lineHeight: 1.55, color: theme.colors.soft }}>
            {s.kredit}<br />{s.ustadz}
          </div>
        </Entrance>
      </div>
    </AbsoluteFill>
  );
};

const ADEGAN = { pembuka: Pembuka, bab: Bab, hook: Bab, poin: Poin, dalil: Dalil, faedah: Faedah, penutup: Penutup } as const;

/** Kepala: label seri & handle di atas, judul bab yang sedang berjalan di bawahnya. */
export const Kepala: React.FC<{ kicker: string; handle: string; bab: DataPanjang["bab"] }> = ({ kicker, handle, bab }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const p = spring({ frame: frame - 6, fps, config: theme.spring.smooth });
  const t = frame / fps;
  const kini = [...bab].reverse().find((b) => t >= b.mulai);
  return (
    <div style={{ position: "absolute", top: 54, left: SISI, right: SISI, opacity: p, display: "flex", alignItems: "center", gap: 22 }}>
      <div style={{ fontFamily: theme.font.body, fontWeight: 600, fontSize: 24, letterSpacing: "0.16em", color: theme.colors.text,
        padding: "9px 22px", borderRadius: 999, border: `2px solid ${theme.colors.line}`, background: theme.colors.surface }}>
        {kicker}
      </div>
      {kini ? (
        <div style={{ fontFamily: theme.font.body, fontWeight: 500, fontSize: 26, color: theme.colors.soft, whiteSpace: "nowrap",
          overflow: "hidden", textOverflow: "ellipsis", maxWidth: 1100 }}>
          {String(kini.no).padStart(2, "0")} · {kini.judul}
        </div>
      ) : null}
      <div style={{ marginLeft: "auto", fontFamily: theme.font.body, fontWeight: 600, fontSize: 28, color: theme.colors.soft }}>{handle}</div>
    </div>
  );
};

/** Bilah bawah: satu ruas per bab, terisi sesuai waktu berjalan. */
export const BilahBab: React.FC<{ bab: DataPanjang["bab"]; total: number }> = ({ bab, total }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const awal = bab.length ? bab[0].mulai : 0;
  const ruas = bab.map((b, i) => [b.mulai, i + 1 < bab.length ? bab[i + 1].mulai : total] as const);
  return (
    <div style={{ position: "absolute", left: SISI, right: SISI, bottom: 48, display: "flex", gap: 10 }}>
      {awal > 0 ? <Ruas a={0} b={awal} t={t} total={total} /> : null}
      {ruas.map(([a, b], i) => <Ruas key={i} a={a} b={b} t={t} total={total} />)}
    </div>
  );
};
const Ruas: React.FC<{ a: number; b: number; t: number; total: number }> = ({ a, b, t, total }) => (
  <div style={{ flex: (b - a) / total, height: 6, borderRadius: 6, background: "rgba(246,241,231,0.16)", overflow: "hidden" }}>
    <div style={{ width: `${interpolate(t, [a, b], [0, 100], clamp)}%`, height: "100%", background: theme.colors.hero, opacity: 0.9 }} />
  </div>
);

export const VideoPanjang: React.FC<DataPanjang> = ({ kicker, handle, durasi, bab, segmen }) => {
  const batas = segmen.map((s) => Math.round(s.mulai * FPS));
  return (
    <AbsoluteFill>
      <Latar />
      {segmen.map((s, i) => {
        const Adegan = ADEGAN[s.jenis];
        const akhir = i + 1 < segmen.length ? batas[i + 1] : Math.round(s.akhir * FPS);
        return (
          <Sequence key={i} from={batas[i]} durationInFrames={Math.max(1, akhir - batas[i])}>
            <Adegan s={s} />
          </Sequence>
        );
      })}
      <Kepala kicker={kicker} handle={handle ?? "@sun_nahdaily"} bab={bab} />
      <BilahBab bab={bab} total={durasi} />
      <Grade />
      <Grain />
      <Vignette />
    </AbsoluteFill>
  );
};
