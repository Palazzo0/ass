import "./index.css";
import React from "react";
import { Composition, CalculateMetadataFunction, staticFile } from "remotion";
import { CinematicOverlay } from "./CinematicOverlay";
import { Input, ALL_FORMATS, UrlSource } from "mediabunny";

const calculateMetadata: CalculateMetadataFunction<Record<string, unknown>> =
  async () => {
    const input = new Input({
      formats: ALL_FORMATS,
      source: new UrlSource(staticFile("doctor.mp4"), {
        getRetryDelay: () => null,
      }),
    });

    const durationInSeconds = await input.computeDuration();
    const fps = 30;

    return {
      durationInFrames: Math.ceil(durationInSeconds * fps),
      fps,
      width: 1080,
      height: 1920,
    };
  };

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="HealthCinematic"
      component={CinematicOverlay}
      durationInFrames={600}
      fps={30}
      width={1080}
      height={1920}
      calculateMetadata={calculateMetadata}
    />
  );
};
