import {Config} from '@remotion/cli/config';

// The recording and screenshots are served straight from ../demo (the real recorded run),
// so the video never uses a copy that could drift from demo/demo_manifest.json.
Config.setPublicDir('../demo');
Config.setVideoImageFormat('jpeg');
Config.setJpegQuality(95);
Config.setOverwriteOutput(true);
