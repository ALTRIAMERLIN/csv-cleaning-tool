import React from 'react';
import {AbsoluteFill, Easing, interpolate, useCurrentFrame} from 'remotion';
import {C, SANS, TESTS_PASSED} from './theme';

const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

const POINTS = [
  'Trims spaces, checks required fields and email format, removes duplicates',
  'Never drops a row silently: every issue keeps its reason',
  'Writes clean.csv, issues.csv, a change log and summary.json',
  'Same input and rules give the same output files',
  'One shared Python core for the web app and the command line',
  ...(TESTS_PASSED !== null ? [`${TESTS_PASSED} automated tests (pytest), all passing`] : []),
];

export const Outro: React.FC = () => {
  const frame = useCurrentFrame();
  const head = interpolate(frame, [0, 12], [0, 1], clamp);
  const label = interpolate(frame, [70, 84], [0, 1], {...clamp, easing: Easing.out(Easing.cubic)});
  return (
    <AbsoluteFill style={{backgroundColor: C.bg, fontFamily: SANS, color: C.text}}>
      <div style={{position: 'absolute', left: 140, top: 110, opacity: head}}>
        <div style={{fontSize: 66, fontWeight: 700}}>CSV Data Cleaning &amp; Validation Tool</div>
        <div style={{fontSize: 30, color: C.muted, marginTop: 8}}>
          Python · Streamlit · command line
        </div>
      </div>
      <div style={{position: 'absolute', left: 140, top: 330}}>
        {POINTS.map((p, i) => {
          const o = interpolate(frame, [14 + i * 7, 24 + i * 7], [0, 1], clamp);
          return (
            <div
              key={p}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 22,
                height: 72,
                fontSize: 36,
                opacity: o,
                transform: `translateX(${(1 - o) * 24}px)`,
              }}
            >
              <span style={{color: C.green, fontWeight: 700}}>✓</span>
              {p}
            </div>
          );
        })}
      </div>
      <div
        style={{
          position: 'absolute',
          right: 140,
          bottom: 100,
          padding: '18px 34px',
          borderRadius: 16,
          border: `3px solid ${C.amber}`,
          color: C.amber,
          fontSize: 40,
          fontWeight: 700,
          opacity: label,
        }}
      >
        Personal demo · Synthetic data
      </div>
    </AbsoluteFill>
  );
};
