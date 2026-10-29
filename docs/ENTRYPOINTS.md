# Ad Engine Pipeline Entrypoints

## Primary Supported Entrypoint
The single supported ad generation entrypoint is:
```bash
npx tsx scripts/produce-ad.ts --url <product_url> [--name <product_name>] [--job <job_id>]
```
This orchestrates:
1. `scrape-brand.ts` → real DOM crawl, WCAG 2.1 contrast math, screenshots
2. `brain_opus.py` → Director AI Gateway, narrative arc selection, critique loop
3. `scene-assembler.ts` → vector UI tree AST + spec.json
4. `ingest-template.ts` → dynamic scenes/index.tsx
5. `render-raw.ts` & `master-render.ts` → 1080p 60fps video + EBU R128 audio mastering

## Legacy / Deprecated Scripts
The following scripts are retained only for historical backwards-compatibility:
- `scripts/run-director.ts`: Deprecated demo script with hardcoded branches. Requires `--legacy` flag to execute.
- `audio_layer.py` (root) & `programmatic_pipeline.py`: Legacy programmatic cue table pipeline.
