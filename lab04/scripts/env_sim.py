from typing import Callable, Iterable, List, Set, Dict
from influxdb_client import InfluxDBClient, Point
from numpy.random import random
from time import sleep
from datetime import datetime, timedelta

from processes import *


class Measurement:
    def __init__(self, process: Process, distortion: Callable[[float], float]):
        self.process = process
        self.distortion = distortion

    def get(self):
        return self.distortion(self.process.get())


class Device(ABC):
    @abstractmethod
    def step(self):
        pass

    @abstractmethod
    def get(self) -> float:
        pass

    @abstractmethod
    def get_influx_meas(self):
        pass

    @abstractmethod
    def get_tags(self):
        pass


class BasicDevice(Device):
    def __init__(self, name: str, measurement: Measurement, p_skip: float,
                 influx_meas: str, influx_tags: Dict[str, str]):
        self.name = name
        self.measurement = measurement
        self.p_skip = p_skip
        self.value = measurement.get()
        self.tags = influx_tags
        self.influx_meas = influx_meas

    def step(self):
        if self.p_skip == 0:
            self.value = self.measurement.get()
        skip = random() < self.p_skip
        self.value = None if skip else self.measurement.get()

    def get(self):
        return self.value

    def get_influx_meas(self):
        return self.influx_meas

    def get_tags(self):
        return self.tags


class DoomedDevice(Device):
    def __init__(self, name: str, base_device: Device, lifetime: int):
        self.name = name
        self.base_device = base_device
        self.time_remaining = lifetime

    def step(self):
        self.base_device.step()
        if self.time_remaining > 0:
            self.time_remaining -= 1

    def get(self) -> float:
        return None if self.time_remaining == 0 else self.base_device.get()

    def get_influx_meas(self):
        return self.base_device.get_influx_meas()

    def get_tags(self):
        return self.base_device.get_tags()


class StickyDevice(Device):
    def __init__(self, name: str, base_device: Device, lifetime: int):
        self.name = name
        self.base_device = base_device
        self.time_remaining = lifetime
        self.value = base_device.get()

    def step(self):
        self.base_device.step()
        if self.time_remaining > 0:
            self.time_remaining -= 1
            self.value = self.base_device.get()

    def get(self) -> float:
        return self.value

    def get_influx_meas(self):
        return self.base_device.get_influx_meas()

    def get_tags(self):
        return self.base_device.get_tags()


class Environment:
    def __init__(self, processes: Set[Process], devices: Set[Device]):
        self.processes = processes
        self.devices = devices

    def add_process(self, process: Process) -> Process:
        self.processes.add(process)
        return process

    def add_device(self, device: Device) -> Device:
        self.devices.add(device)
        return device

    def run_console(self, dt: int):
        while True:
            time = datetime.now()
            for process in self.processes:
                process.step()
            for device in self.devices:
                device.step()
                print(time, device.name, "value:", device.get(), "tags:", device.tags)
            sleep(dt)

    def run_influx(self, dt: int, config_file: str, bucket: str):
        self.client = InfluxDBClient.from_config_file(config_file)
        self.write_api = self.client.write_api()
        while True:
            for process in self.processes:
                process.step()
            for device in self.devices:
                device.step()
                self.write_device(device, bucket)
            print(datetime.now())
            sleep(dt)

    def write_device(self, device: Device, bucket: str):
        value = device.get()
        if value is None:
            return
        p = Point(device.get_influx_meas())
        p.field("value", float(value))
        for (key, val) in device.get_tags().items():
            p.tag(key, val)
        self.write_api.write(bucket, record=p)

    def generate_data(self, steps: int, dt: int, filename: str = "env_sim_gen.csv"):
        time = datetime.now()
        with open(filename, 'w') as file:
            # tags are hardcoded for now
            file.write("#datatype measurement,double,dateTime,tag,tag")
            file.write("m,value,time,room_id,sensor_id")
            for _ in range(steps):
                for p in self.processes:
                    p.step()
                for d in self.devices:
                    d.step()
                    file.write(
                        f"{d.get_influx_meas()},{d.get()},{time},{d.get_tags()['room_id']},{d.get_tags()['sensor_id']}"
                    )
                    d.get()
                time += timedelta(seconds=dt)


def identity(x):
    return x


def add_gauss_noise(sigma: float) -> Callable[[float], float]:
    return lambda x: x+randn()*sigma


def perfect_device(name: str, p: Process, influx_meas: str, tags: Dict[str, str]) -> Device:
    return BasicDevice(name, Measurement(p, identity), 0.0, influx_meas, tags)
