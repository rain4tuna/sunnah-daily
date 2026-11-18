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

/** Aksi tokoh setelah tiba: menentukan gerak (dan pose khusus bila asetnya ada). */
export type Aksi = "bicara" | "senang" | "sedih" | "nangis" | "marah" | "kaget" | "gali" | "doa" | "tunjuk" | "lewat";
export type TokohClay = {
  diam: string;             // pose berdiri (p01)
  samping?: string;         // pose 3/4 (p02): dipakai bergantian supaya tokoh "menoleh"
  jalan?: [string, string]; // dua pose jalan (p03, p04) bergantian
  x: number;                // posisi akhir (pusat, px)
  dari?: "kiri" | "kanan";  // masuk sambil berjalan dari sisi ini
  tinggi?: number;
  aksi?: Aksi;
  aksiFile?: string[];      // pose aksi (mis. sedih p09, gali p12/p13); dua file = bergantian
};
export type BendaClay = { file: string; x: number; y?: number; tinggi: number; muncul?: number };
/** Makhluk latar yang membuat adegan ramai: unta lewat, domba merumput, kerumunan kecil di kejauhan. */
export type FiguranClay = { a: string; b?: string; y: number; tinggi: number; lewat?: "kiri" | "kanan"; x?: number; laju?: number };
export type AdeganClay = {
  latar: string;                                  // gambar latar (selalu ada, cadangan klip)
  gerak?: { file: string; durasi: number };       // klip Flow (dipakai bila ada)
  suasana?: "siang" | "malam";
  tokoh?: TokohClay[];
  benda?: BendaClay[];
  figuran?: FiguranClay[];
  awan?: string[];                                // elemen awan yang melayang (siang)
  bintang?: string;                               // elemen bintang yang berkelip (malam)
  kamera?: "dorong" | "geser" | "tarik";          // gerak kamera adegan
  hujan?: string;                                 // awan mendung (e02) di atas tokoh yang sedih
};
export type DataClay = DataPanjang & { adegan: AdeganClay[]; label?: Record<string, string> };

const LABEL_ID = { pelajaran: "KISAH", faedah: "PELAJARAN BUAT KITA", ajak: "Subscribe & bagikan", kuis: "KUIS!",
  suka: "Suka", subscribe: "Subscribe" };

/** Gerak kamera adegan: skala & geser; lapisan latar memakai sebagian saja (paralaks). */
const useKamera = (a: AdeganClay, faktor = 1) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const t = interpolate(frame, [0, durationInFrames], [0, 1], { ...clamp, easing: theme.ease.inOut });
  const fokus = a.tokoh?.length ? a.tokoh.reduce((n, k) => n + k.x, 0) / a.tokoh.length : W / 2;
  const goyang = Math.sin(frame / 37) * 5 + Math.sin(frame / 23) * 3;          // kamera "dipegang tangan"
  let s = 1, x = 0;
  if (a.kamera === "dorong") { s = 1 + 0.12 * t; x = (W / 2 - fokus) * 0.18 * t; }
  else if (a.kamera === "tarik") { s = 1.14 - 0.12 * t; x = (W / 2 - fokus) * 0.15 * (1 - t); }
  else if (a.kamera === "geser") { s = 1.08; x = interpolate(t, [0, 1], [70, -70]); }
  else { s = 1 + 0.06 * t; x = -30 * t; }
  return `scale(${1 + (s - 1) * faktor}) translate(${(x + goyang) * faktor}px, ${Math.cos(frame / 31) * 3 * faktor}px)`;
};

