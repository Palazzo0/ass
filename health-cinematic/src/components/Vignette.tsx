import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { PHASE_1_END, PHASE_2_END, PHASE_3_END, getPhaseProgress } from "../utils/phases";

export const Vignette: React.FC = () => {
  const frame = useCurrentFrame();
  const { durationInFrames, fps } = useVideoConfig();

  const p1 = getPhaseProgress(frame, durationInFrames, 0, PHASE_1_END);
  const p2 = getPhaseProgress(frame, durationInFrames, 0.38, PHASE_2_END);
  const p3 = getPhaseProgress(frame, durationInFrames, PHASE_2_END, PHASE_3_END);

  const baseOpacity = interpolate(p1, [0, 1], [0.55, 0.72], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const p2Boost    = interpolate(p2, [0, 1], [0, 0.14], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const p3Boost    = interpolate(p3, [0, 1], [0, 0.20], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  // Very slow breathing movement
  const breathe    = 0.012 * Math.sin((frame / fps) * 0.45);

  const vignetteOpacity = baseOpacity + p2Boost + p3Boost + breathe;

  // Red atmospheric tint on edges — builds in phase 2, fades phase 3
  const redEdge = interpolate(p2, [0, 0.3, 1], [0, 0.10, 0.20], { extrapolateLeft: "clamp", extrapolateRight: "clamp" })
    * interpolate(p3, [0, 0.5, 1], [1, 0.6, 0.2], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      {/* Primary dark vignette */}
      <AbsoluteFill
        style={{
          background:
            "radial-gradient(ellipse at 50% 44%, transparent 22%, rgba(0,0,0,0.68) 62%, rgba(0,0,0,0.96) 100%)",
          opacity: vignetteOpacity,
        }}
      />
      {/* Red atmospheric edge in phase 2 */}
      <AbsoluteFill
        style={{
          background:
            "radial-gradient(ellipse at 50% 50%, transparent 30%, rgba(90,0,0,0.82) 100%)",
          opacity: redEdge,
        }}
      />
    </AbsoluteFill>
  );
};
