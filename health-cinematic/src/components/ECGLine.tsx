import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { PHASE_1_END, PHASE_2_END, getPhaseProgress } from "../utils/phases";

const BEAT_FRAMES = 36; // 72 bpm at 30fps
const SAMPLES = 300;
const W = 720;
const H = 80;

function ecgY(rawPhase: number): number {
  const p = ((rawPhase % 1) + 1) % 1;
  if (p < 0.05) return 0;
  if (p < 0.12) return 0.12 * Math.sin(((p - 0.05) / 0.07) * Math.PI); // P wave
  if (p < 0.17) return 0;
  if (p < 0.195) return -0.09; // Q dip
  if (p < 0.215) return -1.0;  // R spike
  if (p < 0.235) return 0.22;  // S dip
  if (p < 0.28) return 0;
  if (p < 0.44) return 0.22 * Math.sin(((p - 0.28) / 0.16) * Math.PI); // T wave
  return 0;
}

export const ECGLine: React.FC = () => {
  const frame = useCurrentFrame();
  const { durationInFrames, width, height } = useVideoConfig();

  const p2 = getPhaseProgress(frame, durationInFrames, PHASE_1_END, PHASE_2_END);
  const p3 = getPhaseProgress(frame, durationInFrames, PHASE_2_END, 1.0);

  const opacity =
    interpolate(p2, [0, 0.18, 1], [0, 0.8, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) *
    interpolate(p3, [0, 0.35, 1], [1, 0.45, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  if (opacity < 0.005) return null;

  const framesPerSample = (BEAT_FRAMES * 2.5) / SAMPLES;
  const pts: string[] = [];

  for (let j = 0; j < SAMPLES; j++) {
    const sf = frame - (SAMPLES - 1 - j) * framesPerSample;
    const x = (j / (SAMPLES - 1)) * W;
    const y = H / 2 - ecgY(sf / BEAT_FRAMES) * (H / 2 - 5);
    pts.push(`${x.toFixed(1)},${y.toFixed(1)}`);
  }

  const pStr = pts.join(" ");
  const cx = width / 2;
  const cy = height * 0.855;
  const cursorY = cy - H / 2 + (H / 2 - ecgY(frame / BEAT_FRAMES) * (H / 2 - 5));

  return (
    <AbsoluteFill style={{ pointerEvents: "none", opacity }}>
      <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} style={{ position: "absolute", inset: 0 }}>
        <defs>
          <linearGradient id="ecgFadeGrad" x1="0" x2="1" y1="0" y2="0">
            <stop offset="0%" stopColor="white" stopOpacity="0" />
            <stop offset="30%" stopColor="white" stopOpacity="0.25" />
            <stop offset="70%" stopColor="white" stopOpacity="0.8" />
            <stop offset="100%" stopColor="white" stopOpacity="1" />
          </linearGradient>
          <mask id="ecgFadeMask">
            <rect x="0" y="0" width={W} height={H} fill="url(#ecgFadeGrad)" />
          </mask>
        </defs>

        <g transform={`translate(${cx - W / 2},${cy - H / 2})`} mask="url(#ecgFadeMask)">
          {/* glow halo */}
          <polyline
            points={pStr}
            fill="none"
            stroke="rgba(255,65,45,0.5)"
            strokeWidth={6}
            style={{ filter: "blur(6px)" }}
          />
          {/* bright core */}
          <polyline
            points={pStr}
            fill="none"
            stroke="rgba(255,140,90,0.92)"
            strokeWidth={1.8}
            strokeLinejoin="round"
          />
        </g>

        {/* cursor dot at current position */}
        <circle cx={cx + W / 2} cy={cursorY} r={3.5} fill="rgba(255,180,100,1)" />
        <circle cx={cx + W / 2} cy={cursorY} r={7} fill="rgba(255,100,60,0.35)" style={{ filter: "blur(3px)" }} />
      </svg>
    </AbsoluteFill>
  );
};
