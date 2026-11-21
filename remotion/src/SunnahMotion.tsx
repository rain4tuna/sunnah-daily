import React from "react";
import { AbsoluteFill, Audio, Sequence, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { theme } from "./theme";
import { Bintang, Entrance, Garis, Karaoke, Scene, WordReveal, clamp } from "./Motion";
import { Grade, Grain, Latar, Vignette } from "./Layers";
import { DenganStiker, StikerData } from "./Stiker";
import { AdeganKaya, ADEGAN_BARU } from "./AdeganKaya";
import { KarakterKaya, POSE_KAYA, VarianKarakter } from "./KarakterKaya";
import { JENIS_PROPERTI, JenisProperti, PropertiKaya } from "./PropertiKaya";

/**
 * SunnahMotion — Template Video Motion/Animasi Baru 9:16 (IG Reels, YouTube Shorts, TikTok).
 *
 * Dirancang mengikuti /claude-youtube (shorts-playbook, retention-scripting-guide) & skill IG (ig-reel):
 * 1. SAFE ZONE KETAT 1080x1920:
 *    - Atas >= 230px, Bawah <= 1440px, Sisi Kanan 230px BERSIH (x <= 850) untuk tombol like/komen/share IG/YT/TikTok.
 * 2. FRAME-1 INSTANT HOOK:
 *    - Judul hook + panggung animasi langsung hadir dan bergerak dari frame 0 (tanpa layar kosong / jeda intro).
 * 3. VISUAL BEAT CADENCE (2-3 detik):
 *    - Kamera dorong/geser lembut, karakter artikulasi natural, properti pop-in, karaoke kata aktif menyala.
 * 4. EMBEDDED VISUAL + VERBAL CTA & LOOP BRIDGE:
 *    - Pill CTA visual muncul tepat setelah faedah (+380% konversi) + kalimat pengait loop di penutup (>100% replay).
 * 5. ATURAN SUNNAH 100%:
 *    - Semua karakter tanpa mata/alis/hidung/mulut; tidak ada Nabi/sahabat/malaikat; TANPA MUSIK (hanya suara + SFX non-musik).
 */

const FPS = 30;

// Safe zone ketat lintas-platform (IG Reels + YT Shorts + TikTok):
// x: 56..846 (lebar 790px -> menyisakan 234px bersih di sisi kanan untuk action rail!)
// y: 230..1430 (menyisakan 230px di atas dan 490px di bawah untuk caption/audio bar!)
export const SAFE_KAYA = {
  left: 56,
  right: 234,
  width: 790,
  top: 230,
  bottom: 1430,
} as const;

export type SegmenKaya = {
  jenis: "hook" | "poin" | "dalil" | "faedah" | "penutup";
  mulai: number;
  akhir: number;
  ucapMulai: number;
  ucapAkhir: number;
  judul?: string;
  narasi?: string;
  no?: number;
  label?: string;
  arab?: string;
  terjemah?: string;
  sumber?: string;
  derajat?: string;
  ajakan?: string;
  kredit?: string;
  ustadz?: string;
  ilustrasi?: string;
  tokoh?: string;
  varian?: VarianKarakter;
  properti?: JenisProperti;
  stiker?: StikerData[];
  hookBadge?: string;
  ctaSingkat?: string;
  loopEcho?: string;
};

export type DataKaya = {
  kicker: string;
  handle?: string;
  durasi: number;
  frame?: number;
  audio?: string;
  segmen: SegmenKaya[];
};

const display: React.CSSProperties = {
  fontFamily: theme.font.display,
  fontWeight: 600,
  letterSpacing: "-0.02em",
  color: theme.colors.text,
};
const badan: React.CSSProperties = {
  fontFamily: theme.font.body,
  fontWeight: 500,
  color: theme.colors.text,
};

const areaIsi: React.CSSProperties = {
  position: "absolute",
  left: SAFE_KAYA.left,
  width: SAFE_KAYA.width,
  top: SAFE_KAYA.top + 88,
  height: SAFE_KAYA.bottom - (SAFE_KAYA.top + 88),
  display: "flex",
  flexDirection: "column",
  justifyContent: "center",
};

const useUcap = (s: SegmenKaya) => {
  const { fps } = useVideoConfig();
  return {
    dari: Math.round((s.ucapMulai - s.mulai) * fps),
    sampai: Math.round((s.ucapAkhir - s.mulai) * fps),
  };
};

/** Header safe-zone (y=230, x=56..846): kicker seri, handle, dan progress bar babak. */
const KepalaKaya: React.FC<{ kicker: string; handle: string; batas: number[] }> = ({ kicker, handle, batas }) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  return (
    <div style={{ position: "absolute", top: SAFE_KAYA.top, left: SAFE_KAYA.left, width: SAFE_KAYA.width }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div
          style={{
            fontFamily: theme.font.body,
            fontWeight: 700,
            fontSize: 24,
            letterSpacing: "0.14em",
            color: theme.colors.bg,
            padding: "8px 20px",
            borderRadius: 999,
            background: theme.colors.hero,
          }}
        >
          {kicker}
        </div>
        <div style={{ fontFamily: theme.font.body, fontWeight: 600, fontSize: 27, color: theme.colors.soft }}>
          {handle}
        </div>
      </div>
      {/* Progress bar retention: menunjukkan babak ke penonton agar bertahan sampai akhir */}
      <div style={{ display: "flex", gap: 8, marginTop: 16 }}>
        {batas.map((mulai, i) => {
          const akhir = i + 1 < batas.length ? batas[i + 1] : durationInFrames;
          const isi = interpolate(frame, [mulai, akhir], [0, 1], clamp);
          return (
            <div
              key={i}
              style={{ flex: 1, height: 6, borderRadius: 6, background: "rgba(246,241,231,0.18)", overflow: "hidden" }}
            >
              <div style={{ width: `${isi * 100}%`, height: "100%", background: theme.colors.hero }} />
            </div>
          );
        })}
      </div>
    </div>
  );
};

/** Frame-1 Instant Hook: teks + visual bergerak langsung di frame 0 (tanpa jeda). */
const HookKaya: React.FC<{ s: SegmenKaya }> = ({ s }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const { dari, sampai } = useUcap(s);
  const kata = (s.judul ?? "").split(" ").filter(Boolean);
  const denyut = 1 + Math.sin(frame / 8) * 0.03;
  const masukJudul = spring({ frame, fps, config: theme.spring.snappy });

  return (
    <Scene>
      <div style={{ ...areaIsi, alignItems: "flex-start", textAlign: "left" }}>
        {/* Hook badge langsung aktif di frame 0 */}
        <div
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: 10,
            padding: "8px 18px",
            borderRadius: 999,
            background: "rgba(232,176,74,0.16)",
            border: `2px solid ${theme.colors.hero}`,
            marginBottom: 18,
            transform: `scale(${denyut})`,
          }}
        >
          <span style={{ width: 10, height: 10, borderRadius: "50%", background: theme.colors.hero }} />
          <span style={{ ...badan, fontWeight: 700, fontSize: 22, letterSpacing: "0.14em", color: theme.colors.hero }}>
            {s.hookBadge || "TAHUKAH KAMU?"}
          </span>
        </div>

        {/* Judul hook <= 6 kata langsung terlihat di frame 0-1 */}
        <div
          style={{
            ...display,
            fontSize: 78,
            lineHeight: 1.08,
            transform: `translateY(${interpolate(masukJudul, [0, 1], [14, 0])}px)`,
            marginBottom: 26,
          }}
        >
          {kata.map((w, i) => (
            <span
              key={i}
              style={{
                display: "inline-block",
                marginRight: "0.22em",
                color: i === kata.length - 1 ? theme.colors.hero : theme.colors.text,
              }}
            >
              {w}
            </span>
          ))}
        </div>

        {/* Panggung animasi kaya bergerak dari frame 0 */}
        <DenganStiker stiker={s.stiker?.slice(0, 2)} sudut={["kiriBawah", "kananAtas"]} delay={4}>
          <AdeganKaya
            jenis={s.ilustrasi}
            tokoh={s.tokoh}
            varian={s.varian}
            properti={s.properti}
            tinggi={420}
            lebar={SAFE_KAYA.width}
            delay={0}
          />
        </DenganStiker>

        {/* Subtitel karaoke kontras tinggi */}
        <div
          style={{
            marginTop: 26,
            padding: "18px 24px",
            borderRadius: 24,
            background: "rgba(12,26,29,0.72)",
            border: `1.5px solid ${theme.colors.line}`,
            width: "100%",
          }}
        >
          <Karaoke
            text={s.narasi ?? ""}
            dari={dari}
            sampai={sampai}
            style={{ ...badan, fontSize: 38, lineHeight: 1.4 }}
          />
        </div>
      </div>
    </Scene>
  );
};

