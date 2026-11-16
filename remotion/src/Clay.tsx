import React from "react";
import {
  AbsoluteFill, Img, OffthreadVideo, Sequence, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig,
} from "remotion";
import { theme } from "./theme";
import { Bintang, Entrance, Karaoke, WordReveal, clamp } from "./Motion";
import { BilahBab, DataPanjang, H, Kepala, SegmenPanjang, W } from "./Panjang";

// Video panjang 16:9 gaya clay/stop-motion: latar diorama (gambar atau klip Flow), tokoh & properti potongan PNG
// yang digerakkan di sini, teks narasi di panel bawah. Aset ada di public_panjang/aset (render dengan --public-dir=public_panjang; dipilih Python: adegan_clay.py).
// ATURAN: Nabi ﷺ, nabi lain, dan malaikat tidak pernah tampil. Tokoh lain tanpa mata/alis (dijaga saat memilih aset).

const FPS = 30;
const TANAH = 905;          // garis kaki tokoh (di atas panel teks)
const TINGGI_TOKOH = 520;

export type TokohClay = {
  diam: string;             // pose berdiri (p01)
  jalan?: [string, string]; // dua pose jalan (p03, p04) bergantian
  x: number;                // posisi akhir (pusat, px)
  dari?: "kiri" | "kanan";  // masuk sambil berjalan dari sisi ini
  tinggi?: number;
};
export type BendaClay = { file: string; x: number; y?: number; tinggi: number; muncul?: number };
export type AdeganClay = {
  latar: string;                                  // gambar latar (selalu ada, cadangan klip)
  gerak?: { file: string; durasi: number };       // klip Flow (dipakai bila ada)
  suasana?: "siang" | "malam";
  tokoh?: TokohClay[];
  benda?: BendaClay[];
  awan?: string[];                                // elemen awan yang melayang (siang)
  bintang?: string;                               // elemen bintang yang berkelip (malam)
};
export type DataClay = DataPanjang & { adegan: AdeganClay[]; label?: Record<string, string> };

const LABEL_ID = { pelajaran: "KISAH", faedah: "PELAJARAN BUAT KITA", ajak: "Subscribe & bagikan", kuis: "KUIS!",
  suka: "Suka", subscribe: "Subscribe" };

/** Latar: klip Flow (diperlambat secukupnya, lalu beralih ke gambar) atau gambar dengan gerak kamera pelan. */
const Latar: React.FC<{ a: AdeganClay; kabur?: boolean }> = ({ a, kabur }) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const zoom = interpolate(frame, [0, durationInFrames], [1.0, 1.08], clamp);
  const geser = interpolate(frame, [0, durationInFrames], [0, -30], clamp);
  const gambar = (
    <Img src={staticFile(a.latar)} style={{ width: W, height: H, objectFit: "cover",
      transform: `scale(${zoom}) translateX(${geser}px)` }} />
  );
  let isi = gambar;
  if (a.gerak) {
    const klip = Math.round(a.gerak.durasi * FPS);
    const laju = Math.min(1, Math.max(0.6, klip / durationInFrames));
    const habis = Math.floor(klip / laju) - 2;
    const pudar = interpolate(frame, [habis - 12, habis], [1, 0], clamp);
    isi = (
      <>
        {habis < durationInFrames ? gambar : null}
        <AbsoluteFill style={{ opacity: pudar }}>
          <Sequence durationInFrames={habis}>
            <OffthreadVideo src={staticFile(a.gerak.file)} muted playbackRate={laju}
              style={{ width: W, height: H, objectFit: "cover" }} />
          </Sequence>
        </AbsoluteFill>
      </>
    );
  }
  return (
    <AbsoluteFill style={{ overflow: "hidden", filter: kabur ? "blur(14px) brightness(0.7)" : undefined,
      transform: kabur ? "scale(1.06)" : undefined }}>
      {isi}
    </AbsoluteFill>
  );
};

