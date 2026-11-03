import raw from './demo-data.json';

export const FPS = 30;
export const data = raw;
export type Example = (typeof raw.examples)[number];

export const C = {
  bg: '#0f172a',
  panel: '#1e293b',
  line: '#334155',
  text: '#f8fafc',
  muted: '#94a3b8',
  blue: '#2563eb',
  green: '#22c55e',
  amber: '#f59e0b',
  red: '#f87171',
};

export const SANS = '"Segoe UI", "Microsoft YaHei", Arial, sans-serif';
export const MONO = 'Consolas, "Microsoft YaHei", monospace';

/** Recording path inside the public dir (../demo). */
export const RECORDING = raw.recording.raw_file.replace(/^demo\//, '');

/** Number of passing tests from test-results/run_info.json, or null if it cannot be read. */
export const TESTS_PASSED: number | null = (() => {
  const m = /^(\d+) passed/.exec(raw.tests);
  return m ? Number(m[1]) : null;
})();

export const sec = (s: number) => Math.round(s * FPS);
