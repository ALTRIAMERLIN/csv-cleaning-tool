import React from 'react';
import {AbsoluteFill, Easing, interpolate, useCurrentFrame} from 'remotion';
import {Caption} from './parts';
import {C, data, Example, MONO, SANS} from './theme';

const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
const ease = Easing.out(Easing.cubic);
const COLS = [
  {key: '#', w: 70},
  {key: 'customer_id', w: 140},
  {key: 'name', w: 210},
  {key: 'email', w: 370},
  {key: 'city', w: 150},
];
const ROW_H = 74;

/** Columns the run blamed for this row, taken from its real reason string. */
const blamed = (e: Example): string[] => {
  const r = e.reason ?? '';
  if (r.startsWith('duplicate_of:')) return data.rules.dedupe_keys;
  return r
    .split(';')
    .filter((x) => x.startsWith('missing_required:') || x.startsWith('invalid_email:'))
    .map((x) => x.split(':')[1]);
};

/** Shows leading/trailing spaces as amber dots and empty cells as "(empty)". */
const Value: React.FC<{v: string; bad?: boolean; good?: boolean}> = ({v, bad, good}) => {
  if (v.trim() === '') {
    return <span style={{color: C.amber}}>{v === '' ? '(empty)' : '·'.repeat(v.length)}</span>;
  }
  const lead = v.length - v.trimStart().length;
  const trail = v.length - v.trimEnd().length;
  return (
    <span style={{color: bad ? C.red : good ? C.green : C.text}}>
      <span style={{color: C.amber}}>{'·'.repeat(lead)}</span>
      {v.trim()}
      <span style={{color: C.amber}}>{'·'.repeat(trail)}</span>
    </span>
  );
};

const order = [...data.examples].sort((a, b) => a.source_row - b.source_row);
const showAt = (i: number) => 46 + i * 11;

const InputTable: React.FC<{frame: number}> = ({frame}) => (
  <div style={{position: 'absolute', left: 70, top: 215, width: 940}}>
    <div style={{fontFamily: SANS, fontSize: 30, fontWeight: 700, color: C.text, marginBottom: 6}}>
      Input: {data.input.file}
    </div>
    <div style={{display: 'flex', gap: 40, fontFamily: SANS, fontSize: 22, color: C.muted, marginBottom: 18}}>
      <span>
        {order.length} of {data.input.rows} rows
      </span>
      <span>
        <span style={{color: C.amber, fontWeight: 700}}>·</span> marks a space
      </span>
      <span>
        <span style={{color: C.red}}>red</span> = value the run flagged
      </span>
    </div>
    <div style={{display: 'flex', borderBottom: `2px solid ${C.line}`, paddingBottom: 10}}>
      {COLS.map((c) => (
        <div key={c.key} style={{width: c.w, fontFamily: MONO, fontSize: 20, color: C.muted}}>
          {c.key}
        </div>
      ))}
    </div>
    {order.map((e, i) => {
      const appear = interpolate(frame, [10 + i * 5, 18 + i * 5], [0, 1], clamp);
      const lit = interpolate(frame, [showAt(i), showAt(i) + 4, showAt(i) + 16, showAt(i) + 24],
        [0, 1, 1, 0.35], clamp);
      const bad = blamed(e);
      return (
        <div
          key={e.source_row}
          style={{
            display: 'flex',
            alignItems: 'center',
            height: ROW_H,
            opacity: appear,
            borderBottom: `1px solid ${C.line}`,
            backgroundColor: `rgba(37, 99, 235, ${0.18 * lit})`,
            fontFamily: MONO,
            fontSize: 22,
            color: C.text,
          }}
        >
          <div style={{width: COLS[0].w, color: C.muted}}>{e.source_row}</div>
          {e.input ? (
            COLS.slice(1).map((c) => (
              <div key={c.key} style={{width: c.w, whiteSpace: 'pre'}}>
                <Value v={(e.input as Record<string, string>)[c.key]} bad={bad.includes(c.key)} />
              </div>
            ))
          ) : (
            <div style={{width: 870, color: C.red, whiteSpace: 'pre'}}>
              {e.raw_record}
              <span style={{fontFamily: SANS, fontSize: 18, color: C.amber}}>
                {'   '}
                {(e.raw_record ?? '').split(',').length} fields, header has {data.input.columns}
              </span>
            </div>
          )}
        </div>
      );
    })}
  </div>
);

