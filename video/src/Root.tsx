import React from 'react';
import {Composition, Still} from 'remotion';
import {Cover} from './Cover';
import {Demo, TOTAL_FRAMES} from './Demo';
import {FPS} from './theme';

export const RemotionRoot: React.FC = () => (
  <>
    <Composition
      id="CsvCleanDemo"
      component={Demo}
      durationInFrames={TOTAL_FRAMES}
      fps={FPS}
      width={1920}
      height={1080}
    />
    <Still id="CsvCleanCover" component={Cover} width={2000} height={1500} />
  </>
);
