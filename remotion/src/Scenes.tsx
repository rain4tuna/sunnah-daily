import React from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { theme } from "./theme";
import { Bintang, Entrance, Garis, Karaoke, Scene, WordReveal, clamp } from "./Motion";
import { Ilustrasi, JenisIlustrasi, Pose } from "./Ilustrasi";

export type Segmen = {
  jenis: "hook" | "poin" | "dalil" | "faedah" | "penutup";
  mulai: number; akhir: number; ucapMulai: number; ucapAkhir: number;
  judul?: string; narasi?: string; no?: number; label?: string;
  arab?: string; terjemah?: string; sumber?: string; derajat?: string;
  ajakan?: string; kredit?: string; ustadz?: string;
  ilustrasi?: JenisIlustrasi; tokoh?: Pose | "";
};

const sisi = theme.safe.side;
const isi: React.CSSProperties = { position: "absolute", left: sisi, right: sisi, top: theme.safe.top, bottom: 1920 - theme.safe.bottom,
  display: "flex", flexDirection: "column", justifyContent: "center" };
const display: React.CSSProperties = { fontFamily: theme.font.display, fontWeight: 600, letterSpacing: "-0.02em", color: theme.colors.text };
const badan: React.CSSProperties = { fontFamily: theme.font.body, fontWeight: 500, color: theme.colors.text };

/** Frame relatif adegan untuk awal & akhir suara. */
const useUcap = (s: Segmen) => {
  const { fps } = useVideoConfig();
  return { dari: Math.round((s.ucapMulai - s.mulai) * fps), sampai: Math.round((s.ucapAkhir - s.mulai) * fps) };
};

export const Hook: React.FC<{ s: Segmen }> = ({ s }) => {
  const { dari, sampai } = useUcap(s);
  const kata = (s.judul ?? "").split(" ");
  return (
    <Scene>
      <div style={{ ...isi, alignItems: "center", textAlign: "center" }}>
        {s.ilustrasi ? <Ilustrasi jenis={s.ilustrasi} tokoh={s.tokoh} tinggi={500} delay={1} /> : <Bintang ukuran={230} delay={2} />}
        <WordReveal text={s.judul ?? ""} delay={10} per={4} sorot={kata.length - 1}
          style={{ ...display, fontSize: 100, lineHeight: 1.08, justifyContent: "center", marginTop: 52 }} />
        <Entrance delay={28} style={{ marginTop: 44 }}>
          <Karaoke text={s.narasi ?? ""} dari={dari} sampai={sampai}
            style={{ ...badan, fontSize: 46, lineHeight: 1.45, justifyContent: "center" }} />
        </Entrance>
      </div>
    </Scene>
  );
};

export const Poin: React.FC<{ s: Segmen }> = ({ s }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const { dari, sampai } = useUcap(s);
  const p = spring({ frame: frame - 8, fps, config: theme.spring.bouncy });
  return (
    <Scene>
      <div style={isi}>
        <div style={{ position: "relative" }}>
          <Ilustrasi jenis={s.ilustrasi} tokoh={s.tokoh} tinggi={530} delay={1} />
          <div style={{ ...display, position: "absolute", left: 30, top: 18, fontSize: 132, lineHeight: 1, color: "transparent",
            WebkitTextStroke: `3px ${theme.colors.hero}`, opacity: p, fontVariantNumeric: "tabular-nums",
            transform: `translateX(${interpolate(p, [0, 1], [-50, 0])}px) scale(${interpolate(p, [0, 1], [0.8, 1])})`, transformOrigin: "left top" }}>
            {String(s.no).padStart(2, "0")}
          </div>
        </div>
        <WordReveal text={s.label ?? ""} delay={12} per={4} style={{ ...display, fontSize: 80, lineHeight: 1.1, marginTop: 50 }} />
        <Garis delay={22} lebar={190} style={{ marginTop: 34, marginBottom: 38 }} />
        <Entrance delay={26}>
          <Karaoke text={s.narasi ?? ""} dari={dari} sampai={sampai} style={{ ...badan, fontSize: 48, lineHeight: 1.48 }} />
        </Entrance>
      </div>
    </Scene>
  );
};

