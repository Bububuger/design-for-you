# How this was built

- **Built with:** Claude Opus 5.5 in Claude Code, by exploraX, on 2026-11-09.
- **Inputs:**
  - The code-built Al Capone documentary made earlier in the same session (5:22, Skia engine, Higgsfield voice, ElevenLabs score).
  - The bugs met along the way.
- **Process.**
  - The skill was first written as `cinematic-doc` for history documentaries.
  - Mid-build it was opened up to any subject (`cinematic-film`).
  - It was tested end to end on both shipped projects: the Wright Flyer documentary at 1080p with captions, and the starter explainer.
- **Bugs fixed from rendered stills:** six real bugs. See the "Self-review" list in `skills/cinematic-film/SKILL.md`.

## Original prompts

Quoted as sent:

> hey I posted the video on X and people loved it. what skill do you think we can make to help them create a cinimatic documentary like this?

> okay great create it

> i want a general skill for cinematic films btw

On scope, the user chose: "Any subject (Recommended)". That meant the same code-built single-camera style for any story (product launch, brand story, science explainer, biography, history), with images from archives, your own photos or AI stills, and more looks than the evidence wall.

> can you open-source this skill in a seperate public repo and name it cinmatic skill

## Prompt to recreate this repo

> Build an open-source agent skill, `cinematic-film`, that makes narrated cinematic films entirely from code on any subject. Ship it as a standalone repo, installable with `npx skills add`, plus Claude Code, Codex, Cursor and Gemini manifests and a no-Node shell installer.
>
> **The method.** One continuous camera moves over one designed world: a board of photos, torn clippings, typeset documents, cards, big type, counters, stamps, pen marks, red string, and maps with region fills, routes and markers. Every visual hit is timed to the word the narrator says. Draw it with skia-python. World units are 4K pixels at zoom 1. The camera is a monotone cubic spline with a log-zoom channel and handheld drift, with motion-blur sub-frames on fast moves. Add a radial spotlight that dims everything but the hero, and a film finish: glow, S-curve, vignette, and half-resolution grain that changes every second frame.
>
> **Scripts** (all take `--project`):
> 1. A setup check.
> 2. A project scaffolder.
> 3. A beat table with a chronology lint.
> 4. A free scratch voice (macOS `say`, espeak-ng, or any TTS command).
> 5. A take splitter: ffmpeg silencedetect plus a segment-based dynamic program, letters-per-second flags, and forced-cut overrides.
> 6. A narration builder that writes `audio/timing.json` and allows only a 0.90 to 1.15x tempo fit.
> 7. A Wikimedia Commons fetcher that records licences, refuses non-free files and writes `credits.md`.
> 8. A map builder: TopoJSON or GeoJSON, with Albers, equirectangular and Mercator projections and Sutherland-Hodgman clipping.
> 9. Asset prep: duotone or natural grading, and generated textures.
> 10. A render driver: probes, contact strips, a cue list, and a parallel MP4 with a worker count that fits in memory.
> 11. A sound-effects synthesiser with no samples.
> 12. A sidechain-ducked, two-pass loudness mixer.
> 13. A caption burner with four styles and SRT output.
>
> **Engine details.** The scene API is `build_film(doc)`, with `doc.L(i)`, `doc.E(i)`, `doc.W(i, "spoken word")` and `doc.on(print, fx, fy)`, plus `film.shot()` to key the camera and spotlight together. Items cue their own sound effects, and fast moves get an automatic whoosh. Font roles fall back across platforms. There are seven looks: wall, slate, charcoal, paper, studio, blueprint and night.
>
> **Performance rules to bake in.**
> - Tile textures with drawImageRect; never use repeat shaders under rotation.
> - Give every item bounds for culling.
> - Cache big vectors as images, and draw them live when the camera is close.
> - Cap photo sizes, and cap x264 lookahead at 4K.
>
> **Docs.** A SKILL.md with seven rules, an 11-step workflow with four approval gates, and a self-review checklist. References on story shapes (documentary, launch, brand, explainer, biography), voice, images and rights, film, sound, and performance.
>
> **Projects to ship.** A runnable studio-look starter explainer that needs no photos, and a 90 second public-domain documentary about the Wright Flyer as the worked example.
>
> **Checks.** CI parses the skill and makes a real film on Linux. No em dashes anywhere.
