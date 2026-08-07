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


class LearningBeliefAgent:
    """
    Laboratory 2. Like BeliefAgent, but NOT given the observation model -- it must
    LEARN the noise from experience. This tests the hypothesis in
    research/questions/observation-model-provenance.md that the observation model is
    itself the state of a *second* Update loop.

    Two nested loops:
      within episode  -- Update a belief over the hidden bit, using the CURRENT noise
                         estimate;
      across episodes -- after the true state is revealed, Update a tally of faithful
                         vs corrupted observations; its ratio is the noise estimate.

    Persists across episodes (the model accumulates). Laplace pseudocounts start the
    noise estimate at 0.5 (uninformative), so early episodes act near-randomly and
    accuracy climbs as the model converges.
    """

    def __init__(self):
        self._faithful = 1.0    # pseudocount
        self._corrupted = 1.0   # pseudocount -> initial noise estimate 0.5
        self._belief = initial_belief()
        self._episode_obs = []

    def noise_estimate(self):
        return self._corrupted / (self._faithful + self._corrupted)

    def observe(self, observation):
        o = receive(observation)
        self._episode_obs.append(o)
        self._belief = update(self._belief, o, self.noise_estimate())

    def guess(self):
        return 0 if self._belief[0] >= self._belief[1] else 1

    def learn(self, true_state):
        # second Update loop: revealed truth turns each observation into a labelled
        # sample of the sensor, tallied into the noise model.
        for o in self._episode_obs:
            if o == true_state:
                self._faithful += 1
            else:
                self._corrupted += 1
        # reset within-episode state for the next episode
        self._belief = initial_belief()
        self._episode_obs = []
