import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import {
  PHASE_1_END,
  PHASE_2_END,
  PHASE_3_END,
  getPhaseProgress,
} from "../utils/phases";

export const Vignette: React.FC = () => {
  const frame = useCurrentFrame();
  const { durationInFrames, fps } = useVideoConfig();

  // Phase 1: standard cinematic vignette
  // Phase 2: deepens and adds warm red tint
  // Phase 3: heavy, oppressive shadow
  const p1 = getPhaseProgress(frame, durationInFrames, 0, PHASE_1_END);
  const p2 = getPhaseProgress(frame, durationInFrames, 0.38, PHASE_2_END);
  const p3 = getPhaseProgress(frame, durationInFrames, PHASE_2_END, PHASE_3_END);

  const baseOpacity = interpolate(p1, [0, 1], [0.58, 0.72], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const midBoost  = interpolate(p2, [0, 1], [0, 0.13], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const endBoost  = interpolate(p3, [0, 1], [0, 0.18], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const breathe   = Math.sin((frame / fps) * 0.5) * 0.01;

  const vignetteOpacity = baseOpacity + midBoost + endBoost + breathe;

  // Red tint that builds in phase 2
  const redOpacity = interpolate(p2, [0, 1], [0, 0.18], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      {/* Dark vignette */}
      <AbsoluteFill
        style={{
          background:
            "radial-gradient(ellipse at 50% 44%, transparent 25%, rgba(0,0,0,0.65) 65%, rgba(0,0,0,0.95) 100%)",
          opacity: vignetteOpacity,
        }}
      />
      {/* Warm red atmospheric tint in phase 2 */}
      <AbsoluteFill
        style={{
          background:
            "radial-gradient(ellipse at 50% 50%, transparent 35%, rgba(80,0,0,0.8) 100%)",
          opacity: redOpacity,
        }}
      />
    </AbsoluteFill>
  );
};
