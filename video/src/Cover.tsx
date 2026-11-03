import React from 'react';
import {AbsoluteFill, Img, staticFile} from 'remotion';
import {C, data, SANS} from './theme';

/** Portfolio cover, 2000x1500 (4:3, Upwork recommends 1000x750). Real screenshot, real counts. */
const SHOT = {x: 40, y: 60, w: 1840, h: 760}; // crop of demo/screens/04_issues.png

const Stat: React.FC<{value: number; label: string; color: string}> = ({value, label, color}) => (
  <div
    style={{
      flex: 1,
      padding: '26px 34px',
      borderRadius: 22,
      backgroundColor: C.panel,
      borderLeft: `10px solid ${color}`,
    }}
  >
    <div style={{fontSize: 84, fontWeight: 700, color: C.text, lineHeight: 1}}>{value}</div>
    <div style={{fontSize: 36, color: C.muted, marginTop: 10}}>{label}</div>
  </div>
);

export const Cover: React.FC = () => {
  const c = data.counts;
  return (
    <AbsoluteFill style={{backgroundColor: C.bg, fontFamily: SANS, color: C.text}}>
      <div style={{position: 'absolute', left: 80, top: 70}}>
        <div style={{fontSize: 100, fontWeight: 700, lineHeight: 1.05}}>
          CSV Data Cleaning &amp; Validation Tool
        </div>
        <div style={{fontSize: 44, color: C.muted, marginTop: 18}}>
          Trim · required fields · email format · duplicates · Python, Streamlit, CLI
        </div>
      </div>
      <div
        style={{
          position: 'absolute',
          left: 80,
          top: 320,
          width: SHOT.w,
          height: SHOT.h,
          overflow: 'hidden',
          borderRadius: 24,
          border: `3px solid ${C.line}`,
          backgroundColor: '#ffffff',
          boxShadow: '0 30px 80px rgba(0, 0, 0, 0.45)',
        }}
      >
        <Img
          src={staticFile('screens/04_issues.png')}
          style={{position: 'absolute', left: -SHOT.x, top: -SHOT.y, width: 1920, height: 1080}}
        />
      </div>
      <div style={{position: 'absolute', left: 80, right: 80, top: 1130, display: 'flex', gap: 36}}>
        <Stat value={c.input_rows} label="rows in" color={C.blue} />
        <Stat value={c.clean_rows} label="clean rows" color={C.green} />
        <Stat value={c.issue_rows} label="issues, each with a reason" color={C.amber} />
      </div>
      <div
        style={{
          position: 'absolute',
          right: 80,
          bottom: 60,
          padding: '14px 30px',
          borderRadius: 16,
          border: `3px solid ${C.amber}`,
          color: C.amber,
          fontSize: 40,
          fontWeight: 700,
        }}
      >
        Personal demo · Synthetic data
      </div>
    </AbsoluteFill>
  );
};