/** Awan melayang pelan (siang) atau bintang berkelip (malam). */
const Suasana: React.FC<{ a: AdeganClay }> = ({ a }) => {
  const frame = useCurrentFrame();
  if (a.gerak) return null;
  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      {(a.awan ?? []).map((f, i) => {
        const x = ((i * 700 + frame * (0.6 + i * 0.25)) % (W + 600)) - 300;
        return <Img key={i} src={staticFile(f)} style={{ position: "absolute", left: x, top: 60 + i * 70,
          width: 260 - i * 50, opacity: 0.92 }} />;
      })}
      {a.bintang ? [0, 1, 2, 3, 4].map((i) => (
        <Img key={i} src={staticFile(a.bintang!)} style={{ position: "absolute", left: 180 + i * 360, top: 70 + (i % 2) * 90,
          width: 46 + (i % 3) * 10, opacity: 0.55 + 0.45 * Math.abs(Math.sin(frame / 18 + i * 1.7)) }} />
      )) : null}
    </AbsoluteFill>
  );
};

/** Tokoh: masuk sambil berjalan (ganti pose A/B + memantul), lalu berdiri dan bernapas. */
const Tokoh: React.FC<{ t: TokohClay; ke: number }> = ({ t, ke }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const tinggi = t.tinggi ?? TINGGI_TOKOH;
  const lama = t.dari && t.jalan ? 54 : 0;
  const mulai = 6 + ke * 10;
  const f = frame - mulai;
  const kiri = t.dari !== "kanan";
  const awal = kiri ? -300 : W + 300;
  const x = lama ? interpolate(f, [0, lama], [awal, t.x], { ...clamp, easing: theme.ease.out }) : t.x;
  const berjalan = lama > 0 && f < lama;
  const file = berjalan ? t.jalan![Math.floor(f / 7) % 2] : t.diam;
  const pantul = berjalan ? -Math.abs(Math.sin(f / 7 * Math.PI)) * 12 : 0;
  const napas = 1 + Math.sin(frame / 20 + ke) * 0.012;
  const muncul = lama ? (f >= 0 ? 1 : 0) : spring({ frame: f, fps, config: theme.spring.smooth });
  return (
    <div style={{ position: "absolute", left: x, top: TANAH, opacity: muncul,
      transform: `translate(-50%, -100%) translateY(${pantul}px) scale(${kiri ? 1 : -1}, ${napas})`, transformOrigin: "50% 100%" }}>
      <Img src={staticFile(file)} style={{ height: tinggi, filter: "drop-shadow(0 18px 18px rgba(0,0,0,0.35))" }} />
    </div>
  );
};

/** Properti: muncul memantul lalu mengapung pelan. */
const Benda: React.FC<{ b: BendaClay; ke: number }> = ({ b, ke }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const mulai = Math.round((b.muncul ?? 0.8 + ke * 0.5) * fps);
  const p = spring({ frame: frame - mulai, fps, config: theme.spring.bouncy });
  const apung = Math.sin((frame - mulai) / 22 + ke * 2) * 6;
  return (
    <div style={{ position: "absolute", left: b.x, top: b.y ?? TANAH, transformOrigin: "50% 100%",
      transform: `translate(-50%, -100%) translateY(${apung}px) scale(${p}) rotate(${interpolate(p, [0, 1], [-12, 0])}deg)` }}>
      <Img src={staticFile(b.file)} style={{ height: b.tinggi, filter: "drop-shadow(0 14px 14px rgba(0,0,0,0.35))" }} />
    </div>
  );
};

const Panggung: React.FC<{ a: AdeganClay }> = ({ a }) => (
  <>
    <Latar a={a} />
    <Suasana a={a} />
    {(a.benda ?? []).map((b, i) => <Benda key={`b${i}`} b={b} ke={i} />)}
    {(a.tokoh ?? []).map((t, i) => <Tokoh key={`t${i}`} t={t} ke={i} />)}
  </>
);

