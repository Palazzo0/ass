// Dialogue phase timing as fraction of total video duration
// Phase 1: "Many of the things you do every day are slowly blocking your blood vessels…"
// Phase 2: "you may not even know it until it causes a stroke or heart attack"
// Phase 3: "The scary part is that for many people, it starts years before the symptoms even appear"

export const PHASE_1_START = 0;
export const PHASE_1_END = 0.40;   // 0 → 40%
export const PHASE_2_START = 0.38;
export const PHASE_2_END = 0.72;   // 38 → 72%
export const PHASE_3_START = 0.70;
export const PHASE_3_END = 1.0;    // 70 → 100%

export const getPhaseProgress = (
  frame: number,
  durationInFrames: number,
  start: number,
  end: number
): number => {
  const startFrame = durationInFrames * start;
  const endFrame = durationInFrames * end;
  if (frame <= startFrame) return 0;
  if (frame >= endFrame) return 1;
  return (frame - startFrame) / (endFrame - startFrame);
};
