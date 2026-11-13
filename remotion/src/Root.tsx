import React from "react";
import { AbsoluteFill, Audio, Composition, Sequence, cancelRender, continueRender, delayRender, staticFile } from "remotion";
import { FONTS } from "./fontdata";
import data from "./data.json";
import { Grade, Grain, Kepala, Latar, Vignette } from "./Layers";
import { Dalil, Faedah, Hook, Penutup, Poin, Segmen } from "./Scenes";
import { Ilustrasi, JENIS, POSE } from "./Ilustrasi";

const FPS = 30;

// Font dimuat dari data yang ditanam (bukan lewat jaringan): pemuatan lewat URL kadang menggantung saat render.
const tunggu = delayRender("font");
Promise.all(FONTS.map(({ family, weight, b64 }) => {
  const biner = Uint8Array.from(atob(b64), (c) => c.charCodeAt(0));
  const f = new FontFace(family, biner.buffer, { weight });
  document.fonts.add(f);
  return f.load();
})).then(() => continueRender(tunggu), (e) => cancelRender(e));

type Data = { kicker: string; handle?: string; durasi: number; frame?: number; audio?: string; segmen: Segmen[] };

const ADEGAN = { hook: Hook, poin: Poin, dalil: Dalil, faedah: Faedah, penutup: Penutup } as const;

/** Lapisan dari bawah ke atas: latar -> adegan -> kepala -> grade -> grain -> vignette. */
const Video: React.FC<Data> = ({ kicker, handle, audio, segmen }) => {
  const batas = segmen.map((s) => Math.round(s.mulai * FPS));
  return (
    <AbsoluteFill>
      <Latar />
      {segmen.map((s, i) => {
        const Adegan = ADEGAN[s.jenis];
        const akhir = i + 1 < segmen.length ? batas[i + 1] : Math.round(s.akhir * FPS);
        return (
          <Sequence key={i} from={batas[i]} durationInFrames={akhir - batas[i]}>
            <Adegan s={s} />
          </Sequence>
        );
      })}
      <Kepala kicker={kicker} handle={handle ?? "@sun_nahdaily"} batas={batas} />
      <Grade />
      <Grain />
      <Vignette />
      {audio ? <Audio src={staticFile(audio)} /> : null}
    </AbsoluteFill>
  );
};

/** Lembar periksa: semua ilustrasi dalam satu layar (bukan untuk tayang). */
const Galeri: React.FC = () => (
  <AbsoluteFill style={{ background: "#0C1A1D", padding: 30, display: "flex", flexDirection: "row", flexWrap: "wrap", gap: 18, alignContent: "flex-start" }}>
    {JENIS.map((j, i) => (
      <div key={j} style={{ width: 328 }}>
        <Ilustrasi jenis={j} tokoh={i % 5 === 4 ? "" : POSE[i % 4]} tinggi={520} lebar={328} />
        <div style={{ color: "#F6F1E7", fontFamily: "Poppins", fontSize: 24, marginTop: 6 }}>{j}{i % 5 === 4 ? "" : ` + ${POSE[i % 4]}`}</div>
      </div>
    ))}
  </AbsoluteFill>
);

export const Root: React.FC = () => (
  <>
    <Composition
      id="SunnahDaily"
      component={Video}
      width={1080}
      height={1920}
      fps={FPS}
      durationInFrames={Math.ceil((data as Data).durasi * FPS)}
      defaultProps={data as Data}
      calculateMetadata={({ props }) => ({ durationInFrames: props.frame ?? Math.ceil(props.durasi * FPS) })}
    />
    <Composition id="Galeri" component={Galeri} width={1080} height={1920} fps={FPS} durationInFrames={300} />
  </>
);
