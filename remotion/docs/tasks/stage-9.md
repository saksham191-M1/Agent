# TASK: Stage 9 — stills fix, docs accuracy, QA report cleanup, audio proposal (STOP after)

Rules: Windows PowerShell; git only inside this folder; do not edit engine/ or existing job specs;
do not rewrite docs/tasks/*.md. Every number you report comes from a command whose output is saved
to a UTF-8 file under docs/reports/logs/ (Out-File -Encoding utf8; never >> or echo >>). The final
report is assembled from those files by a script. If a claim has no command behind it, say so.

1. Stills regression
   a. Show git diff ad897d8 -- scripts/render-stills.ts. Restore three points per scene exactly as in the
      checkpoint: start, middle, end (end = scene.start + scene.duration - 1/fps). Output names are
      <sceneid>-start.png, -middle.png, -end.png, with no "original"/"compiled" prefix. Keep the --spec option
      only if something uses it (check with knip); otherwise remove it.
   b. Delete every *-original.png and *-compiled.png under jobs/*/out/stills.
   c. In qa-report.ts add a staleness check: the visual gate fails if any still is older than spec.json or
      raw.mp4. Prove it by touching spec.json and showing the gate fail, then re-render.
   d. Re-render stills for all three jobs. Print (Get-ChildItem jobs\<id>\out\stills).Count (expect 21)
      and the timestamps. Save full MD5 lists to docs/reports/baselines/stills-<id>.txt, re-run once, and
      show the hashes are identical on both runs.
   e. Look at s1-start, s4-middle and s7-end of swiggy-001 and describe what each frame shows.
2. docs/SPEC_AUTHORING.md
   - duck is a PERCENT applied as music volume x (1 - duck/100) inside scene windows
     (engine/audio/Mixer.tsx line 13); it is not tied to voice clips. Fix every statement that says otherwise.
   - Remove the claim that volumes depend on asset loudness.
   - Add the layout-specific isual fields for every layout, copied from real specs and library/catalog.json
     (name the source file per layout).
   - Replace invented copy and placeholder ids ("abc") with values from a real spec (name the source).
   - Verify the headline/subline character limits against engine/spec.schema.json and print the lines.
3. QA report: rename duckDb to duckPercent; add a check that the room tone and the mix have no click at
   0s and at the last frame (report the sample values at both ends).
4. Audio proposal (DO NOT apply anything)
   a. For each gap window of swiggy-001 (3.5, 6, 6.5, 9, 11.5, 12, 12.5, 17.5, 18s) measure the dBFS of
      music-only, room-only and sfx-only contributions, and the voice-to-music ratio in voice windows,
      from separate renders in a temp folder outside jobs/.
   b. Propose a per-job normalised bed (about -22 LUFS) with volumes near skillme-003's, and show a measured
      table. State plainly what new jobs with <= 2.5 words/sec pacing need for gap audio.
   c. Sketch a voice-aware ducking change in dB (spec fields, attack/release, how legacy duck keeps working,
      the checks that would prove it). Mark it as an engine change that alters the fingerprint and needs my approval.
5. 
pm run verify full output to a file, then $LASTEXITCODE on its own line; git status --short -- .
   in full; 
pm run engine:fingerprint swiggy-001 (it must still be
   ae5497bdc10374c5a1830d99057b17ebd02370e6ee7f312decaa29c7527f4c8f; if not, show the diff in engine/).
6. Report built from logs and exit codes. Wait for my go-ahead.
