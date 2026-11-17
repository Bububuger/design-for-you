# Changelog

## 1.0.1 (2026-11-09)

- `get_fonts.py` fetches open-licensed fonts (Bebas Neue, Homemade Apple) for text roles that Linux and Windows cannot match, so labels, stamps and handwriting keep their look. `check_setup.py` points to it.

## 1.0.0 (2026-11-09)

First release: `cinematic-film`, narrated cinematic films drawn entirely in code, on any subject.

- **Engine.** One continuous camera with motion blur and handheld drift, a spotlight, shakes and auto sound cues.
  - Items: prints and torn clippings, typeset documents, cards, big type, counters, stamps, pen marks, string, maps with region fills, routes and markers.
  - Seven looks.
- **Voice.** Scratch voice for timing, any-TTS take splitting with flagged cuts, and a narration track with a timing file.
- **Story.** Beat table with a chronology lint.
- **Images.** Wikimedia Commons fetcher that records licences and refuses non-free files; a map builder for any country; one-look grading.
- **Sound and finish.**
  - Synthesised sound effects.
  - A ducked, loudness-normalised mix.
  - A memory-aware parallel render.
  - Four caption styles and SRT.
- **Projects.** "Twelve Seconds", a 90 second documentary from seven public-domain photos, and a starter explainer.