const Box: React.FC<{
  title: string;
  count: number;
  color: string;
  top: number;
  rows: Example[];
  frame: number;
  note?: React.ReactNode;
  render: (e: Example) => React.ReactNode;
}> = ({title, count, color, top, rows, frame, note, render}) => (
  <div
    style={{
      position: 'absolute',
      left: 1110,
      top,
      width: 740,
      padding: '18px 26px 10px',
      borderRadius: 16,
      border: `3px solid ${color}`,
      backgroundColor: C.panel,
    }}
  >
    <div style={{display: 'flex', alignItems: 'baseline', gap: 16, marginBottom: 6}}>
      <div style={{fontFamily: MONO, fontSize: 28, fontWeight: 700, color}}>{title}</div>
      <div style={{fontFamily: SANS, fontSize: 22, color: C.muted}}>{count} rows in this run</div>
      {note ? <div style={{fontFamily: SANS, fontSize: 22, color: C.muted, marginLeft: 'auto'}}>{note}</div> : null}
    </div>
    {rows.map((e) => {
      const i = order.indexOf(e);
      const p = interpolate(frame, [showAt(i), showAt(i) + 12], [0, 1], {...clamp, easing: ease});
      return (
        <div
          key={e.source_row}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 18,
            height: 62,
            opacity: p,
            transform: `translateX(${(1 - p) * -60}px)`,
            fontFamily: MONO,
            fontSize: 22,
            color: C.text,
            whiteSpace: 'pre',
          }}
        >
          <div style={{width: 56, color: C.muted}}>{e.source_row}</div>
          {render(e)}
        </div>
      );
    })}
  </div>
);

export const Intro: React.FC = () => {
  const frame = useCurrentFrame();
  const title = interpolate(frame, [0, 12], [0, 1], clamp);
  const arrow = interpolate(frame, [36, 48], [0, 1], clamp);
  const clean = order.filter((e) => e.dest === 'clean.csv');
  const issues = order.filter((e) => e.dest === 'issues.csv');
  return (
    <AbsoluteFill style={{backgroundColor: C.bg}}>
      <div style={{position: 'absolute', left: 70, top: 64, opacity: title}}>
        <div style={{fontFamily: SANS, fontSize: 60, fontWeight: 700, color: C.text}}>
          CSV Data Cleaning &amp; Validation Tool
        </div>
        <div style={{fontFamily: SANS, fontSize: 26, color: C.muted, marginTop: 4}}>
          Real rows from the synthetic demo file and where this run put them
        </div>
      </div>
      <InputTable frame={frame} />
      <div
        style={{
          position: 'absolute',
          left: 1022,
          top: 470,
          fontFamily: SANS,
          fontSize: 80,
          color: C.blue,
          opacity: arrow,
        }}
      >
        →
      </div>
      <Box
        title="clean.csv"
        count={data.counts.clean_rows}
        color={C.green}
        top={215}
        rows={clean}
        frame={frame}
        note={
          <>
            <span style={{color: C.green}}>green</span> = trimmed
          </>
        }
        render={(e) => {
          const before = e.input as Record<string, string>;
          const after = e.after as Record<string, string>;
          return (
            <>
              <div style={{width: 120}}>{after.customer_id}</div>
              <div style={{width: 210}}>
                <Value v={after.name} good={before.name !== after.name} />
              </div>
              <div style={{width: 310, overflow: 'hidden'}}>
                <Value v={after.email} good={before.email !== after.email} />
              </div>
            </>
          );
        }}
      />
      <Box
        title="issues.csv"
        count={data.counts.issue_rows}
        color={C.amber}
        top={215 + 70 + clean.length * 62 + 60}
        rows={issues}
        frame={frame}
        render={(e) => (
          <>
            <div style={{width: 120}}>
              {e.input ? (e.input as Record<string, string>).customer_id : (e.raw_record ?? '').split(',')[0]}
            </div>
            <div
              style={{
                padding: '4px 14px',
                borderRadius: 10,
                backgroundColor: 'rgba(245, 158, 11, 0.16)',
                color: C.amber,
              }}
            >
              {e.reason}
            </div>
          </>
        )}
      />
      <Caption from={22} to={150}>
        Messy CSV in → clean rows out, and every rejected row kept with its reason
      </Caption>
    </AbsoluteFill>
  );
};
