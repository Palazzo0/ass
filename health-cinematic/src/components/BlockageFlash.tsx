import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";

// Three staggered red flashes + screen-edge shock burst at the
// "stroke or heart attack" moment (~65% of video duration).
// Also adds a secondary deep-red wash at phase 2 peak.
export const BlockageFlash: React.FC = () => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  // Main flash onset
  const flashFrame = Math.round(durationInFrames * 0.645);

  const getFlash = () => {
    const r = frame - flashFrame;
    if (r < 0 || r > 72) return 0;
    // Flash 1: r 0-8
    if (r < 8)  return interpolate(r, [0, 3, 6, 8], [0, 0.42, 0.38, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
    // gap 8-22
    if (r < 22) return 0;
    // Flash 2: r 22-30
    if (r < 30) return interpolate(r - 22, [0, 3, 5, 8], [0, 0.32, 0.28, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
    // gap 30-46
    if (r < 46) return 0;
    // Flash 3 (soft): r 46-54
    if (r < 54) return interpolate(r - 46, [0, 3, 5, 8], [0, 0.18, 0.14, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
    return 0;
  };

  const flashOpacity = getFlash();

  // Sustained red wash that builds just before flash and lingers briefly
  const washOpacity = interpolate(
    frame,
    [flashFrame - 15, flashFrame, flashFrame + 10, flashFrame + 45, flashFrame + 80],
    [0, 0.08, 0.14, 0.06, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      {/* Sustained warm red wash */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background:
            "radial-gradient(ellipse at 50% 50%, rgba(160,0,0,0.6) 0%, rgba(100,0,0,0.9) 100%)",
          opacity: washOpacity,
          mixBlendMode: "screen" as const,
        }}
      />
      {/* Flash burst — edge-weighted so center (doctor) stays readable */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background:
            "radial-gradient(ellipse 80% 70% at 50% 50%, rgba(200,20,0,0.2) 0%, rgba(220,30,10,0.85) 100%)",
          opacity: flashOpacity,
        }}
      />
    </AbsoluteFill>
  );
};
