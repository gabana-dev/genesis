# web/ — the Genesis site

Astro 5 + TypeScript. Builds straight into `../docs/`, which GitHub Pages serves from `main`, so
deploying is a `git push`.

```
npm install          # once
npm run dev          # localhost:4321/genesis
npm run build        # astro check + build  -> ../docs
npm run build:fast   # build only; what the 15-minute refresh runs
```

## The parts worth knowing

**`src/lib/data.ts` is the contract with the Python engine.** `product/generate.py` writes
`public/data/*.json`; every page reads it through the loaders here, and each one asserts the
fields it depends on. A renamed field in the engine now fails the build instead of publishing a
page that renders `undefined%` — that hole is the reason this rewrite happened.

**`build.format: 'preserve'`** in `astro.config.mjs` is not a style preference. It keeps
`src/pages` structure verbatim so every already-published URL — `/check.html`,
`/research/index.html` — survives unchanged. A link someone sent a friend must not break in a
refactor.

**`src/pages/[alertsRoute].astro`** is a dynamic route for one static page. That is deliberate:
`getStaticPaths` returns nothing when no Telegram bot handle exists, so the alerts page is never
emitted and the nav never links it. A storefront advertising a door that does not open is worse
than no door, and this makes that rule structural rather than remembered.

**`src/scripts/check.ts`** is the only JavaScript that reaches a visitor. Hyperliquid's responses
are typed there because they are the one input this site does not control — every numeric field
arrives as a decimal string, which is exactly how the untyped version produced silent `NaN`.

## What is deliberately absent

No UI framework, no CSS framework, no client router. The site is thirteen pages of content and
one interactive island; a component runtime would ship JavaScript to readers who need none.
