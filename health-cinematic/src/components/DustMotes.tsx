import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { seededRange } from "../utils/noise";

const MOTE_COUNT = 30;

const MOTES = Array.from({ length: MOTE_COUNT }, (_, i) => ({
  x:      seededRange(i * 11 + 1, 5, 95),
  y:      seededRange(i * 11 + 2, 10, 90),
  size:   seededRange(i * 11 + 3, 2, 5),
  speedY: seededRange(i * 11 + 4, -0.007, -0.002),
  speedX: seededRange(i * 11 + 5, -0.004, 0.004),
  opacity: seededRange(i * 11 + 6, 0.35, 0.65),
  phase:  seededRange(i * 11 + 7, 0, 600),
  hue:    seededRange(i * 11 + 8, 0, 1),
}));

export const DustMotes: React.FC = () => {
  const frame = useCurrentFrame();
  useVideoConfig();

  const globalFade = interpolate(frame, [0, 40], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  return (
    <AbsoluteFill style={{ pointerEvents: "none", overflow: "hidden" }}>
      {MOTES.map((mote, i) => {
        const t = (frame + mote.phase * 600) % 900;
        const y = mote.y + mote.speedY * t;
        const x = mote.x + mote.speedX * t + Math.sin(t * 0.012 + mote.phase * 6) * 2;

        const g = Math.round(175 + mote.hue * 55);
        const b = Math.round(70 + mote.hue * 80);

        const twinkle = 0.65 + 0.35 * Math.sin(frame * 0.09 + mote.phase * 10);
        const opacity = mote.opacity * twinkle * globalFade;

        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: `${x}%`,
              top: `${y}%`,
              width: mote.size,
              height: mote.size,
              borderRadius: "50%",
              background: `rgba(255,${g},${b},1)`,
              filter: `blur(${mote.size * 0.35}px)`,
              opacity,
              transform: "translate(-50%, -50%)",
            }}
          />
        );
      })}
    </AbsoluteFill>
  );
};
