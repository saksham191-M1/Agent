# Engine lessons

- Keep brand facts in `brand.json` and scene copy in `spec.json`; job scene modules should only compose engine primitives.
- Stage job assets into the Remotion public directory before bundling so static asset URLs remain deterministic.
- Pass the job id through Remotion input props rather than relying on process environment values inside a bundled composition.
- Use a portable FFmpeg/FFprobe pair for loudness, silence, and container checks instead of assuming host binaries.
- Fingerprint `/engine` before and after fixture renders to catch accidental job-specific edits.