/** Poin cerita dengan micro-pattern-interrupt + nomor progres + panggung animasi natural. */
const PoinKaya: React.FC<{ s: SegmenKaya }> = ({ s }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const { dari, sampai } = useUcap(s);
  const p = spring({ frame: frame - 3, fps, config: theme.spring.bouncy });

  return (
    <Scene>
      <div style={areaIsi}>
        <DenganStiker stiker={s.stiker?.slice(0, 2)} sudut={["kananAtas", "kiriBawah"]} delay={6}>
          <AdeganKaya
            jenis={s.ilustrasi}
            tokoh={s.tokoh}
            varian={s.varian}
            properti={s.properti}
            tinggi={460}
            lebar={SAFE_KAYA.width}
            delay={0}
          />
          {/* Badge nomor babak */}
          <div
            style={{
              ...display,
              position: "absolute",
              left: 22,
              top: 18,
              fontSize: 82,
              lineHeight: 1,
              color: theme.colors.hero,
              textShadow: "0 10px 26px rgba(0,0,0,0.65)",
              opacity: p,
              transform: `scale(${interpolate(p, [0, 1], [0.75, 1])})`,
            }}
          >
            {String(s.no ?? 1).padStart(2, "0")}
          </div>
        </DenganStiker>

        <WordReveal
          text={s.label ?? ""}
          delay={4}
          per={3}
          style={{ ...display, fontSize: 64, lineHeight: 1.1, marginTop: 28 }}
        />
        <Garis delay={10} lebar={150} style={{ marginTop: 20, marginBottom: 24 }} />

        <div
          style={{
            padding: "18px 24px",
            borderRadius: 24,
            background: "rgba(12,26,29,0.72)",
            border: `1.5px solid ${theme.colors.line}`,
          }}
        >
          <Karaoke
            text={s.narasi ?? ""}
            dari={dari}
            sampai={sampai}
            style={{ ...badan, fontSize: 40, lineHeight: 1.44 }}
          />
        </div>
      </div>
    </Scene>
  );
};

