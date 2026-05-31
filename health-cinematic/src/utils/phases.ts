// Dialogue phase timing as fraction of total video duration (~37 s)
// Phase 1: "blood vessels carry oxygen and nutrients…" intro setup
// Phase 2: lifestyle habits — sedentary, smoking, diet, hypertension, meds, inflammation
// Phase 3: plaque formation — "cholesterol sticks to the walls…"
// Phase 4: narrowing — "smaller and tighter… that's when things get dangerous"

export const PHASE_1_START = 0;
export const PHASE_1_END   = 0.24;   // 0 → 24%  (~0–8.9 s)
export const PHASE_2_START = 0.22;
export const PHASE_2_END   = 0.58;   // 22 → 58% (~8.2–21.6 s)
export const PHASE_3_START = 0.56;
export const PHASE_3_END   = 1.0;    // 56 → 100% (~20.9–37.3 s)
export const PHASE_4_START = 0.80;
export const PHASE_4_END   = 1.0;    // 80 → 100% (~29.8–37.3 s)

export const getPhaseProgress = (
  frame: number,
  durationInFrames: number,
  start: number,
  end: number
): number => {
  const startFrame = durationInFrames * start;
  const endFrame   = durationInFrames * end;
  if (frame <= startFrame) return 0;
  if (frame >= endFrame)   return 1;
  return (frame - startFrame) / (endFrame - startFrame);
};