/** Panel teks narasi di bawah: menyala mengikuti suara. */
const Teks: React.FC<{ s: SegmenPanjang; judul?: string }> = ({ s, judul }) => {
  const { fps } = useVideoConfig();
  const dari = Math.round((s.ucapMulai - s.mulai) * fps), sampai = Math.round((s.ucapAkhir - s.mulai) * fps);
  return (
    <div style={{ position: "absolute", left: 150, right: 150, bottom: 92 }}>
      <Entrance delay={6} y={30}>
        <div style={{ background: "rgba(12,26,29,0.74)", borderRadius: 28, padding: "22px 40px 24px",
          border: `2px solid ${theme.colors.line}`, boxShadow: "0 24px 50px -20px rgba(0,0,0,0.6)" }}>
          {judul ? <div style={{ fontFamily: theme.font.body, fontWeight: 600, fontSize: 24, letterSpacing: "0.16em",
            color: theme.colors.hero, marginBottom: 8 }}>{judul}</div> : null}
          <Karaoke text={s.narasi ?? ""} dari={dari} sampai={sampai}
            style={{ fontFamily: theme.font.body, fontWeight: 500, fontSize: 36, lineHeight: 1.42, color: theme.colors.text }} />
        </div>
      </Entrance>
    </div>
  );
};

