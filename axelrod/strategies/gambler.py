"""Stochastic variants of Lookup table based-strategies, trained with particle
swarm algorithms.

For the original see:
 https://gist.github.com/GDKO/60c3d0fd423598f3c4e4
"""
import random
from random import choice
from typing import Any, TypeVar
import numpy as np

from axelrod.action import Action, str_to_actions, actions_to_str
from axelrod.load_data_ import load_pso_tables
from axelrod.evolvable_player import EvolvablePlayer, InsufficientParametersError
from axelrod.player import Player

from axelrod.random_ import random_choice

from .lookerup import EvolvableLookerUp, LookupTable, LookerUp, Plays, create_lookup_table_keys

C, D = Action.C, Action.D
tables = load_pso_tables("pso_gambler.csv", directory="data")


class Gambler(LookerUp):
    """
    A stochastic version of LookerUp which will select randomly an action in
    some cases.

    Names:

    - Gambler: Original name by Georgios Koutsovoulos
    """

    name = "Gambler"
    classifier = {
        "memory_depth": float("inf"),
        "stochastic": True,
        "makes_use_of": set(),
        "long_run_time": False,
        "inspects_source": False,
        "manipulates_source": False,
        "manipulates_state": False,
    }

    def strategy(self, opponent: Player) -> Action:
        actions_or_float = super(Gambler, self).strategy(opponent)
        if isinstance(actions_or_float, Action):
            return actions_or_float
        return random_choice(actions_or_float)


class EvolvableGambler(Gambler, EvolvableLookerUp):
    name = "EvolvableGambler"

    def __init__(
        self,
        lookup_dict: dict = None,
        initial_actions: tuple = None,
        pattern: Any = None,  # pattern is str or tuple of Actions.
        parameters: Plays = None,
        mutation_probability: float = None
    ) -> None:
        EvolvableLookerUp.__init__(
            self,
            lookup_dict=lookup_dict,
            initial_actions=initial_actions,
            pattern=pattern,
            parameters=parameters,
            mutation_probability=mutation_probability
        )
        self.pattern = list(self.pattern)
        Gambler.__init__(
            self,
            lookup_dict=self.lookup_dict,
            initial_actions=self.initial_actions,
            pattern=self.pattern,
            parameters=self.parameters
        )
        self.overwrite_init_kwargs(
            lookup_dict=self.lookup_dict,
            initial_actions=self.initial_actions,
            pattern=self.pattern,
            parameters=self.parameters,
            mutation_probability=self.mutation_probability,
        )

    def receive_vector(self, vector):
        """Receives a vector and updates the player's pattern. Ignores extra parameters."""
        self.pattern = vector
        self_depth, op_depth, op_openings_depth = self.parameters
        self._lookup = LookupTable.from_pattern(self.pattern, self_depth, op_depth, op_openings_depth)

    def create_vector_bounds(self):
        """Creates the bounds for the decision variables. Ignores extra parameters."""
        size = len(self.pattern)
        lb = [0.0] * size
        ub = [1.0] * size
        return lb, ub

    @staticmethod
    def mutate_pattern(pattern, mutation_probability):
        randoms = np.random.random(len(pattern))
        for i, _ in enumerate(pattern):
            if randoms[i] < mutation_probability:
                ep = random.uniform(-1, 1) / 4
                pattern[i] += ep
                if pattern[i] < 0:
                    pattern[i] = 0
                if pattern[i] > 1:
                    pattern[i] = 1
        return pattern

    def mutate(self):
        pattern = self.mutate_pattern(self.pattern, self.mutation_probability)
        plays, op_plays, op_start_plays = self.parameters
        num_actions = max([plays, op_plays, op_start_plays])
        initial_actions = tuple([choice((C, D)) for _ in range(num_actions)])
        return self.__class__(
            pattern=pattern,
            parameters=self.parameters,
            initial_actions=initial_actions,
            mutation_probability=self.mutation_probability,
        )

    def crossover(self, other):
        pattern1 = self.pattern
        pattern2 = other.pattern
        cross_point = int(random.randint(0, len(pattern1)))
        offspring_pattern = pattern1[:cross_point] + pattern2[cross_point:]

        return self.__class__(
            parameters=self.parameters,
            pattern=offspring_pattern,
            initial_actions=self.initial_actions,
            mutation_probability = self.mutation_probability,
        )

    @staticmethod
    def random_params(plays, op_plays, op_start_plays):
        keys = create_lookup_table_keys(plays, op_plays, op_start_plays)
        pattern = [random.random() for _ in keys]
        table = dict(zip(keys, pattern))
        return pattern, LookupTable(table)

    def serialize_parameters(self):
        self_depth, op_depth, op_openings_depth = self.parameters
        return "{}:{}:{}:{}:{}".format(
            self_depth,
            op_depth,
            op_openings_depth,
            '|'.join(str(v) for v in self.pattern),
            actions_to_str(self.initial_actions)
        )

    @classmethod
    def deserialize_parameters(cls, serialized):
        s = serialized.split(':')
        parameters = tuple(map(int, s[0:3]))
        pattern = list(map(float, s[3].split('|')))
        initial_actions = str_to_actions(s[4])
        return cls(parameters=parameters, pattern=pattern, initial_actions=initial_actions)


