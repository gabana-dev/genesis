import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

/**
 * The research library.
 *
 * `answer` and `finding` are required, not optional. An article without a one-line answer and a
 * finding id is a blog post, and this is an evidence library -- the schema enforces the
 * difference at build time rather than in review.
 */
const research = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/research' }),
  schema: z.object({
    title: z.string(),
    /** The registry id this article publishes: F-0001, CASCADE-1, EXEC-1. */
    finding: z.string(),
    /** One line. If it cannot be stated in one line it is not finished. */
    answer: z.string(),
    /** The standfirst: sample, method and the number that matters. */
    sub: z.string(),
  }),
});

/**
 * The findings registry — every measurement, rendered from the same markdown the repository holds.
 *
 * WHY IT LOADS FROM OUTSIDE web/. `findings/F-*.md` is the source of truth for the whole project:
 * the scorecard, the MCP server and `findings/index.json` are all generated from it. Copying those
 * files in here would create a second copy that drifts, and the first thing to drift would be a
 * status — a REFUTED finding still reading MEASURED on the public site is the exact failure this
 * project exists to make impossible. So the site reads the originals.
 */
const findings = defineCollection({
  loader: glob({ pattern: 'F-*.md', base: '../findings' }),
  schema: z.object({
    id: z.string(),
    title: z.string(),
    status: z.enum(['MEASURED', 'PRELIMINARY', 'ASSUMED', 'REFUTED', 'SUPERSEDED']),
    observation: z.string(),
    sample: z.string(),
    method: z.string(),
    evidence: z.string(),
    /** What would make this wrong, and what is not established. Never optional. */
    confidence: z.string(),
    market_gap: z.string(),
    /* YAML parses a bare 2026-08-22 as a Date, not a string, so these are coerced rather than
       declared as strings. Quoting them in seventeen markdown files would work too and would be
       one quote away from breaking again the next time a finding is written by hand. */
    first_recorded: z.coerce.date(),
    last_updated: z.coerce.date(),
    supersedes: z.string(),
  }),
});

export const collections = { research, findings };
