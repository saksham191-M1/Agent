# Local render fonts

These variable fonts are vendored from the Google Fonts repository. Rendering loads them from
the local Remotion public directory; it does not contact a font CDN.

- `NotoSans.ttf`: `ofl/notosans/NotoSans[wdth,wght].ttf`
- `NotoSansDevanagari.ttf`: `ofl/notosansdevanagari/NotoSansDevanagari[wdth,wght].ttf`
- `Inter.ttf`: `ofl/inter/Inter[opsz,wght].ttf`
- `DMSans.ttf`: `ofl/dmsans/DMSans[opsz,wght].ttf`
- `Outfit.ttf`: `ofl/outfit/Outfit[wght].ttf`
- `SpaceGrotesk.ttf`: `ofl/spacegrotesk/SpaceGrotesk[wght].ttf`

Source: https://github.com/google/fonts. Each family is licensed under the SIL Open Font
License, included as `<family>-OFL.txt`. The generic composition uses Noto Sans with Noto
Sans Devanagari fallback for Hindi. The three curated fixtures retain their configured fonts.
