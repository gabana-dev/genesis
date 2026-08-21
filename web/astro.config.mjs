// @ts-check
import { rm } from 'node:fs/promises';
import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';

/**
 * The content layer emits its schema cache and two module maps into the output directory. For a
 * fully static build nothing references them, and here the output directory IS the published
 * site -- so they would be build internals served on a public URL.
 * @type {import('astro').AstroIntegration}
 */
const tidy = {
  name: 'genesis:tidy',
  hooks: {
    'astro:build:done': async ({ dir }) => {
      for (const junk of ['collections', 'content-assets.mjs', 'content-modules.mjs']) {
        await rm(new URL(junk, dir), { recursive: true, force: true });
      }
    },
  },
};

// GitHub Pages serves /docs from main, so the build writes there directly and the deploy is a
// git push.
export default defineConfig({
  site: 'https://gabana-dev.github.io',
  base: '/genesis',
  outDir: '../docs',
  // `preserve` keeps src/pages structure verbatim: research/index.astro stays
  // research/index.html rather than collapsing to research.html. The published URLs are already
  // shared, so the rewrite must not move any of them.
  build: { format: 'preserve', assets: '_assets' },
  trailingSlash: 'never',
  integrations: [sitemap({ filter: (p) => !p.includes('/_') }), tidy],
  devToolbar: { enabled: false },
});
