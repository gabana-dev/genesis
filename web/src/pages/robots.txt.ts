import type { APIRoute } from 'astro';
import { SITE } from '../lib/data';

/**
 * robots.txt as a route, not a static file, so the sitemap and llms.txt lines follow the site
 * URL from astro.config.mjs. A static copy would keep pointing at the old host after a domain
 * move, which is the one file where a stale URL silently costs indexing.
 */
export const GET: APIRoute = () =>
  new Response(
    `# Isobath. Research and data are meant to be read, by people and by machines.
User-agent: *
Allow: /

# Named explicitly: a robots file that silently blocks AI crawlers is how a body of
# work becomes invisible.
User-agent: GPTBot
Allow: /
User-agent: ClaudeBot
Allow: /
User-agent: Google-Extended
Allow: /
User-agent: PerplexityBot
Allow: /

Sitemap: ${SITE}/sitemap-index.xml
# Plain-language summary for retrieval systems, generated from the same data:
# ${SITE}/llms.txt
`,
    { headers: { 'Content-Type': 'text/plain; charset=utf-8' } },
  );
