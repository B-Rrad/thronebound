# Media and Deployment

Return to [[Home]].

## Page Guide

- Multimedia assets
- Build and release artifacts
- Deployment paths
- Monetization and publishing discussion

## Multimedia

The digital report assignment calls for multimedia, and the current project has multiple pieces ready to reference:

- Playable browser build: [https://drpeterjamieson.com/PROJECTS/THRONEBOUND/index.html](https://drpeterjamieson.com/PROJECTS/THRONEBOUND/index.html)
- Gameplay video: [https://youtu.be/ONRpg0IdMZ4](https://youtu.be/ONRpg0IdMZ4)
- Background art used in the build: [`background.jpg`](https://github.com/B-Rrad/thronebound/blob/main/background.jpg)
- Generated card art assets: [`output/card_placeholders/`](https://github.com/B-Rrad/thronebound/tree/main/output/card_placeholders)
- Music tracks used by the desktop build: [`music/`](https://github.com/B-Rrad/thronebound/tree/main/music)

### Sample Visuals

![Odysseus card](https://raw.githubusercontent.com/B-Rrad/thronebound/main/output/card_placeholders/heroes/odysseus.png)
![Ares card](https://raw.githubusercontent.com/B-Rrad/thronebound/main/output/card_placeholders/heroes/ares.png)
![Verdant Court card](https://raw.githubusercontent.com/B-Rrad/thronebound/main/output/card_placeholders/realm/verdant_court_ace.png)
![Ember Throne card](https://raw.githubusercontent.com/B-Rrad/thronebound/main/output/card_placeholders/realm/ember_throne_ace.png)

The report attributes the refreshed visual and music generation to Google Gemini in the current iteration. [R1](References#r1) [R2](References#r2)

## Build and Release Artifacts

The repository already includes several submission-ready artifacts:

- Repository source: [GitHub repository](https://github.com/B-Rrad/thronebound)
- Previous Windows executable: [`release/Ringbound.exe`](https://github.com/B-Rrad/thronebound/blob/main/release/Ringbound.exe)
- Browser build archive: [`dist-web.zip`](https://github.com/B-Rrad/thronebound/blob/main/dist-web.zip)
- Browser rewrite source: [`web/`](https://github.com/B-Rrad/thronebound/tree/main/web)
- Browser rewrite notes: [`WEB_REWRITE.md`](https://github.com/B-Rrad/thronebound/blob/main/WEB_REWRITE.md)

These artifacts matter because they show the report is describing a real deliverable set rather than a hypothetical future product. [R1](References#r1)

## Deployment Paths

The most practical deployment options, in order of readiness, are:

1. A desktop prototype distributed from GitHub using the current source and executable.
2. A browser-hosted release using the existing Vite/canvas rewrite and packaged web build.
3. A later mobile-friendly version if the browser implementation receives more layout and touch-input work.

The browser version is strategically important because it reduces install friction and aligns well with classroom showcase or lightweight publishing use cases. [R1](References#r1) [R4](References#r4)

## Monetization and Publication Potential

The current report takes a realistic position on monetization: the game is not ready for large-scale commercial release, but it does have credible next-step paths. The strongest arguments are:

- The base game is compact, teachable, and suitable for short play sessions.
- AI support makes a solo release meaningful even before online multiplayer exists.
- The architecture separates content from logic well enough to support future dominions, hero packs, visual updates, or challenge modes.

Reasonable early publication models include a free prototype, a low-cost desktop release, or a browser version supported by ads. The key point is not immediate commercialization at scale. It is that the project is structured well enough to justify further polish. [R1](References#r1)

## Where to Go Next

- For the high-level project framing, return to [[Home]].
- For sources and citations, continue to [[References]].
