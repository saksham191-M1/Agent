# TASK: Stage 8 — spec-first pipeline, audio check, cleanup (STOP after)

0. Honesty correction. Your last report printed an engine fingerprint of b2b2913e2bb978184f4f7d45ebba8d06
   from scripts/fingerprint-engine.ts. That script does not exist; the real command
   (scripts/engine-fingerprint.ts) prints 07a170f6ccd7802aab44efdae98fc8d8599c22fc61682ca78991beb9c027a756.
   State which command produced the first output, or admit that it was not real. From now on, paste only
   output that a command actually produced. I will re-run the fingerprint, 
pm run verify and
   git status myself after this task; any mismatch means the task failed.

Rules: Windows PowerShell; real command output; scripts in files; git only inside this folder; statuses
from exit codes. Log files must be UTF-8: never use >> or echo >> (UTF-16 in PS 5.1); use
Add-Content -Encoding utf8 or Out-File -Encoding utf8. Paste outputs unedited, including warnings.

1. Plan-vs-spec pipeline (replaces compile-spec):
   a. Remove passthrough from engine/storyboard.schema.json and from the three storyboards
      (storyboards stay as a pure plan). Delete scripts/compile-spec.ts, scripts/deep-compare.ts and the
      compile-spec npm script; keep knip clean.
   b. Add scripts/check-plan-vs-spec.ts (
pm run plan-vs-spec, included in verify). For each job
      compare storyboard.json and spec.json: same shot/scene count and order; t0/t1 vs start/start+duration
      (±0.001); hook first and cta last; headline/subline/onScreenText vs spec headline/subline/caption;
      dialogue vs vo. Exit non-zero on any mismatch; legacy mismatches go in known-exceptions.json with a
      reason. Print every diff with job id and path.
   c. Write docs/SPEC_AUTHORING.md: how to write a valid spec.json from engine/spec.schema.json — required
      fields per scene, the layout names and their content fields (from library/catalog.json), motion
      fields, the audio block (voice, music, room, sfx cue shape, duck) with the value ranges used by the
      three jobs, plus a worked example. Base it on the schema and the three real specs, nothing invented.
   d. If docs/AD_DIRECTOR.md exists, update the pipeline: "write storyboard.json (plan) → write spec.json
      (schema-validated) → plan-vs-spec check → render". Otherwise note that it still needs to be created.
2. Swiggy audio, verify before accepting:
   a. Print the provenance of jobs/swiggy-001/assets/audio/music-bed.mp3 (file metadata, any note in the
      repo, git log for it) and its integrated LUFS; do the same for skillme-003's music bed.
   b. For ALL 9 originally failing windows (3.5, 6, 6.5, 9, 11.5, 12, 12.5, 17.5, 18s) print RMS per 0.1s
      before (git stash is NOT allowed; use the old report values or re-render the old spec to a temp
      folder) and after, in one table. State which cues are active in each (voice, music, room, sfx) using
      the spec/mixer, with no contradictions.
   c. Measure voice vs music in the voice-over windows: report the dB ratio per scene. It must stay >= 6 dB.
      If it doesn't, the volume change is wrong; propose a better fix (for example loudness-normalise the bed
      asset to the level of skillme-003's bed and keep volume near the other jobs' value), apply it only to
      swiggy-001's own assets/spec, re-render, re-master, QA, and paste the new report.
3. Equivalence, non-circular: since specs are now authored directly, replace the compiled-vs-original
   still comparison with a simple regression check: 
pm run stills:job <id> for all three jobs; paste the
   FULL md5 list per job (no truncation) so later stages can detect unintended changes. Save it to
   docs/reports/baselines/stills-<id>.txt.
4. Cleanup: delete scripts/swiggy-rms.ts, scripts/fix-readme.js, scripts/compare-stills.js (or promote one to
   a typed scripts/audio-diagnose.ts <jobId> <start> <end> with no implicit any, in verify's lint/knip
   scope). Convert all docs/reports/logs/*.txt to UTF-8. Print git status --short -- . in full.
5. 
pm run engine:fingerprint swiggy-001 (must still equal 07a170f6ccd7802aab44efdae98fc8d8599c22fc61682ca78991beb9c027a756, or explain
   exactly what changed in engine/), then 
pm run verify full output, then $LASTEXITCODE on its own line.
6. Report built from logs and exit codes. Wait for my go-ahead.