class PSOGamblerMem1(Gambler):
    """
    A 1x1x0 PSOGambler trained with pyswarm. This is the 'optimal' memory one
    strategy trained against the set of short run time strategies in the
    Axelrod library.

    Names:

    - PSO Gambler Mem1: Original name by Marc Harper
    """

    name = "PSO Gambler Mem1"

    def __init__(self) -> None:
        pattern = tables[("PSO Gambler Mem1", 1, 1, 0)]
        parameters = Plays(self_plays=1, op_plays=1, op_openings=0)

        super().__init__(parameters=parameters, pattern=pattern)


class PSOGambler1_1_1(Gambler):
    """
    A 1x1x1 PSOGambler trained with pyswarm.

    Names:

    - PSO Gambler 1_1_1: Original name by Marc Harper
    """

    name = "PSO Gambler 1_1_1"

    def __init__(self) -> None:
        pattern = tables[("PSO Gambler 1_1_1", 1, 1, 1)]
        parameters = Plays(self_plays=1, op_plays=1, op_openings=1)

        super().__init__(parameters=parameters, pattern=pattern)


class PSOGambler2_2_2(Gambler):
    """
    A 2x2x2 PSOGambler trained with a particle swarm algorithm (implemented in
    pyswarm). Original version by Georgios Koutsovoulos.

    Names:

    - PSO Gambler 2_2_2: Original name by Marc Harper
    """

    name = "PSO Gambler 2_2_2"

    def __init__(self) -> None:
        pattern = tables[("PSO Gambler 2_2_2", 2, 2, 2)]
        parameters = Plays(self_plays=2, op_plays=2, op_openings=2)

        super().__init__(parameters=parameters, pattern=pattern)


class PSOGambler2_2_2_Noise05(Gambler):
    """
    A 2x2x2 PSOGambler trained with pyswarm with noise=0.05.

    Names:

    - PSO Gambler 2_2_2 Noise 05: Original name by Marc Harper
    """

    name = "PSO Gambler 2_2_2 Noise 05"

    def __init__(self) -> None:
        pattern = tables[("PSO Gambler 2_2_2 Noise 05", 2, 2, 2)]
        parameters = Plays(self_plays=2, op_plays=2, op_openings=2)

        super().__init__(parameters=parameters, pattern=pattern)


class ZDMem2(Gambler):
    """
    A memory two generalization of a zero determinant player.

    Names:

    - ZDMem2: Original name by Marc Harper
    - Unnamed [LiS2014]_

    """

    name = "ZD-Mem2"

    classifier = {
        "memory_depth": 2,
        "stochastic": True,
        "makes_use_of": set(),
        "long_run_time": False,
        "inspects_source": False,
        "manipulates_source": False,
        "manipulates_state": False,
    }

    def __init__(self) -> None:
        pattern = [
            11 / 12,
            4 / 11,
            7 / 9,
            1 / 10,
            5 / 6,
            3 / 11,
            7 / 9,
            1 / 10,
            2 / 3,
            1 / 11,
            7 / 9,
            1 / 10,
            3 / 4,
            2 / 11,
            7 / 9,
            1 / 10,
        ]
        parameters = Plays(self_plays=2, op_plays=2, op_openings=0)

        super().__init__(parameters=parameters, pattern=pattern)
