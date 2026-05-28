import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";

// 72 bpm = 1.2s per beat = 36 frames at 30fps
const BEAT_INTERVAL = 36;

// Create a sharp attack + slow decay for each heartbeat
const heartbeatPulse = (frame: number): number => {
  const phase = ((frame % BEAT_INTERVAL) / BEAT_INTERVAL);
  // Two beats per measure for realism (lub-dub)
  const lub = phase < 0.5 ? phase * 2 : 0;
  const dub = phase >= 0.5 ? (phase - 0.5) * 2 : 0;

  const lubPulse = interpolate(lub, [0, 0.08, 0.5], [0, 1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const dubPulse = interpolate(dub, [0, 0.08, 0.5], [0, 0.55, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return Math.max(lubPulse, dubPulse);
};

export const HeartbeatGlow: React.FC = () => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  const pulse = heartbeatPulse(frame);

  // Heartbeat builds in intensity toward the warning climax
  const intensityRamp = interpolate(
    frame,
    [0, durationInFrames * 0.3, durationInFrames * 0.7, durationInFrames],
    [0.3, 0.5, 0.85, 0.7],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  const opacity = pulse * 0.12 * intensityRamp;

  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      {/* Primary glow — warm amber/red centered slightly below mid (chest area) */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background:
            "radial-gradient(ellipse 60% 40% at 50% 65%, rgba(220,80,40,1) 0%, rgba(180,40,20,0.5) 35%, transparent 75%)",
          opacity,
        }}
      />
      {/* Secondary subtle rim on edges for dramatic feel */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background:
            "radial-gradient(ellipse at 50% 50%, transparent 50%, rgba(120,20,20,0.6) 100%)",
          opacity: pulse * 0.06 * intensityRamp,
        }}
      />
    </AbsoluteFill>
  );
};
