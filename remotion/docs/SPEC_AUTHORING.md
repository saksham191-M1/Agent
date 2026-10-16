# Spec Authoring Guide

This document describes how to write a valid `spec.json` for the brand-agnostic ad engine. It is purely based on the rules strictly enforced by `engine/spec.schema.json`.

## The Audio Block
Top-level `audio` object:
- **assetsRoot**: (string) Prefix path.
- **voice**: Contains `provider`, `voiceId`, `model`, and a `clips` dictionary mapping scene IDs to mp3s.
- **music**: Contains `file`, `mood`, and `volume` (0.0 to 1.0).
- **room**: Contains `file` and `volume` (0.0 to 1.0).
- **sfxFiles**: A dictionary mapping cue types (like "click", "swipe") to filenames.
- **duck**: A PERCENT (0 to 12) applied as `music volume x (1 - duck/100)` inside scene windows (engine/audio/Mixer.tsx line 13); it is not tied to voice clips. Jobs use 5 to 7.

## Scene Requirements
Each scene in the `scenes` array must have:
- **id**: A unique string.
- **start**: Start time in seconds.
- **duration**: Duration in seconds (max 5.0).
- **layout**: Must be one of the layouts defined in `library/catalog.json`.
- **headline** / **subline**: Strings. Character limits verified from `engine/spec.schema.json`:
  - `"headline": {"type": "string", "maxLength": 100}`
  - `"subline": {"type": "string", "maxLength": 180}`
- **visual**: Layout-specific graphic properties (derived from real specs):
  - `hero-type`: `kicker`, `pulseText`, or `orbLabel`
  - `phone`: `greeting`, `prompt`
  - `browser`: `title`, `detail`
  - `big-number`: `eyebrow`, `label`
  - `split`: `title`, `detail`
  - `list`: `items` (array with `label`, `icon`, `detail`)
  - `cta`: `button`, `domain`
  - `photo-overlay`: Not used in current jobs
- **motion**: Object containing `enter`, `idle`, and `exit` animation identifiers. Can optionally have `cursorPath`.
- **sfx**: An array of audio cues (e.g. `[{"t": 0.5, "type": "click", "gain": 0.35}]`).
- **transitionOut**: String.
- Optionally: `caption`, `captionWords`, `vo`.

## Example (Source: jobs/skillme-003/spec.json)
```json
{
  "brand": "skillme-003",
  "format": "9:16",
  "fps": 30,
  "durationSec": 20,
  "bpm": 116,
  "scenes": [
    {
      "id": "K1",
      "start": 0,
      "duration": 2,
      "layout": "hero-type",
      "headline": "Build proof, not promises.",
      "subline": "Real projects. Real GitHub work.",
      "visual": {
        "kicker": "SkillMe open-source sprint",
        "pulseText": "Turn learning into evidence."
      },
      "motion": {
        "enter": "type-slam",
        "idle": "pulse-orbit",
        "exit": "push-through"
      },
      "vo": "Build proof of work, not just another tutorial.",
      "sfx": [
        {
          "t": 0.04,
          "type": "logo-sting",
          "gain": 0.35
        }
      ],
      "transitionOut": "cut"
    }
  ],
  "audio": {
    "assetsRoot": "jobs/skillme-003/assets",
    "voice": {
      "provider": "elevenlabs",
      "voiceId": "pNInz6obbfIdGcdOmalT",
      "model": "eleven_multilingual_v2",
      "clips": {
        "K1": "audio/vo-k1.mp3"
      }
    },
    "music": {
      "file": "audio/music-bed.mp3",
      "mood": "focused build with confident lift",
      "volume": 0.17
    },
    "room": {
      "file": "audio/room-tone.wav",
      "volume": 0.15
    },
    "sfxFiles": {
      "logo-sting": "audio/logo-sting.wav"
    },
    "duck": 7
  }
}
```
