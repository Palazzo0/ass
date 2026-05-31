import React from "react";
import {
  Audio,
  Sequence,
  interpolate,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import {
  PHASE_1_END,
  PHASE_2_END,
  PHASE_3_START,
  getPhaseProgress,
} from "../utils/phases";

export const AudioLayer: React.FC = () => {
  useCurrentFrame(); // keep hook call order stable
  const { durationInFrames, fps } = useVideoConfig();

  // Drone: present throughout, builds in phase 2
  const droneVol = (f: number) =>
    interpolate(
      f,
      [0, fps * 1.5, durationInFrames - fps * 2.5, durationInFrames],
      [0, 0.38, 0.32, 0],
      { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
    ) * (1 + 0.3 * getPhaseProgress(f, durationInFrames, PHASE_1_END, PHASE_2_END));

  // Heartbeat loop: faint phase 1, prominent phase 2, silent phase 3
  const hbVol = (f: number) => {
    const p = getPhaseProgress(f, durationInFrames, 0, PHASE_2_END);
    const p3fade = getPhaseProgress(f, durationInFrames, PHASE_2_END, 1.0);
    return (
      interpolate(p, [0, 0.15, 0.5, 1], [0, 0.10, 0.42, 0.36], {
        extrapolateLeft: "clamp",
        extrapolateRight: "clamp",
      }) *
      interpolate(p3fade, [0, 0.4, 0.9, 1], [1, 0.7, 0.15, 0], {
        extrapolateLeft: "clamp",
        extrapolateRight: "clamp",
      })
    );
  };

  // Boom: triggered at ~72% — "what we doctors call plaque"
  const boomStart = Math.round(durationInFrames * 0.72);

  // Riser: starts at phase 3 onset, builds and then fades
  const riserStart = Math.round(durationInFrames * PHASE_3_START);
  const riserVol = (f: number) => {
    const rFrame = f - riserStart;
    return interpolate(
      rFrame,
      [0, fps * 1.5, fps * 5, fps * 7],
      [0, 0.28, 0.38, 0.1],
      { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
    );
  };

  return (
    <>
      {/* Ambient cinematic drone — full duration */}
      <Audio src={staticFile("sounds/drone.wav")} volume={droneVol} />

      {/* Heartbeat loop — looped throughout */}
      <Audio src={staticFile("sounds/heartbeat-loop.wav")} volume={hbVol} loop />

      {/* Cinematic boom at "stroke or heart attack" */}
      <Sequence from={boomStart} durationInFrames={Math.round(fps * 2.5)}>
        <Audio src={staticFile("sounds/boom.wav")} volume={0.72} />
      </Sequence>

      {/* Tension riser in phase 3 */}
      <Sequence from={riserStart} durationInFrames={Math.round(fps * 8)}>
        <Audio src={staticFile("sounds/riser.wav")} volume={riserVol} />
      </Sequence>
    </>
  );
};
