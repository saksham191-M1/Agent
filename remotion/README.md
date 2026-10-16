# Brand-agnostic ad engine

The reusable renderer is under `engine/`. A job owns its brand evidence, spec, scenes, assets,
and outputs under `jobs/{id}/`.

## Commands

```bash
npm run verify
npm run runtime:check
npm run jobs:generate
npm run render
npm run render:job -- test-brand-002
npm run render:project -- /absolute/path/to/remotion-project.json /absolute/path/to/video.mp4
npm run stills
npm run qa
```

Install dependencies on the OS that will run the renderer (`npm ci`), then install a browser
with `npx remotion browser ensure`. **Note:** never share `node_modules` between Windows and WSL/Linux. Always run `rm -rf node_modules && npm ci` when switching OS. `npm run runtime:check` probes native esbuild, FFmpeg/ffprobe,
and a real browser launch; it prints structured JSON and exits nonzero with the failed stage
and a repair instruction if setup is incomplete. Windows and Linux/WSL require separate
`node_modules` installations.

On minimal Linux hosts, install Chromium's system dependencies. An explicit browser executable
and extracted runtime libraries can also be configured:

```bash
REMOTION_BROWSER_EXECUTABLE="/path/to/chrome-headless-shell" \
LD_LIBRARY_PATH="/path/to/extracted/libs" \
npm run render
```

When Jarvis invokes the renderer, set `REMOTION_LD_LIBRARY_PATH` to the same
directory in `.env`; the backend forwards it to the Remotion child process.

The job id is passed as Remotion input props. `scripts/stage-assets.ts` mirrors the selected job's
assets into the public staging directory before bundling; the canonical files remain under the job.

Jarvis projects use the `ProjectAd` composition. The Studio writes a temporary manifest from its
validated `project.json`, stages the approved local assets, and invokes `scripts/render-project.ts`.
Users do not select Remotion; `STUDIO_RENDERER=auto` prefers it when the Node project and browser
runtime pass their checks. `STUDIO_RENDERER=remotion` requires it, while `STUDIO_RENDERER=python`
forces the legacy renderer for troubleshooting.

## Job contract

- `brand.json`: audited identity, colors, fonts, logo provenance, imagery, and sourced claims.
- `spec.json`: schema-validated timing, copy, layouts, motion labels, captions, and audio paths.
- `scenes/`: job-specific creative composition using only engine primitives.
- `assets/`: canonical media for the job.
- `out/`: stills, raw/final MP4, QA report, and engine fingerprint.

Adding a brand requires only a new `jobs/{id}/` fixture with `brand.json`, `spec.json`,
`scenes/index.tsx`, and `assets/`. Run `npm run jobs:generate`; the registry is generated from
the job folders and the engine remains unchanged. The generated registry is job metadata, not
engine code, and should not be hand-edited.

- catalog.json is the layout catalog.

## Running a job on Windows

To render and master a job end-to-end on Windows:

1. **Render Raw Video**:
   ```powershell
   npm run render:job <jobId>
   ```
   *Output lands in*: `jobs/<jobId>/out/raw.mp4`

2. **Master the Video**:
   ```powershell
   npm run master:job <jobId>
   ```
   *Output lands in*: `jobs/<jobId>/out/final.mp4`

3. **Run QA**:
   ```powershell
   npm run qa:job <jobId>
   ```
   *Output lands in*: `jobs/<jobId>/out/qa-report.json`