export const Dalil: React.FC<{ s: Segmen }> = ({ s }) => {
  const frame = useCurrentFrame();
  const { dari, sampai } = useUcap(s);
  const garis = interpolate(frame, [30, 62], [0, 1], { ...clamp, easing: theme.ease.out });
  const apung = Math.sin(frame / 30) * 4;
  return (
    <Scene>
      <div style={{ ...isi, alignItems: "stretch" }}>
        <Entrance delay={2} y={70} style={{ transform: undefined }}>
          <div style={{ transform: `translateY(${apung}px)`, borderRadius: 44, padding: "62px 56px 58px", background: theme.colors.surface,
            border: `2px solid ${theme.colors.line}`, boxShadow: "0 50px 90px -30px rgba(0,0,0,0.6)" }}>
            <Entrance delay={8}>
              <div style={{ ...badan, fontWeight: 600, fontSize: 30, letterSpacing: "0.2em", color: theme.colors.soft, textAlign: "center" }}>
                {s.label}
              </div>
            </Entrance>
            <Entrance delay={14}>
              <div dir="rtl" lang="ar" style={{ fontFamily: theme.font.arab, fontSize: 76, lineHeight: 1.95, color: theme.colors.text,
                textAlign: "center", marginTop: 26 }}>
                {s.arab}
              </div>
            </Entrance>
            <div style={{ height: 3, margin: "34px auto 40px", width: `${garis * 46}%`, background: theme.colors.line, borderRadius: 3 }} />
            <Entrance delay={34}>
              <Karaoke text={s.terjemah ?? ""} dari={dari} sampai={sampai}
                style={{ ...badan, fontSize: 45, lineHeight: 1.5, justifyContent: "center", textAlign: "center" }} />
            </Entrance>
          </div>
        </Entrance>
        <Entrance delay={46} style={{ alignSelf: "center", marginTop: 46 }}>
          <div style={{ ...badan, fontWeight: 600, fontSize: 36, color: theme.colors.bg, background: theme.colors.hero,
            padding: "14px 36px", borderRadius: 999, boxShadow: `0 0 60px ${theme.colors.hero}55` }}>
            {s.sumber}{s.derajat ? ` · ${s.derajat[0].toUpperCase()}${s.derajat.slice(1)}` : ""}
          </div>
        </Entrance>
      </div>
    </Scene>
  );
};

export const Faedah: React.FC<{ s: Segmen }> = ({ s }) => {
  const { dari, sampai } = useUcap(s);
  return (
    <Scene>
      <div style={{ ...isi, alignItems: "center", textAlign: "center" }}>
        <Ilustrasi jenis={s.ilustrasi} tokoh={s.tokoh} tinggi={460} delay={1} />
        <Entrance delay={8} style={{ marginTop: 52 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 26 }}>
            <Garis delay={14} lebar={90} />
            <div style={{ ...badan, fontWeight: 600, fontSize: 34, letterSpacing: "0.24em", color: theme.colors.soft }}>FAEDAH</div>
            <Garis delay={14} lebar={90} />
          </div>
        </Entrance>
        <Entrance delay={14} style={{ marginTop: 40 }}>
          <Karaoke text={s.narasi ?? ""} dari={dari} sampai={sampai}
            style={{ ...display, fontSize: 70, lineHeight: 1.22, justifyContent: "center" }} />
        </Entrance>
      </div>
    </Scene>
  );
};

export const Penutup: React.FC<{ s: Segmen }> = ({ s }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const p = spring({ frame: frame - 4, fps, config: theme.spring.bouncy });
  return (
    <AbsoluteFill>
      <div style={{ ...isi, alignItems: "center", textAlign: "center" }}>
        <div style={{ transform: `scale(${p})`, filter: `drop-shadow(0 0 50px ${theme.colors.hero}66)` }}>
          <Bintang ukuran={250} delay={0} />
        </div>
        <WordReveal text="Sunnah Daily" delay={12} per={5} style={{ ...display, fontSize: 132, lineHeight: 1, justifyContent: "center", marginTop: 40 }} />
        <Entrance delay={26} style={{ marginTop: 44 }}>
          <div style={{ ...badan, fontSize: 50, lineHeight: 1.4 }}>{s.ajakan}</div>
        </Entrance>
        <Entrance delay={38} style={{ marginTop: 90 }}>
          <div style={{ ...badan, fontSize: 31, lineHeight: 1.55, color: theme.colors.soft }}>
            {s.kredit}<br />{s.ustadz}
          </div>
        </Entrance>
      </div>
    </AbsoluteFill>
  );
};