const Adegan: React.FC<{ s: SegmenPanjang; a: AdeganClay; label: Record<string, string> }> = ({ s, a, label }) => {
  const frame = useCurrentFrame();
  const { durationInFrames, fps } = useVideoConfig();
  const keluar = interpolate(frame, [durationInFrames - 8, durationInFrames], [1, 0], clamp);
  const display: React.CSSProperties = { fontFamily: theme.font.display, fontWeight: 600, color: theme.colors.text,
    textShadow: "0 6px 30px rgba(0,0,0,0.55)", letterSpacing: "-0.01em" };

  if (s.jenis === "dalil") {
    return (
      <AbsoluteFill style={{ opacity: keluar }}>
        <Latar a={a} kabur />
        <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", paddingBottom: 40 }}>
          <Entrance delay={2} y={50}>
            <div style={{ width: 1460, borderRadius: 40, padding: "46px 70px 44px", background: "rgba(12,26,29,0.82)",
              border: `2px solid ${theme.colors.line}`, boxShadow: "0 50px 90px -30px rgba(0,0,0,0.7)", textAlign: "center" }}>
              <div style={{ fontFamily: theme.font.body, fontWeight: 600, fontSize: 26, letterSpacing: "0.2em", color: theme.colors.soft }}>{s.label}</div>
              <div dir="rtl" lang="ar" style={{ fontFamily: theme.font.arab, fontSize: 56, lineHeight: 1.8, color: theme.colors.text, marginTop: 14 }}>{s.arab}</div>
              <div style={{ height: 3, width: 300, margin: "22px auto 26px", background: theme.colors.line, borderRadius: 3 }} />
              <Karaoke text={s.terjemah ?? ""} dari={Math.round((s.ucapMulai - s.mulai) * fps)} sampai={Math.round((s.ucapAkhir - s.mulai) * fps)}
                style={{ fontFamily: theme.font.body, fontWeight: 500, fontSize: 36, lineHeight: 1.5, color: theme.colors.text, justifyContent: "center" }} />
            </div>
          </Entrance>
          <Entrance delay={40} style={{ marginTop: 30 }}>
            <div style={{ fontFamily: theme.font.body, fontWeight: 600, fontSize: 30, color: theme.colors.bg, background: theme.colors.hero,
              padding: "12px 34px", borderRadius: 999 }}>
              {s.sumber}{s.derajat ? ` · ${s.derajat[0].toUpperCase()}${s.derajat.slice(1)}` : ""}
            </div>
          </Entrance>
        </AbsoluteFill>
      </AbsoluteFill>
    );
  }

  if (s.jenis === "bab" || s.jenis === "hook") {
    const p = spring({ frame: frame - 4, fps, config: theme.spring.bouncy });
    return (
      <AbsoluteFill style={{ opacity: keluar }}>
        <Panggung a={a} />
        <AbsoluteFill style={{ background: "linear-gradient(90deg, rgba(8,18,20,0.78), rgba(8,18,20,0.35) 55%, transparent)" }} />
        <div style={{ position: "absolute", left: 150, top: 230, width: 980 }}>
          <div style={{ ...display, fontSize: 190, lineHeight: 0.9, color: "transparent", WebkitTextStroke: `4px ${theme.colors.hero}`,
            opacity: p, transform: `translateX(${interpolate(p, [0, 1], [-60, 0])}px)` }}>{String(s.bab ?? 1).padStart(2, "0")}</div>
          <Entrance delay={8} style={{ marginTop: 10 }}>
            <div style={{ fontFamily: theme.font.body, fontWeight: 600, fontSize: 28, letterSpacing: "0.24em", color: theme.colors.hero }}>
              {label.pelajaran} {s.bab}</div>
          </Entrance>
          <WordReveal text={s.judul ?? ""} delay={14} per={4} style={{ ...display, fontSize: 76, lineHeight: 1.1, marginTop: 18 }} />
        </div>
        <Teks s={s} />
      </AbsoluteFill>
    );
  }

  if (s.jenis === "pembuka" || s.jenis === "penutup") {
    const tutup = s.jenis === "penutup";
    return (
      <AbsoluteFill style={{ opacity: tutup ? 1 : keluar }}>
        <Panggung a={a} />
        <AbsoluteFill style={{ background: "radial-gradient(ellipse at 50% 38%, rgba(8,18,20,0.62), rgba(8,18,20,0.2) 70%)" }} />
        <div style={{ position: "absolute", left: 160, right: 160, top: tutup ? 150 : 190, textAlign: "center",
          display: "flex", flexDirection: "column", alignItems: "center" }}>
          <Bintang ukuran={tutup ? 150 : 120} delay={2} />
          <WordReveal text={tutup ? "Sunnah Daily" : s.judul ?? ""} delay={10} per={4}
            style={{ ...display, fontSize: tutup ? 120 : 92, lineHeight: 1.08, justifyContent: "center", marginTop: 26 }} />
          <Entrance delay={26} style={{ marginTop: 22 }}>
            <div style={{ fontFamily: theme.font.body, fontWeight: 600, fontSize: 32, color: theme.colors.hero,
              textShadow: "0 4px 18px rgba(0,0,0,0.6)" }}>{tutup ? s.ajakan || label.ajak : s.kajian}</div>
          </Entrance>
          {tutup ? (
            <Entrance delay={36} style={{ marginTop: 26 }}>
              <div style={{ fontFamily: theme.font.body, fontSize: 28, lineHeight: 1.5, color: theme.colors.text,
                textShadow: "0 4px 18px rgba(0,0,0,0.6)" }}>{s.kredit}<br />{s.ustadz}</div>
            </Entrance>
          ) : null}
        </div>
        {!tutup ? <Teks s={s} /> : null}
      </AbsoluteFill>
    );
  }

  if (s.jenis === "ajak") {
    return (
      <AbsoluteFill style={{ opacity: keluar }}>
        <Panggung a={a} />
        <TombolAjak label={label} />
        <Teks s={s} />
      </AbsoluteFill>
    );
  }

  if (s.jenis === "kuis" || s.jenis === "jawab") {
    return (
      <AbsoluteFill style={{ opacity: s.jenis === "jawab" ? keluar : 1 }}>
        <Latar a={a} kabur />
        <KartuKuis s={s} label={label} bintang={a.bintang} />
      </AbsoluteFill>
    );
  }

  return (
    <AbsoluteFill style={{ opacity: keluar }}>
      <Panggung a={a} />
      <Teks s={s} judul={s.jenis === "faedah" ? label.faedah : s.label} />
    </AbsoluteFill>
  );
};

