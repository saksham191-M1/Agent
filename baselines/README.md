# Pipeline Verification Baseline Snapshot (Commit 287057d)

Recorded on: 2026-10-30

## 1. Baseline Jobs Captured
Snapshots of `spec.json`, `brand.json`, `storyboard.json`, and `ui_tree.json` have been archived under `baselines/`:
- `baselines/zomato-001/`
- `baselines/zerodha-001/`
- `baselines/swiggy-001/`

## 2. Test & Verification Script Results

| Script | Command | Result | Notes |
| :--- | :--- | :--- | :--- |
| **Typecheck** | `npm run typecheck` | ✅ **PASS** | 0 TypeScript errors |
| **Lint** | `npm run lint -- engine jobs job-entry.tsx project-entry.tsx scripts remotion.config.ts` | ✅ **PASS** | 0 warnings, 0 errors |
| **Brand Leak** | `npm run brand-leak` | ✅ **PASS** | 61 engine files scanned cleanly |
| **Spec Schema** | `npm run spec-schema` | ✅ **PASS** | All 26 jobs valid against Zod schema |
| **Storyboard Schema** | `npm run storyboard-schema` | ✅ **PASS** | Semantic rules passed across all 26 jobs |