/** Kartu dalil: teks Arab Amiri berharakat + terjemah karaoke + badge derajat terverifikasi. */
const DalilKaya: React.FC<{ s: SegmenKaya }> = ({ s }) => {
  const frame = useCurrentFrame();
  const { dari, sampai } = useUcap(s);
  const garis = interpolate(frame, [14, 42], [0, 1], { ...clamp, easing: theme.ease.out });
  const apung = Math.sin(frame / 28) * 3.5;

  return (
    <Scene>
      <div style={{ ...areaIsi, alignItems: "stretch" }}>
        <Entrance delay={0} y={40}>
          <div
            style={{
              transform: `translateY(${apung}px)`,
              borderRadius: 36,
              padding: "42px 38px 38px",
              background: "rgba(16,32,37,0.88)",
              border: `2px solid ${theme.colors.hero}66`,
              boxShadow: "0 40px 80px -26px rgba(0,0,0,0.7)",
            }}
          >
            <div
              style={{
                ...badan,
                fontWeight: 700,
                fontSize: 26,
                letterSpacing: "0.2em",
                color: theme.colors.hero,
                textAlign: "center",
              }}
            >
              {s.label || "DALIL"}
            </div>
            <div
              dir="rtl"
              lang="ar"
              style={{
                fontFamily: theme.font.arab,
                fontSize: 64,
                lineHeight: 1.85,
                color: theme.colors.text,
                textAlign: "center",
                marginTop: 18,
              }}
            >
              {s.arab}
            </div>
            <div
              style={{
                height: 3,
                margin: "24px auto 28px",
                width: `${garis * 52}%`,
                background: theme.colors.hero,
                borderRadius: 3,
                opacity: 0.7,
              }}
            />
            <Karaoke
              text={s.terjemah ?? ""}
              dari={dari}
              sampai={sampai}
              style={{ ...badan, fontSize: 38, lineHeight: 1.46, justifyContent: "center", textAlign: "center" }}
            />
          </div>
        </Entrance>

        <Entrance delay={18} style={{ alignSelf: "center", marginTop: 28 }}>
          <div
            style={{
              ...badan,
              fontWeight: 700,
              fontSize: 30,
              color: theme.colors.bg,
              background: theme.colors.hero,
              padding: "12px 30px",
              borderRadius: 999,
              boxShadow: `0 0 44px ${theme.colors.hero}55`,
            }}
          >
            {s.sumber}
            {s.derajat ? ` · ${s.derajat[0].toUpperCase()}${s.derajat.slice(1)}` : ""}
          </div>
        </Entrance>
      </div>
    </Scene>
  );
};

