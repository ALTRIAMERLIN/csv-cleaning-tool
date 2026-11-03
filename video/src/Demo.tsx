import React from 'react';
import {AbsoluteFill, Sequence} from 'remotion';
import {Intro} from './Intro';
import {Outro} from './Outro';
import {Caption, Clip, Fade, RecordingBadge} from './parts';
import {C, data} from './theme';
import {Verify} from './Verify';

const c = data.counts;
const r = data.rules;

/**
 * Edit decision list. `raw` is the start second in demo/recording/raw_recording.mp4 (see the
 * timeline in demo/demo_manifest.json). Every clip plays at normal speed; only the gaps
 * between clips are cut. Zoom rectangles are in pixels of the 1920x1080 recording.
 */
const SEGMENTS = [
  {id: 'intro', frames: 150},
  {id: 'upload', frames: 240, raw: 1.6},
  {id: 'rules', frames: 420, raw: 13.9},
  {id: 'results', frames: 120, raw: 29.4},
  {id: 'issues', frames: 135, raw: 35.1},
  {id: 'changes', frames: 75, raw: 39.8},
  {id: 'download', frames: 300, raw: 49.0},
  {id: 'outro', frames: 210},
] as const;

export const TOTAL_FRAMES = SEGMENTS.reduce((n, s) => n + s.frames, 0);

const starts = SEGMENTS.reduce<Record<string, number>>((acc, s, i) => {
  acc[s.id] = i === 0 ? 0 : acc[SEGMENTS[i - 1].id] + SEGMENTS[i - 1].frames;
  return acc;
}, {});

const seg = (id: (typeof SEGMENTS)[number]['id']) => {
  const s = SEGMENTS.find((x) => x.id === id)!;
  return {from: starts[id], frames: s.frames, raw: 'raw' in s ? s.raw : 0};
};

const Piece: React.FC<{id: (typeof SEGMENTS)[number]['id']; children: React.ReactNode}> = ({
  id,
  children,
}) => {
  const s = seg(id);
  return (
    <Sequence from={s.from} durationInFrames={s.frames} name={id}>
      <Fade duration={s.frames} edge={id === 'issues' || id === 'changes' ? 5 : 8}>
        {children}
      </Fade>
    </Sequence>
  );
};

export const Demo: React.FC = () => (
  <AbsoluteFill style={{backgroundColor: C.bg}}>
    <Piece id="intro">
      <Intro />
    </Piece>

    <Piece id="upload">
      <Clip startSec={seg('upload').raw} zoom={{at: 150, rect: {x: 60, y: 110, w: 1500, h: 260}}} />
      <RecordingBadge />
      <Caption from={0} to={108} step="1">
        Upload a CSV file (here: the synthetic sample, {data.input.rows} rows)
      </Caption>
      <Caption from={110} to={240} step="2">
        Preview: {data.input.rows} rows · {data.input.columns} columns ·{' '}
        {c.field_count_mismatch_rows} rows with the wrong field count
      </Caption>
    </Piece>

    <Piece id="rules">
      <Clip startSec={seg('rules').raw} zoom={{at: 18, rect: {x: 60, y: 560, w: 1640, h: 420}}} />
      <RecordingBadge />
      <Caption from={0} to={110} step="3">
        Choose the rules from the file&apos;s own columns
      </Caption>
      <Caption from={112} to={372}>
        Trim spaces · required fields · email format · duplicates by{' '}
        {r.dedupe_keys.join(', ')} (keep {r.dedupe_keep})
      </Caption>
      <Caption from={374} to={420} step="4">
        Run
      </Caption>
    </Piece>

    <Piece id="results">
      <Clip startSec={seg('results').raw} zoom={{at: 6, rect: {x: 60, y: 60, w: 1500, h: 260}}} />
      <RecordingBadge />
      <Caption from={0} to={120} step="5">
        {c.input_rows} rows in = {c.clean_rows} clean + {c.issue_rows} issues: every row accounted for
      </Caption>
    </Piece>

    <Piece id="issues">
      <Clip
        startSec={seg('issues').raw}
        zoom={{at: 20, rect: {x: 60, y: 330, w: 1000, h: 470}, max: 1.5}}
      />
      <RecordingBadge />
      <Caption from={0} to={135}>
        Issue rows keep their values and the reason they were not kept
      </Caption>
    </Piece>

    <Piece id="changes">
      <Clip startSec={seg('changes').raw} zoom={{at: -20, rect: {x: 0, y: 0, w: 1670, h: 939}}} />
      <RecordingBadge />
      <Caption from={0} to={75}>
        Change log: {c.changed_cells} trimmed cells, old value → new value
      </Caption>
    </Piece>

    <Piece id="download">
      <Clip startSec={seg('download').raw} zoom={{at: 75, rect: {x: 60, y: 560, w: 1500, h: 380}}} />
      <RecordingBadge />
      <Verify from={210} />
      <Caption from={0} to={205} step="6">
        Download clean.csv, issues.csv, changes.csv and summary.json
      </Caption>
      <Caption from={210} to={300}>
        Checked: each download is byte-identical to the command-line output
      </Caption>
    </Piece>

    <Piece id="outro">
      <Outro />
    </Piece>
  </AbsoluteFill>
);
