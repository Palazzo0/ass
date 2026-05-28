import React from "react";
import { AbsoluteFill } from "remotion";
import { VideoBase } from "./components/VideoBase";
import { Vignette } from "./components/Vignette";
import { SmokeParticles } from "./components/SmokeParticles";
import { DustMotes } from "./components/DustMotes";
import { ArteryOverlay } from "./components/ArteryOverlay";
import { BloodCells } from "./components/BloodCells";
import { HeartbeatGlow } from "./components/HeartbeatGlow";
import { CholesterolParticles } from "./components/CholesterolParticles";
import { AtmosphericFade } from "./components/AtmosphericFade";

export const CinematicOverlay: React.FC = () => {
  return (
    <AbsoluteFill style={{ background: "#000", overflow: "hidden" }}>
      {/* 1. Source footage — fills full canvas with cinematic push-in */}
      <VideoBase />

      {/* 2. Cinematic vignette — dark edges, phase-driven */}
      <Vignette />

      {/* 3. Drifting smoke atmosphere */}
      <SmokeParticles />

      {/* 4. Warm floating dust motes in light shafts */}
      <DustMotes />

      {/* 5. Transparent artery network — emerges, glows, narrows */}
      <ArteryOverlay />

      {/* 6. Flowing blood cell particles — slow in phase 3 */}
      <BloodCells />

      {/* 7. Heartbeat pulse glow — builds in phase 2 */}
      <HeartbeatGlow />

      {/* 8. Cholesterol particles — appear in phase 2 */}
      <CholesterolParticles />

      {/* 9. Atmospheric fades and cinematic grade */}
      <AtmosphericFade />
    </AbsoluteFill>
  );
};
