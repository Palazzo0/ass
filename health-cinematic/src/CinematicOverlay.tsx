import React from "react";
import { AbsoluteFill } from "remotion";
import { VideoBase } from "./components/VideoBase";
import { SilhouetteOverlay } from "./components/SilhouetteOverlay";
import { Vignette } from "./components/Vignette";
import { SmokeParticles } from "./components/SmokeParticles";
import { DustMotes } from "./components/DustMotes";
import { ArteryOverlay } from "./components/ArteryOverlay";
import { BloodCells } from "./components/BloodCells";
import { HeartbeatGlow } from "./components/HeartbeatGlow";
import { CholesterolParticles } from "./components/CholesterolParticles";
import { ECGLine } from "./components/ECGLine";
import { BlockageFlash } from "./components/BlockageFlash";
import { AtmosphericFade } from "./components/AtmosphericFade";
import { FilmGrain } from "./components/FilmGrain";
import { AudioLayer } from "./components/AudioLayer";

export const CinematicOverlay: React.FC = () => {
  return (
    <AbsoluteFill style={{ background: "#000", overflow: "hidden" }}>
      {/* 1. Source footage — fills full canvas with cinematic push-in */}
      <VideoBase />

      {/* 2. Lifestyle silhouette scenes — sync to opening narration */}
      <SilhouetteOverlay />

      {/* 3. Drifting smoke atmosphere */}
      <SmokeParticles />

      {/* 4. Warm floating dust motes */}
      <DustMotes />

      {/* 5. Transparent artery network — draws progressively, glows, narrows */}
      <ArteryOverlay />

      {/* 5. Flowing blood cell particles — slows to crawl in phase 3 */}
      <BloodCells />

      {/* 6. Heartbeat pulse glow — builds in phase 2 */}
      <HeartbeatGlow />

      {/* 7. Cholesterol particles — float phase 1, fly toward camera phase 2 */}
      <CholesterolParticles />

      {/* 8. ECG trace — appears in phase 2 */}
      <ECGLine />

      {/* 9. Red blockage flash at "stroke or heart attack" moment */}
      <BlockageFlash />

      {/* 10. Cinematic vignette — dark edges, red tint in phase 2 */}
      <Vignette />

      {/* 11. Very subtle film grain for cinematic texture */}
      <FilmGrain />

      {/* 12. Atmospheric fades, warm grade, phase 3 desaturation, fade in/out */}
      <AtmosphericFade />

      {/* 13. Audio: drone + heartbeat loop + boom + tension riser */}
      <AudioLayer />
    </AbsoluteFill>
  );
};
