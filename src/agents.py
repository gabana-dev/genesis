"""
Two agents for Laboratory 1, both built ONLY from the earned primitives in
genesis.py and the observations the environment provides.

  MemorylessAgent : keeps no belief. It acts on the most recent observation
                    alone -- Reception without a meaningful Update (each new
                    observation discards the prior state entirely).
  BeliefAgent     : maintains a belief-state via Update on every observation --
                    Reception + Update, exactly as the belief-necessity result
                    prescribes.

The experiment tests the prediction that, under partial observability, the
belief agent's final guess is more accurate than the memoryless agent's.
"""

from genesis import receive, update, initial_belief


class MemorylessAgent:
    def __init__(self):
        self._last = None

    def observe(self, observation):
        self._last = receive(observation)   # no Update; prior state discarded

    def guess(self):
        return self._last                    # act on the latest observation only


class BeliefAgent:
    def __init__(self, noise):
        self._noise = noise
        self._belief = initial_belief()

    def observe(self, observation):
        o = receive(observation)
        self._belief = update(self._belief, o, self._noise)   # Reception + Update

    def guess(self):
        # Read the belief-state to act: the maximum a posteriori hidden state.
        return 0 if self._belief[0] >= self._belief[1] else 1
