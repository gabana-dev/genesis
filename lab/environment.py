"""
A minimal partially observable environment for Genesis Laboratory 1.

Partial observability is the single condition that -- per the belief-necessity
result (research/journal/2026-08-07-belief-derived-by-necessity.md) -- forces a
belief-state. This environment isolates exactly that condition and nothing else.

  Hidden state : one bit, chosen at episode start, fixed for the episode, never
                 directly revealed.
  Observation  : the hidden bit corrupted by noise -- faithful with probability
                 (1 - noise), flipped with probability noise.
  Reward       : +1 if the agent's final guess matches the hidden bit, else 0.

No single observation determines the hidden state -- that is the partial
observability. Integrating observations over time is the only way to do better
than the per-observation accuracy (1 - noise).

Standard library only. No framework, no generality beyond the experiment.
"""

import random


class PartiallyObservableBit:
    def __init__(self, noise, horizon, rng):
        assert 0.0 <= noise < 0.5, "noise must be < 0.5 for observations to be informative"
        self.noise = noise
        self.horizon = horizon
        self.rng = rng
        self._hidden = None
        self._t = 0

    def reset(self):
        """Begin an episode. Returns the first observation."""
        self._hidden = self.rng.randint(0, 1)
        self._t = 0
        return self._observe()

    def _observe(self):
        if self.rng.random() < self.noise:
            return 1 - self._hidden   # corrupted
        return self._hidden           # faithful

    def step(self):
        """Advance one timestep. Returns the next observation, or None once the
        horizon is reached and it is time to guess."""
        self._t += 1
        if self._t >= self.horizon:
            return None
        return self._observe()

    def reward(self, guess):
        return 1 if guess == self._hidden else 0

    def reveal(self):
        """The true hidden state, available only after the episode -- lets an agent
        learn its own observation model from labelled experience (Laboratory 2)."""
        return self._hidden