/** Faedah + Embedded Visual CTA Pill (muncul tepat setelah nilai utama disampaikan). */
const FaedahKaya: React.FC<{ s: SegmenKaya }> = ({ s }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const { dari, sampai } = useUcap(s);
  const ctaSpring = spring({ frame: frame - 28, fps, config: theme.spring.bouncy });

  return (
    <Scene>
      <div style={{ ...areaIsi, alignItems: "center", textAlign: "center" }}>
        <DenganStiker stiker={s.stiker?.slice(0, 2)} sudut={["kiriAtas", "kananBawah"]} delay={4}>
          <AdeganKaya
            jenis={s.ilustrasi}
            tokoh={s.tokoh}
            varian={s.varian}
            properti={s.properti}
            tinggi={390}
            lebar={SAFE_KAYA.width}
            delay={0}
          />
        </DenganStiker>

        <div style={{ display: "flex", alignItems: "center", gap: 20, marginTop: 28 }}>
          <Garis delay={6} lebar={72} />
          <div style={{ ...badan, fontWeight: 700, fontSize: 28, letterSpacing: "0.22em", color: theme.colors.hero }}>
            FAEDAH
          </div>
          <Garis delay={6} lebar={72} />
        </div>

        <div style={{ marginTop: 22 }}>
          <Karaoke
            text={s.narasi ?? ""}
            dari={dari}
            sampai={sampai}
            style={{ ...display, fontSize: 54, lineHeight: 1.24, justifyContent: "center" }}
          />
        </div>

        {/* Embedded Visual CTA Pill (catch viewers before final 10% drop-off) */}
        <div
          style={{
            marginTop: 28,
            padding: "12px 26px",
            borderRadius: 999,
            background: "rgba(46,140,133,0.28)",
            border: `2px solid ${theme.colors.teal}`,
            color: theme.colors.text,
            fontFamily: theme.font.body,
            fontWeight: 600,
            fontSize: 26,
            opacity: ctaSpring,
            transform: `scale(${interpolate(ctaSpring, [0, 1], [0.85, 1])})`,
          }}
        >
          {s.ctaSingkat || "Simpan untuk diamalkan hari ini"}
        </div>
      </div>
    </Scene>
  );
};

/** Penutup: single focused CTA pill + loop-echo + kredit kajian wajib. */
const PenutupKaya: React.FC<{ s: SegmenKaya }> = ({ s }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const p = spring({ frame: frame - 2, fps, config: theme.spring.bouncy });
  const denyut = 1 + Math.sin(frame / 9) * 0.035;

  return (
    <AbsoluteFill>
      <div style={{ ...areaIsi, alignItems: "center", textAlign: "center" }}>
        <div style={{ transform: `scale(${p})`, filter: `drop-shadow(0 0 42px ${theme.colors.hero}66)` }}>
          <Bintang ukuran={190} delay={0} />
        </div>
        <WordReveal
          text="Sunnah Daily"
          delay={6}
          per={4}
          style={{ ...display, fontSize: 98, lineHeight: 1.02, justifyContent: "center", marginTop: 26 }}
        />

        {/* Single Focused CTA Pill (sesuai ig-reel & claude-youtube) */}
        <Entrance delay={14} style={{ marginTop: 32 }}>
          <div
            style={{
              ...badan,
              fontWeight: 700,
              fontSize: 38,
              color: theme.colors.bg,
              background: theme.colors.hero,
              padding: "16px 36px",
              borderRadius: 999,
              transform: `scale(${denyut})`,
              boxShadow: `0 18px 44px -10px ${theme.colors.hero}88`,
            }}
          >
            {s.ajakan || "Tulis Aamiin di komentar"}
          </div>
        </Entrance>

        {/* Loop bridge echo (mengaitkan kembali ke hook awal agar replay mulus) */}
        {s.loopEcho ? (
          <Entrance delay={22} style={{ marginTop: 26 }}>
            <div style={{ ...badan, fontSize: 28, color: theme.colors.soft, fontStyle: "italic" }}>
              “{s.loopEcho}”
            </div>
          </Entrance>
        ) : null}

        {/* Kredit kajian wajib */}
        <Entrance delay={26} style={{ marginTop: 48 }}>
          <div style={{ ...badan, fontSize: 26, lineHeight: 1.5, color: theme.colors.soft }}>
            {s.kredit}
            <br />
            {s.ustadz}
          </div>
        </Entrance>
      </div>
    </AbsoluteFill>
  );
};

