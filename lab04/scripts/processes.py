from abc import ABC, abstractmethod
from typing import Union
from numpy.random import random, poisson, randn
from typing import List, Callable


class Process(ABC):
    @abstractmethod
    def step(self):
        pass

    @abstractmethod
    def get(self) -> float:
        pass

    def __add__(self, other):
        return


class ConstantProcess(Process):
    def __init__(self, value: Union[float, int]):
        self.value = value

    def step(self):
        pass

    def get(self) -> float:
        return self.value


class BirthDeathProcess(Process):
    """
    A discretized birth and death process.
    The birth and death rates are given by another process, making it possibly non-homogeneous.
    The lower limit of the process is always 0. The upper limit can be specified, 0 means infinity.
    """

    def __init__(self, birth_rate: Process, death_rate: Process, init: int = 0, limit: int = 0):
        self.birth_rate = birth_rate
        self.death_rate = death_rate
        self.value = init
        self.limit = limit

    def step(self):
        # birth/death number in a time window ~ poisson(birth/death_rate)
        _lambda = self.birth_rate.get()
        n_birth = poisson(_lambda)
        _mu = self.death_rate.get()
        n_death = poisson(_mu)
        self.value = self.value+n_birth
        if self.limit > 0:
            self.value = min(self.limit, self.value)
        self.value = max(0, self.value-n_death)

    def get(self) -> float:
        return self.value


class GaussianNoiseProcess(Process):
    def __init__(self, mean: float, std: float):
        self.mean = mean
        self.std = std
        self.value = std*randn()+mean

    def step(self):
        self.value = self.std*randn()+self.mean

    def get(self) -> float:
        return self.value


class PwConstantProcess(Process):
    """
    A piecewise constanct process, determined by the values and lengths of the constant parts.
    The process can be made seasonal, meaning that it will loop back to 0 at the last specified timestep.
    If it is not seasonal, the last value is used until infinity.
    """

    def __init__(self, phase_lengths: List[int], values: List[float], seasonal: bool = False):
        self.phase_lengths = phase_lengths
        self.values = values
        self.seasonal = seasonal
        self.t = 0
        self.phase = 0
        self.value = values[0]

    def step(self):
        self.t += 1
        if self.t > self.phase_lengths[self.phase]:
            self.phase += 1
            self.t = 0

            # TODO: non-seasonal case
            if self.seasonal and self.phase > len(self.values)-1:
                self.phase = 0
                self.t = 0
            self.value = self.values[self.phase]
    pass

    def get(self) -> float:
        return self.value


class IntegratedProcess(Process):
    def __init__(self, base_process: Process, offset: float = 0.0):
        self.value = base_process.get() + offset
        self.base_process = base_process

    def step(self):
        self.value += self.base_process.get()

    def get(self) -> float:
        return self.value


class ReplayedProcess(Process):
    def __init__(self, samples: List[float]):
        self.samples = samples
        self.t = 0

    def step(self):
        self.t += 1
        if self.t > len(self.samples)-1:
            self.t = 0

    def get(self) -> float:
        return self.samples[self.t]


class SumProcess(Process):
    def __init__(self, components: List[Process]):
        self.components = components

    def step(self):
        # the component processes must be stepped themselves;
        # this is in order to avoid stepping them multiple times
        # if they are part of multiple dependent processes
        pass

    def get(self) -> float:
        return sum([c.get() for c in self.components])


class ProductProcess(Process):
    def __init__(self, components: List[Process]):
        self.components = components

    def step(self):
        pass

    def get(self) -> float:
        res = 1.0
        for c in self.components:
            res *= c.get()
        return res


class OnOffProcess(Process):
    def __init__(self, on_to_off_prob: Process, off_to_on_prob: Process):
        """
        :param on_to_off_prob: probability of turning off if it is on; the process should be between 0 and 1
        :param off_to_on_prob: probability of turning on if it is off; the process should be between 0 and 1
        """
        self.on_to_off_prob = on_to_off_prob
        self.off_to_on_prob = off_to_on_prob
        self.value = 0

    def step(self):
        if self.value == 0:
            if random() < self.off_to_on_prob.get():
                self.value = 1
        else:
            if random() < self.on_to_off_prob.get():
                self.value = 0

    def get(self) -> float:
        return self.value


class TransformedProcess(Process):
    def __init__(self, base_process: Process, transformation: Callable[[float], float]):
        self.base_process = base_process
        self.transformation = transformation

    def step(self):
        pass

    def get(self) -> float:
        return self.transformation(self.base_process.get())
