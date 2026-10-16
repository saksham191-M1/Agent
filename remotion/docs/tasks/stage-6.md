# TASK: Stage 6 — prove the engine is brand-agnostic, close the open items (STOP after)

Environment: Windows PowerShell, project root remotion-swiggy. Rules: paste real command output;
never type result values; scripts go in files (no `node -e` with nested quotes); git only inside this
folder (no checkout/reset/clean/stash outside it); do not edit existing job specs; do not touch
../tools or ../studio. Report statuses come from exit codes, never typed.

1. Baseline: `npm run engine:fingerprint` (save output). 
2. Render skillme-003 end to end (raw -> master -> QA) with an explicit job id. Paste the QA report.
3. Render swiggy-001 again end to end. Paste the QA report.
4. `npm run engine:fingerprint` again: the hashes must be identical to step 1 (zero engine diffs).
   Paste both outputs.
5. Deep round trip: for each job, compile storyboard+brand to jobs/<id>/out/spec.compiled.json and
   deep-compare with spec.json for ALL scenes and the audio block. Ignore only fields carried by
   `passthrough`. Print path-level diffs and list which fields only passthrough carries.
6. Replace `catch { /* ignore */ }` in scripts/compile-spec.ts with real handling (warn with the
   error, or fail). Justify in one line.
7. Set engines.node to the Node versions you actually tested. Test the current one and, if you can
   install it with nvm-windows or fnm, Node 22 (otherwise state that only one version was tested).
8. `npm run verify`, then print `$LASTEXITCODE` on the next line. Paste unedited output.
9. Add a README section "Running a job on Windows" with the exact commands and where outputs land.

Report: docs/reports/stage6.md assembled from logs with exit codes and timestamps. Wait for my go-ahead.