/** Tombol Suka & Subscribe yang muncul lalu "ditekan" (ajakan di tengah video). */
const TombolAjak: React.FC<{ label: Record<string, string> }> = ({ label }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const tombol = (teks: string, ikon: React.ReactNode, warna: string, muncul: number, tekan: number) => {
    const p = spring({ frame: frame - muncul, fps, config: theme.spring.bouncy });
    const ditekan = frame >= tekan;
    const dip = interpolate(frame, [tekan - 4, tekan, tekan + 6], [1, 0.86, 1], clamp);
    return (
      <div style={{ display: "flex", alignItems: "center", gap: 18, padding: "22px 44px", borderRadius: 999,
        background: ditekan ? warna : "rgba(246,241,231,0.95)", color: ditekan ? theme.colors.text : theme.colors.bg,
        fontFamily: theme.font.body, fontWeight: 700, fontSize: 46, boxShadow: "0 24px 50px -14px rgba(0,0,0,0.55)",
        transform: `scale(${p * dip})` }}>
        {ikon}{teks}
      </div>
    );
  };
  const jempol = (
    <svg width={52} height={52} viewBox="0 0 24 24" fill="currentColor"><path d="M2 21h4V9H2v12zm20-11c0-1.1-.9-2-2-2h-6.3l1-4.6v-.3c0-.4-.2-.8-.4-1.1L13.2 1 6.6 7.6c-.4.3-.6.8-.6 1.4V19c0 1.1.9 2 2 2h9c.8 0 1.5-.5 1.8-1.2l3-7.1c.1-.2.2-.5.2-.7v-2z" /></svg>
  );
  const lonceng = (
    <svg width={50} height={50} viewBox="0 0 24 24" fill="currentColor"><path d="M12 22c1.1 0 2-.9 2-2h-4c0 1.1.9 2 2 2zm6-6v-5c0-3.1-1.6-5.6-4.5-6.3V4c0-.8-.7-1.5-1.5-1.5S10.5 3.2 10.5 4v.7C7.6 5.4 6 7.9 6 11v5l-2 2v1h16v-1l-2-2z" /></svg>
  );
  return (
    <div style={{ position: "absolute", top: 250, left: 0, right: 0, display: "flex", justifyContent: "center", gap: 40 }}>
      {tombol(label.suka, jempol, theme.colors.teal, 8, 40)}
      {tombol(label.subscribe, lonceng, theme.colors.merah, 16, 64)}
    </div>
  );
};

