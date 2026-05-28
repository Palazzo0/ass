import React from "react";
import { AbsoluteFill } from "remotion";
import { VideoBase } from "./components/VideoBase";
import { Vignette } from "./components/Vignette";
import { SmokeParticles } from "./components/SmokeParticles";
import { DustMotes } from "./components/DustMotes";
import { ArteryOverlay } from "./components/ArteryOverlay";
import { BloodCells } from "./components/BloodCells";
import { HeartbeatGlow } from "./components/HeartbeatGlow";
import { AtmosphericFade } from "./components/AtmosphericFade";

export const CinematicOverlay: React.FC = () => {
  return (
    <AbsoluteFill style={{ background: "#000", overflow: "hidden" }}>
      {/* Layer 1: Source footage with push-in zoom */}
      <VideoBase />

      {/* Layer 2: Dark cinematic vignette */}
      <Vignette />

      {/* Layer 3: Drifting smoke atmosphere */}
      <SmokeParticles />

      {/* Layer 4: Warm floating dust motes */}
      <DustMotes />

      {/* Layer 5: Artery texture overlay with narrowing effect */}
      <ArteryOverlay />

      {/* Layer 6: Blood cell particles */}
      <BloodCells />

      {/* Layer 7: Heartbeat glow pulse */}
      <HeartbeatGlow />

      {/* Layer 8: Atmospheric entry/exit fades + warm grade */}
      <AtmosphericFade />
    </AbsoluteFill>
  );
};
