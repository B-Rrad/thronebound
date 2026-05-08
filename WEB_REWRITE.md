# Ringbound Web Rewrite

This directory contains the first TypeScript/canvas rewrite of Ringbound. The Python pygame version remains the source of truth while the browser version catches up.

## Current Scope

- Local two-player play
- Drafting from shared realm and hero pools
- Canvas-rendered cards, table, hand, actions, wounds, and game log
- Refaced Greek hero and dominion data loaded from the Python game JSON files
- Generated card placeholder artwork bundled from `output/card_placeholders/`
- Core combat rules
- Hero effects ported from the pygame implementation
- Ares timing fix included: the extra wound only applies if the Ares attack card survives to a fully defended round end

## Run Locally

Install Node.js 20+ first. Then run:

```bash
npm install
npm run web:dev
```

Open the Vite URL, usually:

```text
http://localhost:5173/web/
```

## Build

```bash
npm run web:build
```

The static output is written to `dist-web/`.

## Next Migration Steps

1. Split `web/src/ringbound.ts` into smaller modules once behavior stabilizes.
2. Add TypeScript tests for the rules engine.
3. Add browser/mobile layout passes.
4. Decide whether to port AI or keep the first web release strictly two-player.
5. Add GitHub Pages deployment from `dist-web/`.
