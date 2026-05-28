import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { Video } from "@remotion/media";
import { staticFile } from "remotion";

export const VideoBase: React.FC = () => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  // Slow push-in: scale 1.0 → 1.055 over the full duration
  const scale = interpolate(frame, [0, durationInFrames], [1.0, 1.055], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Slight upward drift to keep the face centered as we zoom in
  const translateY = interpolate(frame, [0, durationInFrames], [0, -20], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{ overflow: "hidden" }}>
      <AbsoluteFill
        style={{
          transform: `scale(${scale}) translateY(${translateY}px)`,
          transformOrigin: "50% 40%",
        }}
      >
        <Video
          src={staticFile("doctor.mp4")}
          style={{ width: "100%", height: "100%", objectFit: "cover" }}
        />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
