import React from 'react';
import {Composition} from 'remotion';
import {Demo, TOTAL_FRAMES} from './Demo';
import {FPS} from './theme';

export const RemotionRoot: React.FC = () => (
  <Composition
    id="CsvCleanDemo"
    component={Demo}
    durationInFrames={TOTAL_FRAMES}
    fps={FPS}
    width={1920}
    height={1080}
  />
);
