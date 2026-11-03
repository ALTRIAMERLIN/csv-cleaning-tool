import React from 'react';
import {
  AbsoluteFill,
  Easing,
  interpolate,
  OffthreadVideo,
  staticFile,
  useCurrentFrame,
} from 'remotion';
import {C, RECORDING, SANS, sec} from './theme';

const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
const ease = Easing.inOut(Easing.cubic);

export type Rect = {x: number; y: number; w: number; h: number};

/** Scale + offset that puts a source rectangle in the middle of the frame, never past an edge. */
const view = (r: Rect, maxScale: number) => {
  const s = Math.min(1920 / r.w, 1080 / r.h, maxScale);
  const tx = Math.min(0, Math.max(1920 - 1920 * s, 960 - s * (r.x + r.w / 2)));
  const ty = Math.min(0, Math.max(1080 - 1080 * s, 540 - s * (r.y + r.h / 2)));
  return {s, tx, ty};
};

export type Zoom = {at: number; rect: Rect; max?: number};

/** A piece of the real recording, starting at `startSec` of the raw file, played at 1x. */
export const Clip: React.FC<{startSec: number; zoom?: Zoom}> = ({startSec, zoom}) => {
  const frame = useCurrentFrame();
  let s = 1;
  let tx = 0;
  let ty = 0;
  if (zoom) {
    const v = view(zoom.rect, zoom.max ?? 1.5);
    const p = interpolate(frame, [zoom.at, zoom.at + 20], [0, 1], {...clamp, easing: ease});
    s = 1 + (v.s - 1) * p;
    tx = v.tx * p;
    ty = v.ty * p;
  }
  return (
    <AbsoluteFill style={{backgroundColor: '#ffffff', overflow: 'hidden'}}>
      <div
        style={{
          position: 'absolute',
          left: 0,
          top: 0,
          width: 1920,
          height: 1080,
          transformOrigin: '0 0',
          transform: `translate(${tx}px, ${ty}px) scale(${s})`,
        }}
      >
        <OffthreadVideo
          src={staticFile(RECORDING)}
          trimBefore={sec(startSec)}
          muted
          style={{width: 1920, height: 1080}}
        />
      </div>
    </AbsoluteFill>
  );
};

/** Fade a whole segment in and out so cuts between real clips read as cuts. */
export const Fade: React.FC<{duration: number; children: React.ReactNode; edge?: number}> = ({
  duration,
  children,
  edge = 8,
}) => {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [0, edge, duration - edge, duration], [0, 1, 1, 0], clamp);
  return <AbsoluteFill style={{opacity}}>{children}</AbsoluteFill>;
};

/** Bottom caption. Times are frames local to the enclosing Sequence. */
export const Caption: React.FC<{from: number; to: number; step?: string; children: React.ReactNode}> = ({
  from,
  to,
  step,
  children,
}) => {
  const frame = useCurrentFrame();
  if (frame < from || frame > to) return null;
  const opacity = interpolate(frame, [from, from + 6, to - 6, to], [0, 1, 1, 0], clamp);
  const lift = interpolate(frame, [from, from + 8], [14, 0], {...clamp, easing: ease});
  return (
    <div
      style={{
        position: 'absolute',
        left: 0,
        right: 0,
        bottom: 56,
        display: 'flex',
        justifyContent: 'center',
        opacity,
        transform: `translateY(${lift}px)`,
      }}
    >
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 22,
          maxWidth: 1600,
          padding: '20px 34px',
          borderRadius: 18,
          backgroundColor: 'rgba(15, 23, 42, 0.92)',
          color: C.text,
          fontFamily: SANS,
          fontSize: 40,
          fontWeight: 600,
          lineHeight: 1.25,
          boxShadow: '0 12px 40px rgba(15, 23, 42, 0.35)',
        }}
      >
        {step ? (
          <div
            style={{
              flex: 'none',
              width: 54,
              height: 54,
              borderRadius: 27,
              backgroundColor: C.blue,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: 30,
              fontWeight: 700,
            }}
          >
            {step}
          </div>
        ) : null}
        <div>{children}</div>
      </div>
    </div>
  );
};

/** Top-right label shown on every piece of real recording. */
export const RecordingBadge: React.FC = () => (
  <div
    style={{
      position: 'absolute',
      top: 28,
      right: 34,
      padding: '10px 18px',
      borderRadius: 12,
      backgroundColor: 'rgba(15, 23, 42, 0.86)',
      color: C.text,
      fontFamily: SANS,
      fontSize: 22,
      lineHeight: 1.35,
      textAlign: 'right',
    }}
  >
    <div style={{fontWeight: 700}}>Real screen recording · normal speed</div>
    <div style={{color: '#cbd5e1'}}>Personal demo · Synthetic data</div>
  </div>
);