/** Latar: klip Flow (diperlambat secukupnya, lalu beralih ke gambar) atau gambar dengan gerak kamera pelan. */
const Latar: React.FC<{ a: AdeganClay; kabur?: boolean }> = ({ a, kabur }) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const kamera = useKamera(a, 0.6);
  const gambar = (
    <Img src={staticFile(a.latar)} style={{ width: W, height: H, objectFit: "cover", transform: kamera }} />
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

// angka acak tetap (sama tiap render) untuk partikel
const acak = (n: number) => { const x = Math.sin(n * 127.1 + 311.7) * 43758.5453; return x - Math.floor(x); };
// gerak "stop-motion": nilai hanya berubah tiap 2 frame (12 fps), khas animasi clay
const dua = (f: number) => Math.floor(f / 2) * 2;

/** Kepulan debu kecil di kaki (tiap langkah / mendarat). */
const Debu: React.FC<{ x: number; f: number; kuat?: number }> = ({ x, f, kuat = 1 }) => (
  <>
    {[0, 1, 2, 3, 4].map((i) => {
      const u = f / 16;
      if (u < 0 || u > 1) return null;
      const arah = (i - 2) * 26 + (acak(i + x) - 0.5) * 20;
      return <div key={i} style={{ position: "absolute", left: x + arah * u * 2.2 * kuat, top: TANAH - 14 - u * 26 * kuat - acak(i) * 10,
        width: (22 + acak(i * 3) * 18) * kuat * (0.6 + u), height: (16 + acak(i * 5) * 12) * kuat * (0.6 + u), borderRadius: "50%",
        background: "rgba(214,186,140,0.75)", opacity: (1 - u) * 0.85, transform: "translate(-50%, -50%)", filter: "blur(1px)" }} />;
    })}
  </>
);

/** Partikel aksi di sekitar tokoh: air mata, tanah galian, kilau senang, uap marah, tanda seru kaget. */
const Partikel: React.FC<{ aksi: Aksi; x: number; puncak: number; f: number; arah: number }> = ({ aksi, x, puncak, f, arah }) => {
  if (f < 0) return null;
  // sedih/nangis: TANPA air mata di wajah (titik di wajah polos bisa terbaca seperti mata); cukup awan mendung + gerak
  if (aksi === "gali") {
    return (
      <>
        {[0, 1, 2, 3, 4, 5].map((i) => {
          const per = 18;
          const u = ((f + i * 3) % per) / per;
          const vx = (40 + acak(i) * 70) * -arah, vy = 120 + acak(i + 7) * 60;
          return <div key={i} style={{ position: "absolute", left: x + arah * 120 + vx * u * 2, top: TANAH - 30 - vy * u + 260 * u * u,
            width: 16 + acak(i * 2) * 14, height: 13 + acak(i * 4) * 10, borderRadius: "45%", background: "#9a6b43",
            boxShadow: "inset -3px -3px 0 rgba(0,0,0,0.22)", transform: `translate(-50%,-50%) rotate(${u * 300}deg)` }} />;
        })}
        <div style={{ position: "absolute", left: x + arah * 170, top: TANAH, width: Math.min(220, 60 + f * 0.9), height: Math.min(70, 16 + f * 0.3),
          borderRadius: "50% 50% 8px 8px / 100% 100% 8px 8px", background: "linear-gradient(#b07c4f, #8a5c37)",
          transform: "translate(-50%, -100%)", boxShadow: "inset 0 6px 0 rgba(255,255,255,0.12)" }} />
      </>
    );
  }
  if (aksi === "senang") {
    return (
      <>
        {[0, 1, 2, 3, 4].map((i) => {
          const per = 40;
          const u = ((f + i * 8) % per) / per;
          const s = Math.sin(u * Math.PI);
          return <div key={i} style={{ position: "absolute", left: x + (acak(i) - 0.5) * 260, top: puncak - 20 - u * 90 + acak(i + 3) * 60,
            fontSize: 34 + acak(i * 9) * 20, color: theme.colors.hero, opacity: s, transform: `translate(-50%,-50%) scale(${0.5 + s * 0.6}) rotate(${u * 180}deg)`,
            textShadow: "0 0 14px rgba(255,210,120,0.8)" }}>✦</div>;
        })}
      </>
    );
  }
  if (aksi === "marah") {
    return (
      <>
        {[0, 1, 2].map((i) => {
          const per = 30;
          const u = ((f + i * 10) % per) / per;
          return <div key={i} style={{ position: "absolute", left: x + (i - 1) * 46 + Math.sin(u * 6) * 8, top: puncak - 10 - u * 80,
            width: 34 + u * 30, height: 34 + u * 30, borderRadius: "50%", background: "rgba(240,240,240,0.8)", opacity: (1 - u) * 0.8,
            transform: "translate(-50%,-50%)", filter: "blur(2px)" }} />;
        })}
      </>
    );
  }
  if (aksi === "kaget") {
    const p = interpolate(f, [0, 6, 12, 40, 50], [0, 1.3, 1, 1, 0], clamp);
    return <div style={{ position: "absolute", left: x + 70, top: puncak - 40, fontFamily: theme.font.display, fontWeight: 700, fontSize: 110,
      color: theme.colors.hero, transform: `translate(-50%,-50%) scale(${p}) rotate(${Math.sin(f / 3) * 8}deg)`,
      textShadow: "0 6px 0 #a5701f, 0 12px 20px rgba(0,0,0,0.4)" }}>!</div>;
  }
  return null;
};

/** Tokoh: masuk sambil berjalan (debu tiap langkah, mendarat memantul), lalu "hidup" sesuai aksinya. */
const Tokoh: React.FC<{ t: TokohClay; ke: number; jumlah: number }> = ({ t, ke, jumlah }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const tinggi = t.tinggi ?? TINGGI_TOKOH;
  const aksi = t.aksi ?? "bicara";
  const lewat = aksi === "lewat";
  const lama = lewat ? durationInFrames : t.dari && t.jalan ? 48 : 0;
  const mulai = 4 + ke * 12;
  const f = frame - mulai;
  const dariKiri = t.dari !== "kanan";
  const awal = dariKiri ? -280 : W + 280;
  const x = lewat ? interpolate(f, [0, lama], [awal, dariKiri ? W + 280 : -280], clamp)
    : lama ? interpolate(f, [0, lama], [awal, t.x], { ...clamp, easing: theme.ease.out }) : t.x;
  // sebelum mulai berjalan f negatif; Math.floor(-1/7) % 2 = -1 di JS -> jalan[-1] undefined -> staticFile error
  const berjalan = lama > 0 && f >= 0 && f < lama;
  const s = f - lama;                     // waktu sejak tiba
  const q = dua(frame);
  // arah hadap: saat berjalan mengikuti arah jalan; setelah tiba menghadap ke tengah / ke lawan bicara
  let hadap = berjalan ? (dariKiri ? 1 : -1) : (t.x < W / 2 ? 1 : -1);
  let file = (berjalan ? t.jalan![Math.floor(f / 6) % 2] : undefined) ?? t.diam ?? t.jalan?.[0];
  let y = 0, rot = 0, sx = 1, sy = 1 + Math.sin(q / 14 + ke) * 0.015, gx = 0;
  if (berjalan) {
    y = -Math.abs(Math.sin(f / 6 * Math.PI)) * 16;
    rot = Math.sin(f / 6 * Math.PI) * 3;
  } else if (s >= 0) {
    const mendarat = interpolate(s, [0, 5, 12], [0.9, 1.06, 1], clamp);      // squash saat berhenti
    sy *= mendarat; sx *= 2 - mendarat;
    // giliran bicara: bila dua tokoh, bergantian tiap 2,5 detik
    const giliran = jumlah < 2 || Math.floor(s / 75) % jumlah === ke;
    if (aksi === "bicara" || aksi === "tunjuk") {
      if (giliran) { y = -Math.abs(Math.sin(q / 5)) * 9; rot = Math.sin(q / 9) * 2.5; }
      else rot = Math.sin(q / 25) * 1;
      // menoleh sebentar tiap ~4 detik (pose 3/4 dicerminkan)
      if (t.samping && Math.floor((s + ke * 50) / 120) % 2 === 1 && (s + ke * 50) % 120 < 40) file = t.samping;
      if (jumlah < 2 && Math.floor(s / 110) % 3 === 2) hadap = -hadap;
    } else if (aksi === "senang") {
      const u = (s % 28) / 28;
      y = -Math.sin(u * Math.PI) * 46;
      const tekan = u < 0.12 ? 1 - u / 0.12 : u > 0.9 ? (u - 0.9) / 0.1 : 0;
      sy *= 1 - tekan * 0.12 + Math.sin(u * Math.PI) * 0.06; sx *= 1 + tekan * 0.1;
      rot = Math.sin(u * Math.PI * 2) * 5;
    } else if (aksi === "sedih" || aksi === "nangis") {
      const turun = interpolate(s, [0, 30], [0, 1], { ...clamp, easing: theme.ease.out });
      sy *= 1 - 0.035 * turun; y = 8 * turun;
      rot = (3 + Math.sin(q / 30) * 2) * turun * hadap;
      if (aksi === "nangis") gx = Math.sin(frame * 1.7) * 2.6;                // bahu terisak
    } else if (aksi === "marah") {
      gx = (acak(q) - 0.5) * 9; rot = 4 * hadap + Math.sin(q / 3) * 1.5;
      if (Math.floor(s / 45) % 2 === 0) y = -Math.abs(Math.sin(s / 4)) * 14;   // menghentak
    } else if (aksi === "kaget") {
      y = -interpolate(s, [0, 6, 14, 22], [0, 60, -6, 0], clamp);
      sy *= interpolate(s, [0, 6, 14, 22], [1, 1.12, 0.92, 1], clamp);
      rot = interpolate(s, [0, 8, 24], [0, -8 * hadap, -3 * hadap], clamp);
    } else if (aksi === "gali") {
      const u = (s % 18) / 18;
      rot = Math.sin(u * Math.PI * 2) * 6 * hadap; y = Math.abs(Math.sin(u * Math.PI)) * 6;
    } else if (aksi === "doa") {
      rot = Math.sin(q / 26) * 1.2;
    }
    if (t.aksiFile?.length) {
      file = t.aksiFile.length > 1 ? t.aksiFile[Math.floor(s / 9) % t.aksiFile.length] : t.aksiFile[0];
    }
  }
  if (!file) return null;
  const muncul = lama ? (f >= 0 ? 1 : 0) : spring({ frame: f, fps, config: theme.spring.bouncy });
  const langkah = berjalan ? Math.floor(f / 6) : -1;
  return (
    <>
      {berjalan && langkah % 2 === 0 ? <Debu x={x} f={f % 12} kuat={0.6} /> : null}
      {!lewat && s >= 0 && s < 16 ? <Debu x={x} f={s} kuat={1} /> : null}
      <div style={{ position: "absolute", left: x + gx, top: TANAH, opacity: muncul,
        transform: `translate(-50%, -100%) translateY(${y}px) rotate(${rot}deg) scale(${hadap * sx * (lama ? 1 : muncul)}, ${sy * (lama ? 1 : muncul)})`,
        transformOrigin: "50% 100%" }}>
        <Img src={staticFile(file)} style={{ height: tinggi, filter: "drop-shadow(0 18px 18px rgba(0,0,0,0.35))" }} />
      </div>
      {!berjalan ? <Partikel aksi={aksi} x={x} puncak={TANAH - tinggi + y} f={s} arah={hadap} /> : null}
    </>
  );
};

/** Figuran latar: unta/kerumunan berjalan pelan menyeberang, atau domba merumput di tempat. */
const Figuran: React.FC<{ g: FiguranClay; ke: number }> = ({ g, ke }) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const f = dua(frame);
  let x = g.x ?? W / 2, file = g.a, y = 0;
  if (g.lewat) {
    const dariKiri = g.lewat === "kiri";
    const jarak = W + 800;
    const maju = (f * (g.laju ?? 1.6) + ke * 500 + (durationInFrames % 300)) % jarak;
    x = dariKiri ? -400 + maju : W + 400 - maju;
    if (g.b) file = Math.floor(f / 10) % 2 ? g.b : g.a;
    y = -Math.abs(Math.sin(f / 10 * Math.PI)) * 4;
    return (
      <div style={{ position: "absolute", left: x, top: g.y, transform: `translate(-50%, -100%) translateY(${y}px) scaleX(${dariKiri ? 1 : -1})`,
        transformOrigin: "50% 100%", opacity: 0.96 }}>
        <Img src={staticFile(file)} style={{ height: g.tinggi, filter: "drop-shadow(0 10px 10px rgba(0,0,0,0.3)) saturate(0.9)" }} />
      </div>
    );
  }
  if (g.b) file = Math.floor((f + ke * 37) / 50) % 2 ? g.b : g.a;
  return (
    <div style={{ position: "absolute", left: x, top: g.y, transform: `translate(-50%, -100%) rotate(${Math.sin(f / 30 + ke) * 1.5}deg)`,
      transformOrigin: "50% 100%" }}>
      <Img src={staticFile(file)} style={{ height: g.tinggi, filter: "drop-shadow(0 10px 10px rgba(0,0,0,0.3)) saturate(0.9)" }} />
    </div>
  );
};

