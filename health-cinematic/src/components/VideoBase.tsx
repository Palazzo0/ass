import React from "react";
import {
  AbsoluteFill,
  interpolate,
  OffthreadVideo,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

export const VideoBase: React.FC = () => {
  const frame = useCurrentFrame();
  const { durationInFrames, width, height } = useVideoConfig();

  // Slow cinematic push-in over full duration
  const scale = interpolate(frame, [0, durationInFrames], [1.0, 1.07], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{ overflow: "hidden", background: "#000" }}>
      <AbsoluteFill
        style={{
          transform: `scale(${scale})`,
          transformOrigin: "50% 42%",
        }}
      >
        <OffthreadVideo
          src={staticFile("doctor.mp4")}
          style={{
            position: "absolute",
            top: 0,
            left: 0,
            width,
            height,
            objectFit: "cover",
          }}
        />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
