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

export const collections = { research };