/** Kartu kuis: soal + 3 pilihan; 'kuis' memberi hitung mundur, 'jawab' menyalakan jawaban yang benar. */
const KartuKuis: React.FC<{ s: SegmenPanjang; label: Record<string, string>; bintang?: string }> = ({ s, label, bintang }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const jawab = s.jenis === "jawab";
  const habisSuara = Math.round((s.ucapAkhir - s.mulai) * fps);
  const sisa = Math.ceil((durationInFrames - frame) / fps);
  const hitung = !jawab && frame > habisSuara && sisa >= 1 && sisa <= 5 ? sisa : 0;
  const p = spring({ frame: frame - 2, fps, config: theme.spring.bouncy });
  return (
    <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", paddingBottom: 30 }}>
      <div style={{ width: 1400, borderRadius: 44, padding: "40px 64px 46px", background: "rgba(12,26,29,0.86)",
        border: `3px solid ${theme.colors.hero}`, boxShadow: "0 50px 90px -30px rgba(0,0,0,0.7)", transform: `scale(${jawab ? 1 : p})` }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <div style={{ fontFamily: theme.font.display, fontWeight: 600, fontSize: 64, color: theme.colors.hero }}>{label.kuis}</div>
          {hitung ? (
            <div style={{ width: 110, height: 110, borderRadius: "50%", background: theme.colors.hero, color: theme.colors.bg,
              display: "flex", alignItems: "center", justifyContent: "center", fontFamily: theme.font.display, fontWeight: 600, fontSize: 70,
              transform: `scale(${1 + 0.15 * Math.max(0, 1 - ((frame % fps) / 8))})` }}>{hitung}</div>
          ) : null}
        </div>
        <div style={{ fontFamily: theme.font.body, fontWeight: 600, fontSize: 46, lineHeight: 1.35, color: theme.colors.text, marginTop: 18 }}>{s.tanya}</div>
        <div style={{ display: "flex", flexDirection: "column", gap: 18, marginTop: 32 }}>
          {(s.pilihan ?? []).map((t, i) => {
            const benar = jawab && i === s.jawab;
            const masuk = spring({ frame: frame - (jawab ? 0 : 14 + i * 8), fps, config: theme.spring.smooth });
            return (
              <div key={i} style={{ display: "flex", alignItems: "center", gap: 26, padding: "18px 30px", borderRadius: 24,
                background: benar ? theme.colors.benar : "rgba(246,241,231,0.08)", border: `2px solid ${benar ? theme.colors.benar : theme.colors.line}`,
                opacity: jawab && !benar ? 0.4 : masuk, transform: `translateX(${interpolate(masuk, [0, 1], [-40, 0])}px) scale(${benar ? 1.03 : 1})` }}>
                <div style={{ width: 64, height: 64, borderRadius: "50%", background: theme.colors.hero, color: theme.colors.bg, flexShrink: 0,
                  display: "flex", alignItems: "center", justifyContent: "center", fontFamily: theme.font.body, fontWeight: 700, fontSize: 36 }}>{"ABC"[i]}</div>
                <div style={{ fontFamily: theme.font.body, fontWeight: 600, fontSize: 40, color: theme.colors.text }}>{t}{benar ? "  ✓" : ""}</div>
              </div>
            );
          })}
        </div>
      </div>
      {jawab && bintang ? [0, 1, 2, 3, 4, 5, 6, 7].map((i) => {
        const q = spring({ frame: frame - 4 - i * 2, fps, config: theme.spring.bouncy });
        const sudut = (i / 8) * Math.PI * 2;
        return <Img key={i} src={staticFile(bintang)} style={{ position: "absolute", left: W / 2 + Math.cos(sudut) * 900 * q - 40,
          top: H / 2 + Math.sin(sudut) * 500 * q - 40, width: 80, opacity: q, transform: `rotate(${frame * 3 + i * 40}deg)` }} />;
      }) : null}
    </AbsoluteFill>
  );
};

export const VideoClay: React.FC<DataClay> = ({ kicker, handle, durasi, bab, segmen, adegan, label }) => {
  const batas = segmen.map((s) => Math.round(s.mulai * FPS));
  const lbl = { ...LABEL_ID, ...(label ?? {}) };
  return (
    <AbsoluteFill style={{ background: theme.colors.bg }}>
      {segmen.map((s, i) => {
        const akhir = i + 1 < segmen.length ? batas[i + 1] : Math.round(s.akhir * FPS);
        return (
          <Sequence key={i} from={batas[i]} durationInFrames={Math.max(1, akhir - batas[i])}>
            <Adegan s={s} a={adegan[i] ?? adegan[0]} label={lbl} />
          </Sequence>
        );
      })}
      <AbsoluteFill style={{ pointerEvents: "none", background:
        "linear-gradient(180deg, rgba(8,18,20,0.62), rgba(8,18,20,0.0) 17%, transparent 85%, rgba(8,18,20,0.45))" }} />
      <Kepala kicker={kicker} handle={handle ?? "@sun_nahdaily"} bab={bab} />
      <BilahBab bab={bab} total={durasi} />
    </AbsoluteFill>
  );
};
