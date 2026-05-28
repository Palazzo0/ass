export const seeded = (seed: number): number => {
  const x = Math.sin(seed + 1) * 10000;
  return x - Math.floor(x);
};

export const seededRange = (seed: number, min: number, max: number): number =>
  min + seeded(seed) * (max - min);
