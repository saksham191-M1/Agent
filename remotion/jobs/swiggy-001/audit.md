# Migration audit

Audit scope: the original `src/`, scripts, package configuration, public assets, and renders.
All original application source files were read before migration. Brand-specific data now lives
in this job; engine defaults contain only neutral fallback tokens.

| Original location | Brand-specific items | Destination |
| --- | --- | --- |
| `src/config.ts` | Swiggy; swiggy.com; “One app for everyday convenience.”; “Get the Swiggy app”; Food delivery, Instamart, Dineout; feature copy; seven scene headlines/sublines/VO; 3B+ orders, 238K+ restaurant partners, 718+ cities; 108 BPM; timings; voice/model IDs; 23 SFX cues | `brand.json`, `spec.json` |
| `src/theme.ts` | Inter (400–800); orange `#fc8019`, light orange `#ffad65`; navy `#0a1118`/`#111c25`; text `#f7f8fa`; muted `#9eacb8`; unused green `#8ee6ba` | `brand.json` (unused green removed) |
| `src/components/BrandLockup.tsx` | Text-only Swiggy lockup | Official downloaded logo in `assets/`; provenance in `brand.json` |
| `src/components/PhoneMockup.tsx` | Swiggy header; Good evening; What are we doing today?; Search for food or essentials; Food, Instamart, Dineout, Scenes; F/I/D/S badges | `spec.json`; semantic illustrations replace letter badges |
| `src/components/BrowserMockup.tsx` | Swiggy header; Bengaluru; craving/essentials/dining prompts; Momo House, Pizza Lane, Biryani Bowl; The Terrace, Table Stories, Basil & Co.; invented 4.7/4.8/4.6 ratings and 20–40-minute estimates; Fresh fruit, Daily essentials, Quick snacks; Home/Orders/Offers/Account/Search/View/Explore UI copy | Job data; unverifiable merchants, ratings and delivery estimates removed |
| `src/components/BrowserMockup.tsx` (palette) | `#ffbd80`, `#f4a27b`, `#fff0d7`, `#fff7ef`, `#fff`, `#e9edf0`, `#edf0f2`, `#17232d`, `#1a2530`, `#687583`, `#65727e`, `#72808c`, `#9da8b1`, `#75818a`, `#56636e`, `#f1e6dc` | Derived token surfaces; no literal colors in engine components |
| Phone/cursor/button/frame palettes | `#17232d`, `#182530`, `#77828c`, `#87929c`, `#f4f6f7`, `#99a3aa`, `#fff1e6`, `#f6f7f8`, `#edf0f1`, `#859099`, `#52616e`, `#143447`, `#fff`, `#0a1118` | `brand.json` or neutral tokens defaults |
| `src/scenes/S1.tsx`–`S7.tsx` | All duplicated headlines/sublines; service labels; Swiggy network; Everyday convenience, at scale; growing-network sentence; CTA and URL | `spec.json`; job-only creative modules |
| `src/captions.ts`, `src/generatedCaptions.ts` | Old fallback scripts, final VO text, ElevenLabs per-word timestamps | Job `spec.json`; no estimated fallback timestamps in engine |
| `src/audio/*` | Seven named Swiggy VO files; hardcoded scene windows and 20s envelope | Spec-configured mixer and assets |
| `src/Root.tsx`, scripts/package | SwiggyLaunch composition, ordered S1–S7 imports, named output files | Generic `Ad` composition, job registry, CLI job parameter |
| `public/audio/` | Seven human TTS clips, generated music, room tone, eleven SFX files | `assets/audio/` |
| `out/` | Previously delivered Swiggy MP4/raw/stills | Job `out/`; retained migration renders are explicitly labeled |

## Original copy inventory

- Headlines: One app. More everyday.; The next meal, sorted.; Essentials, right when needed;
  Make going out easier; Your day, in one flow; A network built at scale; Make the next plan.
- Sublines: Food, essentials, dining, plans.; Choose a dish and keep moving.; Instamart for
  quick everyday top-ups.; Find Dineout spots worth your time.; Food, essentials,
  plans—without the context switch.; 3B+ orders · 238K+ restaurants · 718+ cities;
  Get the Swiggy app.
- VO: One app keeps everyday plans moving.; Find a meal. Keep moving.; Instamart brings
  essentials when you need them.; Dineout helps you find your next place.; Food, essentials.
  One place.; Three billion. One network.; Open Swiggy. Plan easier.
- Additional UI: Good food and good plans, moving with you.; What are you craving?;
  Need it now?; Where do you want to go?; Reserve your table; Essentials · quick delivery;
  Move through your day; Three ways to make today easier; A growing network behind the
  next plan.; Everyday convenience, at scale.

Inter was a design choice in the original project, not verified as the corporate brand font.
The migration retains it as an explicit job override. No API key is stored in either JSON.