/** Awan mendung kecil di atas tokoh yang sedih, dengan rintik hujan. */
const AwanSedih: React.FC<{ file: string; x: number; puncak: number }> = ({ file, x, puncak }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const p = spring({ frame: frame - 40, fps, config: theme.spring.bouncy });
  const f = dua(frame);
  return (
    <div style={{ position: "absolute", left: x, top: puncak - 70 + Math.sin(f / 20) * 6, transform: `translate(-50%,-50%) scale(${p})` }}>
      {[0, 1, 2, 3, 4, 5, 6].map((i) => {
        const u = ((f + i * 7) % 24) / 24;
        return <div key={i} style={{ position: "absolute", left: 40 + i * 26, top: 80 + u * 110, width: 5, height: 16, borderRadius: 4,
          background: "#8cc8f0", opacity: (1 - u) * 0.9 * (frame > 46 ? 1 : 0) }} />;
      })}
      <Img src={staticFile(file)} style={{ width: 240, filter: "brightness(0.72) saturate(0.6) drop-shadow(0 8px 10px rgba(0,0,0,0.3))" }} />
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

const Panggung: React.FC<{ a: AdeganClay }> = ({ a }) => {
  const frame = useCurrentFrame();
  const kamera = useKamera(a, 1);
  const sedih = (a.tokoh ?? []).find((t) => t.aksi === "sedih" || t.aksi === "nangis");
  // masuk adegan: sedikit "pop" kamera supaya pergantian babak terasa hidup
  const pop = interpolate(frame, [0, 10], [1.05, 1], { ...clamp, easing: theme.ease.out });
  return (
    <AbsoluteFill style={{ transform: `scale(${pop})` }}>
      <Latar a={a} />
      <Suasana a={a} />
      <AbsoluteFill style={{ transform: kamera, transformOrigin: "50% 80%" }}>
        {(a.figuran ?? []).map((g, i) => <Figuran key={`g${i}`} g={g} ke={i} />)}
        {(a.benda ?? []).map((b, i) => <Benda key={`b${i}`} b={b} ke={i} />)}
        {(a.tokoh ?? []).map((t, i) => <Tokoh key={`t${i}`} t={t} ke={i} jumlah={(a.tokoh ?? []).filter((k) => k.aksi !== "lewat").length} />)}
        {sedih && a.hujan ? <AwanSedih file={a.hujan} x={sedih.x} puncak={TANAH - (sedih.tinggi ?? TINGGI_TOKOH)} /> : null}
      </AbsoluteFill>
      {sedih ? <AbsoluteFill style={{ background: "rgba(30,50,80,0.18)", mixBlendMode: "multiply" }} /> : null}
    </AbsoluteFill>
  );
};

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