const ADEGAN_KAYA = {
  hook: HookKaya,
  poin: PoinKaya,
  dalil: DalilKaya,
  faedah: FaedahKaya,
  penutup: PenutupKaya,
} as const;

export const SunnahMotion: React.FC<DataKaya> = ({ kicker, handle, audio, segmen }) => {
  const batas = segmen.map((s) => Math.round(s.mulai * FPS));
  return (
    <AbsoluteFill>
      <Latar />
      {segmen.map((s, i) => {
        const Adegan = ADEGAN_KAYA[s.jenis];
        const akhir = i + 1 < segmen.length ? batas[i + 1] : Math.round(s.akhir * FPS);
        return (
          <Sequence key={i} from={batas[i]} durationInFrames={Math.max(1, akhir - batas[i])}>
            <Adegan s={s} />
          </Sequence>
        );
      })}
      <KepalaKaya kicker={kicker} handle={handle ?? "@sun_nahdaily"} batas={batas} />
      <Grade />
      <Grain />
      <Vignette />
      {audio ? <Audio src={staticFile(audio)} /> : null}
    </AbsoluteFill>
  );
};

/** Lembar periksa visual (contact sheet) untuk verifikasi independen:
 *  Menampilkan seluruh 8 pose KarakterKaya (4 varian, 100% tanpa mata & hidung), 12 PropertiKaya, dan 6 adegan baru. */
export const GaleriKaya: React.FC = () => {
  const frame = useCurrentFrame();
  const varianList: VarianKarakter[] = ["pria_sorban", "pemuda", "tetua_jubah", "wanita_hijab"];
  return (
    <AbsoluteFill style={{ background: "#0C1A1D", padding: 28, display: "flex", flexDirection: "column", gap: 18 }}>
      <div style={{ color: theme.colors.hero, fontFamily: theme.font.display, fontSize: 38, fontWeight: 600 }}>
        GaleriKaya — 8 Pose Karakter (100% Tanpa Mata/Hidung), 12 Properti & 6 Adegan Baru
      </div>

      {/* Baris 1: 8 pose karakter tanpa mata & hidung */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12 }}>
        {POSE_KAYA.map((pose, i) => (
          <div
            key={pose}
            style={{
              background: "#13262B",
              borderRadius: 18,
              border: `1.5px solid ${theme.colors.line}`,
              padding: 8,
              textAlign: "center",
            }}
          >
            <svg width={230} height={240} viewBox="-150 -360 300 390">
              <KarakterKaya x={0} y={0} scale={0.95} pose={pose} varian={varianList[i % 4]} frame={frame + i * 7} />
            </svg>
            <div style={{ color: theme.colors.text, fontFamily: theme.font.body, fontSize: 18 }}>
              {pose} ({varianList[i % 4]})
            </div>
          </div>
        ))}
      </div>

      {/* Baris 2: 12 properti */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(6, 1fr)", gap: 10 }}>
        {JENIS_PROPERTI.map((prop, i) => (
          <div
            key={prop}
            style={{
              background: "#13262B",
              borderRadius: 14,
              border: `1px solid ${theme.colors.line}`,
              padding: 6,
              textAlign: "center",
            }}
          >
            <svg width={150} height={116} viewBox="-80 -70 160 140">
              <PropertiKaya jenis={prop} x={0} y={0} scale={0.95} frame={frame + 30 + i * 4} delay={0} />
            </svg>
            <div style={{ color: theme.colors.soft, fontFamily: theme.font.body, fontSize: 14 }}>{prop}</div>
          </div>
        ))}
      </div>

      {/* Baris 3: 6 adegan baru */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 12 }}>
        {ADEGAN_BARU.map((ad, i) => (
          <div key={ad} style={{ textAlign: "center" }}>
            <AdeganKaya
              jenis={ad}
              tokoh={POSE_KAYA[i % POSE_KAYA.length]}
              varian={varianList[i % 4]}
              tinggi={260}
              lebar={330}
              delay={0}
            />
            <div style={{ color: theme.colors.text, fontFamily: theme.font.body, fontSize: 16, marginTop: 4 }}>
              {ad}
            </div>
          </div>
        ))}
      </div>
    </AbsoluteFill>
  );
};
