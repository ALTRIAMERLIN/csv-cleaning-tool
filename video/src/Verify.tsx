import React from 'react';
import {interpolate, useCurrentFrame} from 'remotion';
import {C, data, MONO, SANS} from './theme';

const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
const FILES = ['clean.csv', 'issues.csv', 'changes.csv', 'summary.json'] as const;

const Mark: React.FC<{ok: boolean; children: React.ReactNode}> = ({ok, children}) => (
  <div style={{display: 'flex', gap: 14, color: ok ? C.green : C.red}}>
    <span style={{fontWeight: 700}}>{ok ? '✓' : '✗'}</span>
    <span style={{color: C.text}}>{children}</span>
  </div>
);

/** Card with the real checks from demo/demo_manifest.json. `from` is the local start frame. */
export const Verify: React.FC<{from: number}> = ({from}) => {
  const frame = useCurrentFrame() - from;
  if (frame < 0) return null;
  const card = interpolate(frame, [0, 10], [0, 1], clamp);
  const k = data.checks;
  const sameAsCli = k.downloads_match_cli_output && k.downloads_match_core_output;
  return (
    <div
      style={{
        position: 'absolute',
        left: 150,
        right: 150,
        top: 120,
        padding: '26px 36px',
        borderRadius: 20,
        backgroundColor: 'rgba(15, 23, 42, 0.95)',
        border: `2px solid ${C.line}`,
        opacity: card,
        transform: `translateY(${(1 - card) * -20}px)`,
        fontFamily: SANS,
        color: C.text,
      }}
    >
      <div style={{fontSize: 32, fontWeight: 700, marginBottom: 14}}>
        Downloaded files, checked against a separate command-line run
      </div>
      <div style={{display: 'flex', fontSize: 20, color: C.muted, paddingBottom: 6}}>
        <div style={{width: 230}}>file</div>
        <div style={{width: 130}}>rows</div>
        <div style={{width: 150}}>bytes</div>
        <div style={{width: 520}}>SHA-256 (first 24 characters)</div>
        <div>download vs CLI</div>
      </div>
      {FILES.map((f, i) => {
        const o = data.outputs[f] as {bytes: number; sha256: string; rows?: number};
        const row = interpolate(frame, [6 + i * 4, 12 + i * 4], [0, 1], clamp);
        return (
          <div
            key={f}
            style={{
              display: 'flex',
              alignItems: 'center',
              height: 46,
              opacity: row,
              borderTop: `1px solid ${C.line}`,
              fontFamily: MONO,
              fontSize: 24,
            }}
          >
            <div style={{width: 230}}>{f}</div>
            <div style={{width: 130}}>{o.rows ?? '—'}</div>
            <div style={{width: 150}}>{o.bytes}</div>
            <div style={{width: 520, color: '#cbd5e1'}}>{o.sha256.slice(0, 24)}…</div>
            <div style={{fontFamily: SANS, color: sameAsCli ? C.green : C.red, fontWeight: 600}}>
              {sameAsCli ? '✓ same bytes' : '✗ see manifest'}
            </div>
          </div>
        );
      })}
      <div
        style={{
          marginTop: 14,
          display: 'flex',
          flexDirection: 'column',
          gap: 6,
          fontSize: 24,
          opacity: interpolate(frame, [26, 34], [0, 1], clamp),
        }}
      >
        <Mark ok={k.counts_match_expected && k.reason_counts_match_expected}>
          Counts match the expected results written by the data generator
        </Mark>
        <Mark ok={k.accounting_ok}>
          Each of the {data.counts.input_rows} input rows is in exactly one output file
        </Mark>
      </div>
    </div>
  );
};
