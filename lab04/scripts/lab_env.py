from env_sim import *
from numpy.random import randint
import argparse

"""
This is the simulated environment used for the Time Series lab of the Cyber Physical Systems course.
"""

env = Environment(set(), set())
parser = argparse.ArgumentParser(description="Simulator for the CPS InfluxDB lab.")

parser.add_argument('--co2', action='store_true')
parser.add_argument('--stuck_after', type=int)
parser.add_argument('--kill_after', type=int)
parser.add_argument('-dt', type=int, default=1)

args = parser.parse_args()

# A time step in the simulated environment equals 10 minutes in the simulated world's time.
# The simulation starts at 7:00 am


def add_outside_temperature(env: Environment):
    # Outside temperature
    out_temp_mean_process = env.add_process(IntegratedProcess(
        env.add_process(PwConstantProcess([8*6, 4*6, 12*6], [1.5/6, 0, -1.2/6], seasonal=True)), offset=8.0
    ))

    out_temp_noise_process = env.add_process(IntegratedProcess(
        env.add_process(GaussianNoiseProcess(0, 1/6))
    ))

    out_temp_process = env.add_process(SumProcess(
        [out_temp_mean_process, out_temp_noise_process]
    ))

    meas_out_temp = Measurement(out_temp_process, lambda x: x)
    env.add_device(BasicDevice("temp0", meas_out_temp, 0, "temperature", {"room_id": "0", "sensor_id": "0"}))


def create_room(env: Environment, room_id: str,
                arrival_rates: List[float], arrival_phase_lengths: List[int],
                departure_rates: List[float], departure_phase_lengths: List[int],
                co2_inc_per_people: float = 10.0/6.0, co2_mean_increase: float = -0.1):
    # Number of people in the room
    arrival_rate_process = env.add_process(PwConstantProcess(
        arrival_phase_lengths, arrival_rates, True)
    )

    departure_rate_process = env.add_process(PwConstantProcess(
        departure_phase_lengths, departure_rates, True)
    )

    num_people = env.add_process(BirthDeathProcess(arrival_rate_process, departure_rate_process))

    def num_people_noise(x: float) -> float:
        return max(0, x + randint(-1, 2))

    meas_num_people = Measurement(num_people, num_people_noise)
    env.add_device(BasicDevice("people", meas_num_people, 0, "n_people", {"room_id": room_id, "sensor_id": "0"}))

    # Inside temperature
    in_temp_mean_process = env.add_process(IntegratedProcess(
        env.add_process(PwConstantProcess([6*6, 6*6, 12*6], [0.2/6, 0, -0.1/6], seasonal=True)), offset=22.0
    ))

    in_temp_noise_process = env.add_process(IntegratedProcess(
        env.add_process(GaussianNoiseProcess(0, 0.5/6))
    ))

    in_temp_process = env.add_process(SumProcess(
        [in_temp_mean_process, in_temp_noise_process]
    ))
    meas_in_temp_1 = Measurement(in_temp_process, add_gauss_noise(0.5))
    meas_in_temp_2 = Measurement(in_temp_process, add_gauss_noise(0.5))
    temp_device_1 = BasicDevice("temp1", meas_in_temp_1, 0, "temperature", {"room_id": room_id, "sensor_id": "1"})
    if args.kill_after is not None:
        temp_device_1 = DoomedDevice("temp1", temp_device_1, args.kill_after)
    env.add_device(temp_device_1)

    temp_device_2 = BasicDevice("temp2", meas_in_temp_2, 0, "temperature", {"room_id": room_id, "sensor_id": "2"})
    if args.stuck_after is not None:
        temp_device_2 = StickyDevice("temp2", temp_device_2, args.stuck_after)
    env.add_device(temp_device_2)

    # CO2 level
    co2_emission_process = env.add_process(
        TransformedProcess(num_people, lambda x: co2_inc_per_people * x)
    )

    co2_ambient_process = env.add_process(IntegratedProcess(
        env.add_process(GaussianNoiseProcess(co2_mean_increase, 1.0)), 600
    ))

    co2_process = env.add_process(SumProcess([co2_ambient_process, co2_emission_process]))

    meas_co2 = Measurement(co2_process, add_gauss_noise(10))
    env.add_device(BasicDevice("co2", meas_co2, 0, "co2", {"room_id": room_id, "sensor_id": "3"}))


# add_outside_temperature(env)
n_rooms = 3

arrival_params = [
    ([6, 24, 24, 90], [2, 40, 30, 2]),           # Lecture Room A
    ([6, 24, 24, 90], [1, 20, 15, 1]),           # Lecture room B
    ([18, 12, 12, 24, 78], [2, 30, 80, 30, 2])   # Dining Room
]

departure_params = [
    ([12, 24, 24, 84], [2, 40, 90, 40]),        # Lecture Room A
    ([12, 24, 24, 84], [1, 20, 15, 1]),         # Lecture room B
    ([24, 12, 12, 24, 70], [2, 30, 80, 30, 2])  # Dining Room
]

for i in range(n_rooms):
    arrival_phase_lengths, arrival_rates = arrival_params[i]
    depart_phase_lengths, depart_rates = departure_params[i]

    create_room(
        env, str(i+1),
        arrival_rates, arrival_phase_lengths,
        depart_rates, depart_phase_lengths,
        co2_mean_increase=10.0 if args.co2 else -0.1
    )

env.run_influx(args.dt, "config.ini", "smart_uni")